#!/usr/bin/env python3
"""Decode MakerDAO Vat traces into an auditable ETH-A borrowing-event dataset.

The input is the public trace archive linked by Chaleenutthawut et al. (2024).
It contains successful calls to the MakerDAO Vat contract, ordered by block and
transaction trace.  No RPC endpoint or API key is required once the archive is
downloaded.

Only documented Vat call signatures are decoded.  A positive ``dart`` in
``frob`` is defined as a debt-draw event.  The generated DAI amount equals the
normalised debt change multiplied by the collateral type's accumulated rate.
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import math
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


FROB = "0x76088703"
MOVE = "0xbb35783b"
FOLD = "0xb65337df"
GRAB = "0x7bab3f40"
FLUX = "0x6111be2e"
FORK = "0x870c616d"

RAY = 10**27
WAD = 10**18
RAD = 10**45
UINT_256 = 2**256
INT_255 = 2**255


def _words(calldata: str) -> list[str]:
    payload = calldata[10:]
    if len(payload) % 64:
        raise ValueError("ABI payload length is not a multiple of 32 bytes")
    return [payload[i : i + 64] for i in range(0, len(payload), 64)]


def _signed(word: str) -> int:
    value = int(word, 16)
    return value - UINT_256 if value >= INT_255 else value


def _address(word: str) -> str:
    return "0x" + word[-40:].lower()


def _ilk(word: str) -> str:
    return bytes.fromhex(word).rstrip(b"\x00").decode("ascii", errors="replace")


def _iso_timestamp(value: str) -> str:
    return value.replace(" UTC", "+00:00")


@dataclass
class Spell:
    urn: str
    start_timestamp: str
    start_transaction_hash: str
    start_dai: float = 0.0
    total_drawn_dai: float = 0.0
    total_repaid_or_liquidated_dai: float = 0.0
    positive_draw_count: int = 0
    negative_repayment_count: int = 0
    liquidation_count: int = 0
    fork_count: int = 0
    started_by_frob: bool = False


@dataclass
class VaultState:
    art_wei: int = 0
    spell: Spell | None = None


def _event_time_days(start: str, end: str) -> float:
    start_dt = datetime.fromisoformat(start)
    end_dt = datetime.fromisoformat(end)
    return (end_dt - start_dt).total_seconds() / 86400.0


def build_lifecycles(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reconstruct debt spells; fork-affected spells are retained but flagged."""

    states: defaultdict[str, VaultState] = defaultdict(VaultState)
    completed: list[dict[str, Any]] = []
    anomalous_urns: set[str] = set()

    def apply_change(
        urn: str,
        delta_art: int,
        event_type: str,
        timestamp: str,
        tx_hash: str,
        dai_delta: float,
    ) -> None:
        state = states[urn]
        before = state.art_wei
        after = before + delta_art

        if before == 0 and after > 0:
            state.spell = Spell(
                urn=urn,
                start_timestamp=timestamp,
                start_transaction_hash=tx_hash,
                started_by_frob=event_type == "frob_draw",
            )

        spell = state.spell
        if spell is not None:
            if event_type == "frob_draw":
                spell.positive_draw_count += 1
                spell.total_drawn_dai += max(dai_delta, 0.0)
                if spell.positive_draw_count == 1:
                    spell.start_dai = max(dai_delta, 0.0)
            elif event_type == "frob_repay":
                spell.negative_repayment_count += 1
                spell.total_repaid_or_liquidated_dai += abs(dai_delta)
            elif event_type == "grab":
                spell.liquidation_count += 1
                spell.total_repaid_or_liquidated_dai += abs(dai_delta)
            elif event_type.startswith("fork"):
                spell.fork_count += 1

        if after < 0:
            # The published BigQuery extract deliberately omits top-level
            # calls (trace_address IS NULL).  A negative running balance is
            # therefore evidence that a preceding state change is absent.
            # Such an urn must never enter the observed-lifecycle sample.
            anomalous_urns.add(urn)
            state.art_wei = 0
            state.spell = None
            return

        state.art_wei = after

        if before > 0 and after == 0 and spell is not None:
            if spell.liquidation_count:
                status = "liquidated"
            elif spell.fork_count:
                status = "fork_affected"
            else:
                status = "repaid"
            completed.append(
                {
                    "urn": urn,
                    "start_timestamp": spell.start_timestamp,
                    "end_timestamp": timestamp,
                    "duration_days": _event_time_days(spell.start_timestamp, timestamp),
                    "status": status,
                    "start_transaction_hash": spell.start_transaction_hash,
                    "end_transaction_hash": tx_hash,
                    "start_dai": spell.start_dai,
                    "total_drawn_dai": spell.total_drawn_dai,
                    "total_repaid_or_liquidated_dai": spell.total_repaid_or_liquidated_dai,
                    "positive_draw_count": spell.positive_draw_count,
                    "negative_repayment_count": spell.negative_repayment_count,
                    "liquidation_count": spell.liquidation_count,
                    "fork_count": spell.fork_count,
                    "single_draw_clean": bool(
                        spell.started_by_frob
                        and spell.positive_draw_count == 1
                        and spell.negative_repayment_count == 1
                        and spell.liquidation_count == 0
                        and spell.fork_count == 0
                    ),
                }
            )
            state.spell = None

    for event in events:
        event_type = event["event_type"]
        if event_type == "fork":
            dart = int(event["dart_wei"])
            apply_change(
                event["src_urn"], -dart, "fork_out", event["timestamp"],
                event["transaction_hash"], -abs(float(event["dai_delta"])),
            )
            apply_change(
                event["dst_urn"], dart, "fork_in", event["timestamp"],
                event["transaction_hash"], abs(float(event["dai_delta"])),
            )
        else:
            if event_type == "frob":
                typed = "frob_draw" if int(event["dart_wei"]) > 0 else "frob_repay"
            else:
                typed = "grab"
            apply_change(
                event["urn"], int(event["dart_wei"]), typed,
                event["timestamp"], event["transaction_hash"],
                float(event["dai_delta"]),
            )

    final_timestamp = events[-1]["timestamp"] if events else ""
    for urn, state in states.items():
        spell = state.spell
        if spell is None or state.art_wei == 0:
            continue
        completed.append(
            {
                "urn": urn,
                "start_timestamp": spell.start_timestamp,
                "end_timestamp": final_timestamp,
                "duration_days": _event_time_days(spell.start_timestamp, final_timestamp),
                "status": "active_at_sample_end",
                "start_transaction_hash": spell.start_transaction_hash,
                "end_transaction_hash": "",
                "start_dai": spell.start_dai,
                "total_drawn_dai": spell.total_drawn_dai,
                "total_repaid_or_liquidated_dai": spell.total_repaid_or_liquidated_dai,
                "positive_draw_count": spell.positive_draw_count,
                "negative_repayment_count": spell.negative_repayment_count,
                "liquidation_count": spell.liquidation_count,
                "fork_count": spell.fork_count,
                "single_draw_clean": False,
            }
        )

    for row in completed:
        if row["urn"] in anomalous_urns:
            row["single_draw_clean"] = False
            row["reconstruction_anomaly"] = True
        else:
            row["reconstruction_anomaly"] = False

    return completed


def decode(raw_zip: Path, output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selector_counts: Counter[str] = Counter()
    rates: defaultdict[str, int] = defaultdict(lambda: RAY)
    events: list[dict[str, Any]] = []
    raw_rows = 0
    malformed_rows = 0

    with zipfile.ZipFile(raw_zip) as archive:
        csv_names = [name for name in archive.namelist() if name.lower().endswith(".csv") and not name.startswith("__MACOSX")]
        if len(csv_names) != 1:
            raise ValueError(f"Expected exactly one CSV in archive, found {csv_names}")
        with archive.open(csv_names[0]) as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8", newline="")
            for row in csv.DictReader(text):
                raw_rows += 1
                calldata = row.get("input", "")
                selector = calldata[:10]
                selector_counts[selector] += 1
                if selector not in {FOLD, FROB, GRAB, FORK}:
                    continue
                try:
                    words = _words(calldata)
                    timestamp = _iso_timestamp(row["block_timestamp"])
                    order = int(row["order"])
                    block_number = int(row["block_number"])
                    transaction_index = int(row["transaction_index"])
                    tx_hash = row["transaction_hash"].lower()

                    if selector == FOLD:
                        ilk = _ilk(words[0])
                        rates[ilk] += _signed(words[2])
                        continue

                    ilk = _ilk(words[0])
                    if ilk != "ETH-A":
                        continue
                    rate = rates[ilk]

                    if selector in {FROB, GRAB}:
                        urn = _address(words[1])
                        dink = _signed(words[4])
                        dart = _signed(words[5])
                        if dart == 0:
                            continue
                        events.append(
                            {
                                "order": order,
                                "timestamp": timestamp,
                                "block_number": block_number,
                                "transaction_index": transaction_index,
                                "transaction_hash": tx_hash,
                                "event_type": "frob" if selector == FROB else "grab",
                                "ilk": ilk,
                                "urn": urn,
                                "src_urn": "",
                                "dst_urn": "",
                                "dink_wei": dink,
                                "dart_wei": dart,
                                "rate_ray": rate,
                                "collateral_delta_eth": dink / WAD,
                                "normalised_debt_delta": dart / WAD,
                                "dai_delta": dart * rate / RAD,
                            }
                        )
                    elif selector == FORK:
                        src = _address(words[1])
                        dst = _address(words[2])
                        dink = _signed(words[3])
                        dart = _signed(words[4])
                        if dart == 0:
                            continue
                        events.append(
                            {
                                "order": order,
                                "timestamp": timestamp,
                                "block_number": block_number,
                                "transaction_index": transaction_index,
                                "transaction_hash": tx_hash,
                                "event_type": "fork",
                                "ilk": ilk,
                                "urn": "",
                                "src_urn": src,
                                "dst_urn": dst,
                                "dink_wei": dink,
                                "dart_wei": dart,
                                "rate_ray": rate,
                                "collateral_delta_eth": dink / WAD,
                                "normalised_debt_delta": dart / WAD,
                                "dai_delta": dart * rate / RAD,
                            }
                        )
                except (ValueError, IndexError, UnicodeDecodeError):
                    malformed_rows += 1

    events.sort(key=lambda item: item["order"])
    event_df = pd.DataFrame(events)
    event_df.to_csv(output_dir / "makerdao_eth_a_debt_events_all.csv", index=False)

    draw_df = event_df[(event_df["event_type"] == "frob") & (event_df["dart_wei"] > 0)].copy()
    draw_df.rename(columns={"dai_delta": "borrowed_dai"}, inplace=True)
    draw_df["event_id"] = [f"ETHA-{i:06d}" for i in range(1, len(draw_df) + 1)]
    draw_df["borrow_date"] = pd.to_datetime(draw_df["timestamp"], utc=True).dt.strftime("%Y-%m-%d")
    draw_df["borrow_year"] = pd.to_datetime(draw_df["timestamp"], utc=True).dt.year
    draw_df.to_csv(output_dir / "makerdao_eth_a_draw_events.csv", index=False)

    lifecycles = build_lifecycles(events)
    lifecycle_df = pd.DataFrame(lifecycles).sort_values(["start_timestamp", "urn"])
    lifecycle_df.to_csv(output_dir / "makerdao_eth_a_lifecycles.csv", index=False)

    analysis_window = draw_df[
        (pd.to_datetime(draw_df["timestamp"], utc=True) >= pd.Timestamp("2020-01-01", tz="UTC"))
        & (pd.to_datetime(draw_df["timestamp"], utc=True) < pd.Timestamp("2023-08-01", tz="UTC"))
        & (draw_df["borrowed_dai"] >= 1.0)
    ].copy()
    analysis_window.to_csv(output_dir / "makerdao_eth_a_draw_events_analysis.csv", index=False)

    construction = pd.DataFrame(
        [
            ("Raw successful Vat call traces", raw_rows, "Public BigQuery extraction archive"),
            ("Decoded ETH-A debt-changing events", len(event_df), "frob, grab, and fork with non-zero dart"),
            ("Positive ETH-A frob debt draws", len(draw_df), "Operational definition of borrowing event"),
            ("Excluded before 2020-01-01", int((pd.to_datetime(draw_df["timestamp"], utc=True) < pd.Timestamp("2020-01-01", tz="UTC")).sum()), "Prespecified analysis window"),
            ("Excluded draw amounts below 1 DAI after date filter", int(((pd.to_datetime(draw_df["timestamp"], utc=True) >= pd.Timestamp("2020-01-01", tz="UTC")) & (draw_df["borrowed_dai"] < 1.0)).sum()), "Economically de minimis debt adjustments; avoids gas-cost singularities"),
            ("Final draw-event analysis sample", len(analysis_window), "All eligible ETH-A draws, not a 1,000-event sample"),
            ("Unique ETH-A urn addresses in final sample", analysis_window["urn"].nunique(), "Vault-level identifiers; not verified real-world borrowers"),
            ("Clean single-draw repaid lifecycles", int(lifecycle_df["single_draw_clean"].sum()), "Used only for observed-duration robustness"),
        ],
        columns=["stage", "count", "rule"],
    )
    construction.to_csv(output_dir / "sample_construction.csv", index=False)

    metadata = {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "raw_archive": str(raw_zip),
        "raw_rows": raw_rows,
        "malformed_decoded_rows": malformed_rows,
        "selector_counts": dict(selector_counts),
        "eth_a_debt_event_rows": len(event_df),
        "all_positive_eth_a_draws": len(draw_df),
        "analysis_draws": len(analysis_window),
        "unique_analysis_urns": int(analysis_window["urn"].nunique()),
        "total_analysis_borrowed_dai": float(analysis_window["borrowed_dai"].sum()),
        "clean_single_draw_lifecycles": int(lifecycle_df["single_draw_clean"].sum()),
        "definition": "A borrowing event is a successful ETH-A Vat.frob call with positive dart.",
    }
    (output_dir / "decode_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("raw_zip", type=Path)
    parser.add_argument("output_dir", type=Path)
    args = parser.parse_args()
    metadata = decode(args.raw_zip, args.output_dir)
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
