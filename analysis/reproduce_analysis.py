#!/usr/bin/env python3
"""Reproduce the first paper's revised results from archived draws and official FX.

The empirical tables deliberately exclude probability-weighted liquidation returns:
a monthly FX series and terminal price shocks do not identify liquidation paths.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from borrower_cashflows import CostAssumptions, accrued_debt_usd, survivor_cashflow

HORIZONS = (3, 6, 12, 24)
RATES = (0.05, 0.10, 0.20, 0.40, 0.80, 1.20)
MINIMUM_SIZES = (1, 100, 1000, 5000, 10000)
CURRENCIES = ("ARS", "TRY")
FX_COLUMNS = {"ARS": "ARGCCUSMA02STM", "TRY": "CCUSMA02TRM618N"}
BASE = CostAssumptions()
COLORS = {"ARS": "#7a3e9d", "TRY": "#147d8d"}


def load_fx(paths: dict[str, Path]) -> pd.DataFrame:
    parts = []
    for currency, path in paths.items():
        frame = pd.read_csv(path)
        frame = frame.rename(columns={"observation_date": "month", FX_COLUMNS[currency]: "local_per_usd"})
        frame["month"] = pd.to_datetime(frame["month"]).dt.to_period("M")
        frame["local_per_usd"] = pd.to_numeric(frame["local_per_usd"], errors="coerce")
        frame = frame.dropna(subset=["local_per_usd"])
        frame["currency"] = currency
        parts.append(frame[["currency", "month", "local_per_usd"]])
    return pd.concat(parts, ignore_index=True)


def fx_lookup(fx: pd.DataFrame, currency: str) -> dict[pd.Period, float]:
    part = fx[fx.currency == currency]
    return dict(zip(part.month, part.local_per_usd, strict=True))


def fixed_frame(draws: pd.DataFrame, lookup: dict[pd.Period, float], months: int) -> pd.DataFrame:
    frame = draws[["event_id", "order", "timestamp", "urn", "borrowed_dai"]].copy()
    frame["start_month"] = pd.to_datetime(frame.timestamp, utc=True).dt.tz_convert(None).dt.to_period("M")
    frame["end_month"] = frame.start_month + months
    frame["fx_start"] = frame.start_month.map(lookup)
    frame["fx_close"] = frame.end_month.map(lookup)
    return frame.dropna(subset=["fx_start", "fx_close"]).reset_index(drop=True)


def with_cashflows(frame: pd.DataFrame, years: object, rate: float = 0.20,
                   costs: CostAssumptions = BASE) -> pd.DataFrame:
    out = frame.copy()
    p = out.borrowed_dai.to_numpy()
    e0 = out.fx_start.to_numpy()
    et = out.fx_close.to_numpy()
    out["gross_usd"] = p * (1 - e0 / et)
    amounts = survivor_cashflow(p, e0, et, years, rate, costs)
    out["debt_usd"] = amounts["debt_service_usd"]
    out["net_usd"] = amounts["net_benefit_usd"]
    out["gross_pct"] = 100 * out.gross_usd / p
    out["net_pct"] = 100 * out.net_usd / p
    return out


def metric(frame: pd.DataFrame, label: str, *, currency: str, horizon: str) -> dict:
    p = frame.borrowed_dai
    return {
        "currency": currency, "sample": label, "horizon": horizon,
        "n": len(frame), "total_principal_usd": float(p.sum()),
        "median_gross_pct": float(frame.gross_pct.median()),
        "median_net_pct": float(frame.net_pct.median()),
        "mean_net_pct": float(frame.net_pct.mean()),
        "positive_net_pct": float(100 * (frame.net_usd > 0).mean()),
        "weighted_net_pct": float(100 * frame.net_usd.sum() / p.sum()),
    }


def prepare_lifecycles(lifecycles: pd.DataFrame, lookup: dict[pd.Period, float]) -> pd.DataFrame:
    clean = lifecycles[
        lifecycles.single_draw_clean.astype(str).str.lower().eq("true")
        & lifecycles.status.eq("repaid")
        & (lifecycles.start_dai >= 1)
        & (lifecycles.duration_days > 0)
    ].copy()
    clean = clean.rename(columns={"start_dai": "borrowed_dai", "start_timestamp": "timestamp"})
    clean["start_dt"] = pd.to_datetime(clean.timestamp, utc=True)
    clean["end_dt"] = pd.to_datetime(clean.end_timestamp, utc=True)
    clean = clean[clean.start_dt >= pd.Timestamp("2020-01-01", tz="UTC")].copy()
    clean["start_month"] = clean.start_dt.dt.tz_convert(None).dt.to_period("M")
    clean["end_month"] = clean.end_dt.dt.tz_convert(None).dt.to_period("M")
    clean["fx_start"] = clean.start_month.map(lookup)
    clean["fx_close"] = clean.end_month.map(lookup)
    clean = clean.dropna(subset=["fx_start", "fx_close"]).reset_index(drop=True)
    return with_cashflows(clean, clean.duration_days.to_numpy() / 365.25)


def urn_counts(draws: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    counts = draws.groupby("urn", as_index=False, sort=False).agg(
        draw_count=("event_id", "size"), total_drawn_dai=("borrowed_dai", "sum"))
    bands = pd.cut(counts.draw_count, bins=[0, 1, 2, 5, 10, np.inf],
                   labels=["1", "2", "3-5", "6-10", "11+"])
    dist = counts.assign(band=bands).groupby("band", observed=True).agg(
        urns=("urn", "size"), draw_events=("draw_count", "sum")).reset_index()
    dist["share_urns_pct"] = 100 * dist.urns / len(counts)
    dist["share_draws_pct"] = 100 * dist.draw_events / len(draws)
    return counts, dist


def dependence(frame: pd.DataFrame, currency: str) -> tuple[list[dict], pd.DataFrame]:
    first = frame.sort_values(["timestamp", "order", "event_id"]).drop_duplicates("urn", keep="first")
    urn = frame.groupby("urn", as_index=False).agg(
        draws=("event_id", "size"), principal_usd=("borrowed_dai", "sum"),
        net_usd=("net_usd", "sum"), gross_usd=("gross_usd", "sum"))
    urn["net_pct"] = 100 * urn.net_usd / urn.principal_usd
    rows = []
    for name, selected in [("All draw events", frame), ("First draw per urn", first)]:
        rows.append({
            "currency": currency, "unit": name, "n": len(selected),
            "median_net_pct": selected.net_pct.median(),
            "equal_unit_mean_pct": selected.net_pct.mean(),
            "weighted_net_pct": 100 * selected.net_usd.sum() / selected.borrowed_dai.sum(),
            "positive_units_pct": 100 * (selected.net_usd > 0).mean(),
        })
    rows.append({
        "currency": currency, "unit": "Urn aggregate", "n": len(urn),
        "median_net_pct": urn.net_pct.median(),
        "equal_unit_mean_pct": urn.net_pct.mean(),
        "weighted_net_pct": 100 * urn.net_usd.sum() / urn.principal_usd.sum(),
        "positive_units_pct": 100 * (urn.net_usd > 0).mean(),
    })
    urn["currency"] = currency
    return rows, urn


def concentration(frame: pd.DataFrame, currency: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    ranked = frame.sort_values(["borrowed_dai", "event_id"], ascending=[False, True])
    denom_benefit = frame.net_usd.sum()
    rows = []
    for fraction in (0.01, 0.05, 0.10):
        top = ranked.head(math.ceil(fraction * len(ranked)))
        rows.append({
            "currency": currency, "top_pct_by_draw_size": 100 * fraction, "events": len(top),
            "share_principal_pct": 100 * top.borrowed_dai.sum() / frame.borrowed_dai.sum(),
            "share_signed_net_benefit_pct": 100 * top.net_usd.sum() / denom_benefit,
            "top_weighted_net_pct": 100 * top.net_usd.sum() / top.borrowed_dai.sum(),
        })
    monthly = frame.groupby("start_month", sort=True).agg(
        events=("event_id", "size"), principal_usd=("borrowed_dai", "sum"),
        net_usd=("net_usd", "sum")).reset_index()
    monthly["currency"] = currency
    monthly["start_month"] = monthly.start_month.astype(str)
    monthly["share_principal_pct"] = 100 * monthly.principal_usd / frame.borrowed_dai.sum()
    monthly["share_signed_net_benefit_pct"] = 100 * monthly.net_usd / denom_benefit
    monthly["weighted_net_pct"] = 100 * monthly.net_usd / monthly.principal_usd
    return pd.DataFrame(rows), monthly


def thresholds(frame: pd.DataFrame, currency: str, sample: str) -> list[dict]:
    rows = []
    for floor in MINIMUM_SIZES:
        part = frame[frame.borrowed_dai >= floor]
        rows.append({
            "currency": currency, "sample": sample, "minimum_usd": floor, "n": len(part),
            "retained_events_pct": 100 * len(part) / len(frame),
            "median_net_pct": part.net_pct.median(),
            "mean_net_pct": part.net_pct.mean(),
            "positive_net_pct": 100 * (part.net_usd > 0).mean(),
            "weighted_net_pct": 100 * part.net_usd.sum() / part.borrowed_dai.sum(),
        })
    return rows


def duration_bins(frame: pd.DataFrame, currency: str) -> pd.DataFrame:
    bands = pd.cut(frame.duration_days, bins=[0, 1, 7, 30, 90, np.inf],
                   labels=["(0,1]", "(1,7]", "(7,30]", "(30,90]", ">90"])
    result = frame.assign(duration_band=bands).groupby("duration_band", observed=True).agg(
        n=("urn", "size"), median_days=("duration_days", "median"),
        median_net_pct=("net_pct", "median"), positive_net_pct=("net_usd", lambda x: 100 * (x > 0).mean()),
        principal_usd=("borrowed_dai", "sum"), total_net_usd=("net_usd", "sum"),
    ).reset_index()
    result["currency"] = currency
    result["weighted_net_pct"] = 100 * result.total_net_usd / result.principal_usd
    return result


def terminal_screen(frame: pd.DataFrame, currency: str) -> list[dict]:
    p = frame.borrowed_dai.to_numpy()
    debt = accrued_debt_usd(p, frame.fx_start.to_numpy(), frame.fx_close.to_numpy(), 1, 0.20)
    rows = []
    for cr0 in (1.50, 1.75, 2.00):
        for shock in (0, 0.10, 0.25, 0.40, 0.60):
            ratio = cr0 * p * (1 - shock) / debt
            rows.append({
                "currency": currency, "initial_ratio_pct": 100 * cr0,
                "terminal_price_decline_pct": 100 * shock,
                "terminal_below_150pct_share": 100 * (ratio < 1.50).mean(),
                "median_terminal_ratio_pct": 100 * np.median(ratio),
                "n": len(frame),
            })
    return rows


def _escape(value: object) -> str:
    return str(value).replace("%", r"\%").replace("_", r"\_")


def tex_tabular(path: Path, headings: list[str], rows: list[list[object]], align: str) -> None:
    lines = [r"\begin{tabular}{" + align + "}", r"\toprule",
             " & ".join(headings) + r" \\", r"\midrule"]
    for row in rows:
        lines.append(" & ".join(_escape(x) for x in row) + r" \\")
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def save_tables(output: Path, summary: pd.DataFrame, dep: pd.DataFrame, size: pd.DataFrame,
                concentration: pd.DataFrame, duration: pd.DataFrame, terminal: pd.DataFrame) -> None:
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in CURRENCIES:
        d = summary[(summary.currency == c) & (summary["sample"] == "Clean observed duration")].iloc[0]
        m12 = summary[(summary.currency == c) & (summary.horizon == "12m")].iloc[0]
        m24 = summary[(summary.currency == c) & (summary.horizon == "24m")].iloc[0]
        rows.append([c, f"{int(d.n):,}", f"{d.median_net_pct:.2f}", f"{m12.median_gross_pct:.2f}",
                     f"{m12.median_net_pct:.2f}", f"{m24.median_net_pct:.2f}"])
    tex_tabular(output / "main.tex",
                ["FX", "Clean spells", "Observed net", "12m gross", "12m net", "24m net"], rows, "lrrrrr")
    tex_tabular(output / "dependence.tex",
                ["FX", "Unit", "$N$", "Median net", "Mean net", "Weighted net"],
                [[r.currency, r.unit, f"{int(r.n):,}", f"{r.median_net_pct:.2f}",
                  f"{r.equal_unit_mean_pct:.2f}", f"{r.weighted_net_pct:.2f}"]
                 for r in dep.itertuples()], "llrrrr")
    tex_tabular(output / "size.tex",
                ["FX", "Sample", "Min. USD", "$N$", "Median net", "Weighted net"],
                [[r.currency, "Observed" if r.sample.startswith("Clean") else "12m",
                  f"{int(r.minimum_usd):,}", f"{int(r.n):,}", f"{r.median_net_pct:.2f}",
                  f"{r.weighted_net_pct:.2f}"] for r in size.itertuples()], "llrrrr")
    tex_tabular(output / "concentration.tex",
                ["FX", "Largest draws", "Share of principal", "Share of signed net"],
                [[r.currency, f"{r.top_pct_by_draw_size:.0f}%", f"{r.share_principal_pct:.2f}",
                  f"{r.share_signed_net_benefit_pct:.2f}"] for r in concentration.itertuples()], "llrr")
    tex_tabular(output / "duration.tex",
                ["FX", "Duration (days)", "$N$", "Median net", "Positive"],
                [[r.currency, "$>90$" if r.duration_band == ">90" else r.duration_band,
                  f"{int(r.n):,}", f"{r.median_net_pct:.2f}",
                  f"{r.positive_net_pct:.2f}"] for r in duration.itertuples()], "llrrr")
    shown = terminal[(terminal.initial_ratio_pct == 175) &
                     terminal.terminal_price_decline_pct.isin([10, 25, 40, 60])]
    tex_tabular(output / "terminal.tex",
                ["FX", "Price decline", "Terminal breach share"],
                [[r.currency, f"{r.terminal_price_decline_pct:.0f}%",
                  f"{r.terminal_below_150pct_share:.2f}"] for r in shown.itertuples()], "lrr")


def save_figures(fx: pd.DataFrame, durations: dict[str, pd.DataFrame], monthly: pd.DataFrame,
                 terminal: pd.DataFrame, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 12, "axes.titlesize": 13, "figure.dpi": 125,
                         "savefig.dpi": 220, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(9, 4.5))
    for c in CURRENCIES:
        part = fx[(fx.currency == c) & (fx.month >= pd.Period("2019-01")) &
                  (fx.month <= pd.Period("2025-07"))]
        ax.plot(part.month.dt.to_timestamp(), part.local_per_usd, lw=2, color=COLORS[c], label=c)
    ax.set_yscale("log")
    ax.set_xlabel("Month")
    ax.set_ylabel("Official local-currency units per USD (log scale)")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out / "fx_paths.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    for c in CURRENCIES:
        vals = durations[c].duration_days.to_numpy()
        bins = np.logspace(-3, 3.5, 70)
        ax.hist(vals, bins=bins, histtype="step", linewidth=2, label=c, color=COLORS[c])
    ax.set_xscale("log")
    ax.set_xlabel("Observed clean-spell duration (days; logarithmic)")
    ax.set_ylabel("Number of reconstructed spells")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out / "observed_duration.png")
    plt.close(fig)

    pivot = monthly.pivot(index="start_month", columns="currency", values="share_signed_net_benefit_pct")
    fig, ax = plt.subplots(figsize=(10, 4.8))
    x = np.arange(len(pivot))
    ax.bar(x-0.18, pivot.ARS, width=0.36, color=COLORS["ARS"], label="ARS")
    ax.bar(x+0.18, pivot.TRY, width=0.36, color=COLORS["TRY"], label="TRY")
    ax.axhline(0, color="black", lw=0.8)
    ax.set_xticks(x[::3], pivot.index[::3], rotation=45, ha="right")
    ax.set_ylabel("Share of signed 12-month net benefit (%)")
    ax.set_xlabel("Origination month")
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(out / "origination_month.png")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.4), sharey=True)
    for ax, c in zip(axes, CURRENCIES, strict=True):
        subset = terminal[terminal.currency == c]
        for cr0 in (150, 175, 200):
            line = subset[subset.initial_ratio_pct == cr0]
            ax.plot(line.terminal_price_decline_pct, line.terminal_below_150pct_share,
                    "-o", lw=2, label=f"Start {cr0}%")
        ax.set_title(c)
        ax.set_xlabel("Assumed terminal collateral decline (%)")
        ax.set_ylim(0, 105)
    axes[0].set_ylabel("Below 150% at terminal month (%)")
    axes[1].legend(frameon=False, fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "terminal_screen.png")
    plt.close(fig)


def run(args: argparse.Namespace) -> dict:
    args.output_dir.mkdir(parents=True, exist_ok=True)
    draws = pd.read_csv(args.draws, low_memory=False)
    lifecycles = pd.read_csv(args.lifecycles, low_memory=False)
    fx = load_fx({"ARS": args.ars_fx, "TRY": args.try_fx})
    fx.assign(month=fx.month.astype(str)).to_csv(args.output_dir / "fx_monthly_oecd_fred.csv", index=False)
    count_frame, count_dist = urn_counts(draws)
    count_frame.to_csv(args.output_dir / "urn_draw_counts.csv", index=False)
    count_dist.to_csv(args.output_dir / "urn_draw_distribution.csv", index=False)

    summaries, rate_rows, dep_rows, urn_rows, top_rows, months, size_rows = [], [], [], [], [], [], []
    duration_parts, terminal_rows, duration_frames, fixed12 = [], [], {}, {}
    for currency in CURRENCIES:
        lookup = fx_lookup(fx, currency)
        for h in HORIZONS:
            frame = fixed_frame(draws, lookup, h)
            adjusted = with_cashflows(frame, h/12)
            summaries.append(metric(adjusted, "Fixed holding-period scenario", currency=currency, horizon=f"{h}m"))
            if h == 12:
                fixed12[currency] = adjusted
            for rate in RATES:
                cash = adjusted if rate == 0.20 else with_cashflows(frame, h/12, rate)
                row = metric(cash, "Fixed holding-period scenario", currency=currency, horizon=f"{h}m")
                row["annual_effective_rate_pct"] = 100 * rate
                rate_rows.append(row)
        twelve = fixed12[currency]
        dep, urn = dependence(twelve, currency)
        dep_rows.extend(dep)
        urn_rows.append(urn)
        concentration_rows, month_rows = concentration(twelve, currency)
        top_rows.append(concentration_rows)
        months.append(month_rows)
        size_rows.extend(thresholds(twelve, currency, "Fixed 12m"))
        terminal_rows.extend(terminal_screen(twelve, currency))
        observed = prepare_lifecycles(lifecycles, lookup)
        duration_frames[currency] = observed
        summaries.append(metric(observed, "Clean observed duration", currency=currency, horizon="observed"))
        size_rows.extend(thresholds(observed, currency, "Clean observed duration"))
        duration_parts.append(duration_bins(observed, currency))
    summary = pd.DataFrame(summaries)
    rate = pd.DataFrame(rate_rows)
    dep = pd.DataFrame(dep_rows)
    urn = pd.concat(urn_rows, ignore_index=True)
    top = pd.concat(top_rows, ignore_index=True)
    monthly = pd.concat(months, ignore_index=True)
    size = pd.DataFrame(size_rows)
    duration = pd.concat(duration_parts, ignore_index=True)
    terminal = pd.DataFrame(terminal_rows)
    for name, data in {
        "main_summary.csv": summary,
        "rate_sensitivity.csv": rate,
        "urn_robustness.csv": dep,
        "urn_aggregate_12m.csv": urn,
        "large_event_concentration.csv": top,
        "origination_month_concentration.csv": monthly,
        "position_size_sensitivity.csv": size,
        "observed_duration_bands.csv": duration,
        "terminal_collateral_ratio_screen.csv": terminal,
    }.items():
        data.to_csv(args.output_dir / name, index=False)
    save_tables(args.latex_table_dir, summary, dep, size, top, duration, terminal)
    save_figures(fx, duration_frames, monthly, terminal, args.figure_dir)
    metadata = {
        "draw_events": len(draws), "unique_urns": int(draws.urn.nunique()),
        "total_drawn_dai": float(draws.borrowed_dai.sum()),
        "observed_clean_spells_per_currency": {c: len(duration_frames[c]) for c in CURRENCIES},
        "median_observed_days_per_currency": {c: float(duration_frames[c].duration_days.median()) for c in CURRENCIES},
        "conditional_liquidation_cashflows": "Implemented and tested separately; not estimated from terminal-only shocks",
        "risk_adjusted_median_removed": True,
        "ars_interpretation": "Official monthly FX counterfactual only; no executable ARS series",
        "fee_timing": "Paid in USD at origination; not financed",
        "gas_scope": "Half at opening and half at voluntary close; only opening charged to borrower upon liquidation",
    }
    (args.output_dir / "validation_summary.json").write_text(json.dumps(metadata, indent=2)+"\n")
    return metadata


def main() -> None:
    root = Path(__file__).resolve().parent.parent
    p = argparse.ArgumentParser()
    p.add_argument("--draws", type=Path, default=root/"data/processed/makerdao_eth_a_draw_events_analysis.csv")
    p.add_argument("--lifecycles", type=Path, default=root/"data/processed/makerdao_eth_a_lifecycles.csv")
    p.add_argument("--ars-fx", type=Path, default=root/"data/raw_fx/ars_usd_fred.csv")
    p.add_argument("--try-fx", type=Path, default=root/"data/raw_fx/try_usd_fred.csv")
    p.add_argument("--output-dir", type=Path, default=root/"results")
    p.add_argument("--figure-dir", type=Path, default=root/"figures")
    p.add_argument("--latex-table-dir", type=Path, default=root/"tables")
    args = p.parse_args()
    print(json.dumps(run(args), indent=2))


if __name__ == "__main__":
    main()
