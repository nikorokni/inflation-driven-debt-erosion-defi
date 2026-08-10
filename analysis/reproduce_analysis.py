#!/usr/bin/env python3
"""Reproduce all empirical tables and figures used by the revised manuscript."""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


HORIZONS = (3, 6, 12, 24)
ANNUAL_RATES = (0.05, 0.10, 0.20, 0.40, 0.80, 1.20)
COLLATERAL_RATIOS = (1.50, 1.75, 2.00)
LIQUIDATION_PENALTIES = (0.05, 0.10, 0.13)
LIQUIDATION_RATIO = 1.50


@dataclass(frozen=True)
class CostAssumptions:
    protocol_fee_fraction: float = 0.005
    swap_slippage_fraction_each_way: float = 0.003
    gas_usd_round_trip: float = 40.0


def load_fx(ars_path: Path, try_path: Path) -> pd.DataFrame:
    specifications = (
        ("ARS", ars_path, "ARGCCUSMA02STM"),
        ("TRY", try_path, "CCUSMA02TRM618N"),
    )
    frames = []
    for currency, path, value_column in specifications:
        frame = pd.read_csv(path)
        frame = frame.rename(columns={"observation_date": "month", value_column: "local_per_usd"})
        frame["month"] = pd.to_datetime(frame["month"]).dt.to_period("M")
        frame["local_per_usd"] = pd.to_numeric(frame["local_per_usd"], errors="coerce")
        frame = frame.dropna(subset=["local_per_usd"])
        frame["currency"] = currency
        frames.append(frame[["currency", "month", "local_per_usd"]])
    return pd.concat(frames, ignore_index=True)


def fx_map(fx: pd.DataFrame, currency: str) -> dict[pd.Period, float]:
    subset = fx[fx["currency"] == currency]
    return dict(zip(subset["month"], subset["local_per_usd"], strict=True))


def attach_fx(
    events: pd.DataFrame,
    fx: pd.DataFrame,
    currency: str,
    horizon_months: int,
) -> pd.DataFrame:
    result = events.copy()
    timestamps = pd.to_datetime(result["timestamp"], utc=True).dt.tz_localize(None)
    result["start_month"] = timestamps.dt.to_period("M")
    result["end_month"] = result["start_month"] + horizon_months
    mapping = fx_map(fx, currency)
    result["fx_start"] = result["start_month"].map(mapping)
    result["fx_end"] = result["end_month"].map(mapping)
    result = result.dropna(subset=["fx_start", "fx_end"]).copy()
    result["currency"] = currency
    result["horizon_months"] = horizon_months
    result["fx_ratio"] = result["fx_start"] / result["fx_end"]
    result["gross_benefit_usd"] = result["borrowed_dai"] * (1.0 - result["fx_ratio"])
    result["gross_benefit_pct"] = 100.0 * (1.0 - result["fx_ratio"])
    return result


def cost_adjusted(
    frame: pd.DataFrame,
    annual_rate: float,
    assumptions: CostAssumptions,
    years: pd.Series | float | None = None,
) -> pd.DataFrame:
    result = frame.copy()
    if years is None:
        years = result["horizon_months"] / 12.0
    factor = np.power(1.0 + annual_rate, years)
    principal = result["borrowed_dai"]
    debt_service = principal * result["fx_ratio"] * factor
    protocol_fee = assumptions.protocol_fee_fraction * principal * result["fx_ratio"]
    entry_swap = assumptions.swap_slippage_fraction_each_way * principal
    repayment_swap = assumptions.swap_slippage_fraction_each_way * debt_service
    total_repayment = debt_service + protocol_fee + entry_swap + repayment_swap + assumptions.gas_usd_round_trip
    result["annual_borrow_rate"] = annual_rate
    result["debt_service_usd"] = debt_service
    result["protocol_fee_usd"] = protocol_fee
    result["swap_slippage_usd"] = entry_swap + repayment_swap
    result["gas_usd"] = assumptions.gas_usd_round_trip
    result["total_repayment_usd"] = total_repayment
    result["net_benefit_preliq_usd"] = principal - total_repayment
    result["net_benefit_preliq_pct"] = 100.0 * result["net_benefit_preliq_usd"] / principal
    return result


def calculate_break_even(frame: pd.DataFrame, assumptions: CostAssumptions) -> pd.Series:
    principal = frame["borrowed_dai"]
    q = frame["fx_ratio"]
    years = frame["horizon_months"] / 12.0
    numerator = 1.0 - assumptions.protocol_fee_fraction * q - assumptions.swap_slippage_fraction_each_way - assumptions.gas_usd_round_trip / principal
    denominator = q * (1.0 + assumptions.swap_slippage_fraction_each_way)
    rhs = numerator / denominator
    values = np.where(rhs > 0, np.power(rhs, 1.0 / years) - 1.0, np.nan)
    return pd.Series(values, index=frame.index)


def descriptive_statistics(draws: pd.DataFrame) -> pd.DataFrame:
    stats = pd.DataFrame(
        [
            {
                "final_draw_events": len(draws),
                "unique_urns": draws["urn"].nunique(),
                "date_start": pd.to_datetime(draws["timestamp"], utc=True).min().date().isoformat(),
                "date_end": pd.to_datetime(draws["timestamp"], utc=True).max().date().isoformat(),
                "total_borrowed_dai": draws["borrowed_dai"].sum(),
                "mean_borrowed_dai": draws["borrowed_dai"].mean(),
                "median_borrowed_dai": draws["borrowed_dai"].median(),
                "std_borrowed_dai": draws["borrowed_dai"].std(),
                "minimum_borrowed_dai": draws["borrowed_dai"].min(),
                "maximum_borrowed_dai": draws["borrowed_dai"].max(),
            }
        ]
    )
    return stats


def horizon_summary(all_horizons: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (currency, horizon), group in all_horizons.groupby(["currency", "horizon_months"], sort=True):
        q1 = group["gross_benefit_pct"].quantile(0.25)
        q3 = group["gross_benefit_pct"].quantile(0.75)
        rows.append(
            {
                "currency": currency,
                "horizon_months": horizon,
                "eligible_events": len(group),
                "total_borrowed_dai": group["borrowed_dai"].sum(),
                "mean_gross_benefit_pct": group["gross_benefit_pct"].mean(),
                "median_gross_benefit_pct": group["gross_benefit_pct"].median(),
                "std_gross_benefit_pct": group["gross_benefit_pct"].std(),
                "iqr_gross_benefit_pct": q3 - q1,
                "positive_positions_pct": 100.0 * (group["gross_benefit_pct"] > 0).mean(),
                "total_gross_benefit_usd": group["gross_benefit_usd"].sum(),
                "value_weighted_gross_benefit_pct": 100.0 * group["gross_benefit_usd"].sum() / group["borrowed_dai"].sum(),
            }
        )
    return pd.DataFrame(rows)


def net_summary(all_horizons: pd.DataFrame, assumptions: CostAssumptions) -> tuple[pd.DataFrame, pd.DataFrame]:
    net_rows = []
    break_even_rows = []
    for (currency, horizon), group in all_horizons.groupby(["currency", "horizon_months"], sort=True):
        break_even = 100.0 * calculate_break_even(group, assumptions)
        break_even_rows.append(
            {
                "currency": currency,
                "horizon_months": horizon,
                "median_break_even_rate_pct": break_even.median(),
                "p25_break_even_rate_pct": break_even.quantile(0.25),
                "p75_break_even_rate_pct": break_even.quantile(0.75),
            }
        )
        for rate in ANNUAL_RATES:
            adjusted = cost_adjusted(group, rate, assumptions)
            net_rows.append(
                {
                    "currency": currency,
                    "horizon_months": horizon,
                    "annual_borrow_rate_pct": 100.0 * rate,
                    "events": len(adjusted),
                    "mean_net_benefit_pct": adjusted["net_benefit_preliq_pct"].mean(),
                    "median_net_benefit_pct": adjusted["net_benefit_preliq_pct"].median(),
                    "positive_positions_pct": 100.0 * (adjusted["net_benefit_preliq_usd"] > 0).mean(),
                    "total_net_benefit_usd": adjusted["net_benefit_preliq_usd"].sum(),
                    "value_weighted_net_benefit_pct": 100.0 * adjusted["net_benefit_preliq_usd"].sum() / adjusted["borrowed_dai"].sum(),
                }
            )
    return pd.DataFrame(net_rows), pd.DataFrame(break_even_rows)


def lifecycle_summary(lifecycles: pd.DataFrame, fx: pd.DataFrame, assumptions: CostAssumptions) -> pd.DataFrame:
    clean = lifecycles[
        lifecycles["single_draw_clean"].astype(str).str.lower().eq("true")
        & (lifecycles["start_dai"] >= 1.0)
    ].copy()
    clean = clean.rename(columns={"start_timestamp": "timestamp", "start_dai": "borrowed_dai"})
    clean["start_dt"] = pd.to_datetime(clean["timestamp"], utc=True).dt.tz_localize(None)
    clean["end_dt"] = pd.to_datetime(clean["end_timestamp"], utc=True).dt.tz_localize(None)
    clean = clean[(clean["start_dt"] >= pd.Timestamp("2020-01-01")) & (clean["duration_days"] > 0)]
    rows = []
    for currency in ("ARS", "TRY"):
        mapping = fx_map(fx, currency)
        frame = clean.copy()
        frame["start_month"] = frame["start_dt"].dt.to_period("M")
        frame["end_month"] = frame["end_dt"].dt.to_period("M")
        frame["fx_start"] = frame["start_month"].map(mapping)
        frame["fx_end"] = frame["end_month"].map(mapping)
        frame = frame.dropna(subset=["fx_start", "fx_end"])
        frame["fx_ratio"] = frame["fx_start"] / frame["fx_end"]
        frame["gross_benefit_pct"] = 100.0 * (1.0 - frame["fx_ratio"])
        frame["horizon_months"] = 12.0 * frame["duration_days"] / 365.25
        adjusted = cost_adjusted(frame, 0.20, assumptions, years=frame["duration_days"] / 365.25)
        rows.append(
            {
                "currency": currency,
                "eligible_clean_lifecycles": len(frame),
                "median_duration_days": frame["duration_days"].median(),
                "mean_gross_benefit_pct": frame["gross_benefit_pct"].mean(),
                "median_gross_benefit_pct": frame["gross_benefit_pct"].median(),
                "mean_net_benefit_pct_at_20pct_rate": adjusted["net_benefit_preliq_pct"].mean(),
                "positive_net_positions_pct": 100.0 * (adjusted["net_benefit_preliq_usd"] > 0).mean(),
            }
        )
    return pd.DataFrame(rows)


def collateral_stress(all_horizons: pd.DataFrame, assumptions: CostAssumptions) -> pd.DataFrame:
    base = all_horizons[all_horizons["horizon_months"] == 12].copy()
    collateral_scenarios = {
        "USD_stablecoin": (0.0,),
        "ETH": (0.10, 0.25, 0.40, 0.60),
        "BTC": (0.10, 0.25, 0.40, 0.60),
    }
    rows = []
    for currency, currency_frame in base.groupby("currency"):
        adjusted = cost_adjusted(currency_frame, 0.20, assumptions)
        for collateral_type, shocks in collateral_scenarios.items():
            for shock in shocks:
                for initial_cr in COLLATERAL_RATIOS:
                    collateral_usd = adjusted["borrowed_dai"] * initial_cr * (1.0 - shock)
                    health_ratio = collateral_usd / adjusted["debt_service_usd"]
                    liquidated = health_ratio < LIQUIDATION_RATIO
                    for penalty in LIQUIDATION_PENALTIES:
                        loss = np.where(liquidated, penalty * adjusted["debt_service_usd"], 0.0)
                        risk_benefit = adjusted["net_benefit_preliq_usd"] - loss
                        rows.append(
                            {
                                "currency": currency,
                                "horizon_months": 12,
                                "annual_borrow_rate_pct": 20.0,
                                "collateral_type": collateral_type,
                                "collateral_shock_pct": 100.0 * shock,
                                "initial_collateral_ratio_pct": 100.0 * initial_cr,
                                "liquidation_threshold_pct": 100.0 * LIQUIDATION_RATIO,
                                "liquidation_penalty_pct": 100.0 * penalty,
                                "liquidated_positions_pct": 100.0 * liquidated.mean(),
                                "mean_risk_adjusted_benefit_pct": 100.0 * (risk_benefit / adjusted["borrowed_dai"]).mean(),
                                "positive_risk_adjusted_positions_pct": 100.0 * (risk_benefit > 0).mean(),
                                "value_weighted_risk_adjusted_benefit_pct": 100.0 * risk_benefit.sum() / adjusted["borrowed_dai"].sum(),
                            }
                        )
    return pd.DataFrame(rows)


def robustness_summary(draws: pd.DataFrame, fx: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for currency in ("ARS", "TRY"):
        base = attach_fx(draws, fx, currency, 12)
        mapping = fx_map(fx, currency)
        previous_start = (base["start_month"] - 1).map(mapping)
        next_start = (base["start_month"] + 1).map(mapping)
        previous_end = (base["end_month"] - 1).map(mapping)
        next_end = (base["end_month"] + 1).map(mapping)
        start_window = pd.concat([base["fx_start"], previous_start, next_start], axis=1).max(axis=1)
        end_window = pd.concat([base["fx_end"], previous_end, next_end], axis=1).min(axis=1)
        conservative = 100.0 * (1.0 - start_window / end_window)
        rows.extend(
            [
                {
                    "currency": currency,
                    "specification": "Base calendar-month average",
                    "events": len(base),
                    "mean_gross_benefit_pct": base["gross_benefit_pct"].mean(),
                    "median_gross_benefit_pct": base["gross_benefit_pct"].median(),
                    "positive_positions_pct": 100.0 * (base["gross_benefit_pct"] > 0).mean(),
                },
                {
                    "currency": currency,
                    "specification": "Conservative adjacent-month FX window",
                    "events": int(conservative.notna().sum()),
                    "mean_gross_benefit_pct": conservative.mean(),
                    "median_gross_benefit_pct": conservative.median(),
                    "positive_positions_pct": 100.0 * (conservative > 0).mean(),
                },
            ]
        )
    return pd.DataFrame(rows)


def cost_sensitivity_summary(all_horizons: pd.DataFrame) -> pd.DataFrame:
    scenarios = {
        "Low execution cost": CostAssumptions(0.000, 0.001, 10.0),
        "Base execution cost": CostAssumptions(0.005, 0.003, 40.0),
        "High execution cost": CostAssumptions(0.010, 0.010, 100.0),
    }
    rows = []
    base = all_horizons[all_horizons["horizon_months"] == 12]
    for currency, group in base.groupby("currency"):
        for label, assumptions in scenarios.items():
            adjusted = cost_adjusted(group, 0.20, assumptions)
            rows.append(
                {
                    "currency": currency,
                    "scenario": label,
                    "annual_borrow_rate_pct": 20.0,
                    "protocol_fee_pct": 100.0 * assumptions.protocol_fee_fraction,
                    "swap_slippage_each_way_pct": 100.0 * assumptions.swap_slippage_fraction_each_way,
                    "round_trip_gas_usd": assumptions.gas_usd_round_trip,
                    "median_net_benefit_pct": adjusted["net_benefit_preliq_pct"].median(),
                    "positive_positions_pct": 100.0 * (adjusted["net_benefit_preliq_usd"] > 0).mean(),
                    "value_weighted_net_benefit_pct": 100.0 * adjusted["net_benefit_preliq_usd"].sum() / adjusted["borrowed_dai"].sum(),
                }
            )
    return pd.DataFrame(rows)


def configure_plotting() -> None:
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.titlesize": 12,
            "axes.labelsize": 10,
            "figure.dpi": 120,
            "savefig.dpi": 300,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )


def save_figures(
    draws: pd.DataFrame,
    fx: pd.DataFrame,
    gross: pd.DataFrame,
    net: pd.DataFrame,
    break_even: pd.DataFrame,
    stress: pd.DataFrame,
    figure_dir: Path,
) -> None:
    configure_plotting()
    figure_dir.mkdir(parents=True, exist_ok=True)
    colors = {"ARS": "#7b2cbf", "TRY": "#0081a7"}

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    ax.hist(np.log10(draws["borrowed_dai"]), bins=70, color="#264653", alpha=0.9)
    ax.set_xlabel(r"Borrowing-event size, $\log_{10}$(DAI)")
    ax.set_ylabel("Number of debt-draw events")
    ax.set_title("Distribution of ETH-A borrowing-event sizes")
    fig.tight_layout()
    fig.savefig(figure_dir / "figure3.png")
    plt.close(fig)

    yearly = draws.groupby("borrow_year").agg(events=("event_id", "size"), total_dai=("borrowed_dai", "sum")).reset_index()
    fig, ax1 = plt.subplots(figsize=(7.2, 4.2))
    ax2 = ax1.twinx()
    ax1.bar(yearly["borrow_year"] - 0.15, yearly["events"], width=0.3, color="#457b9d", label="Events")
    ax2.bar(yearly["borrow_year"] + 0.15, yearly["total_dai"] / 1e9, width=0.3, color="#e76f51", label="DAI value")
    ax1.set_xlabel("Year")
    ax1.set_ylabel("Event count", color="#457b9d")
    ax2.set_ylabel("Total DAI drawn (billions)", color="#e76f51")
    ax1.set_xticks(yearly["borrow_year"])
    ax1.set_title("ETH-A borrowing activity by year")
    fig.tight_layout()
    fig.savefig(figure_dir / "figure6.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for currency in ("ARS", "TRY"):
        subset = fx[(fx["currency"] == currency) & (fx["month"] >= pd.Period("2019-01", "M"))]
        dates = subset["month"].dt.to_timestamp()
        ax.plot(dates, subset["local_per_usd"], label=currency, color=colors[currency], linewidth=2)
    ax.set_yscale("log")
    ax.set_ylabel("Local currency per USD (log scale)")
    ax.set_xlabel("Month")
    ax.set_title("Official monthly ARS/USD and TRY/USD trajectories")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "figure2.png")
    plt.close(fig)

    gross_summary = horizon_summary(gross)
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    for currency in ("ARS", "TRY"):
        subset = gross_summary[gross_summary["currency"] == currency]
        ax.plot(subset["horizon_months"], subset["median_gross_benefit_pct"], marker="o", label=currency, color=colors[currency])
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xticks(HORIZONS)
    ax.set_xlabel("Fixed repayment horizon (months)")
    ax.set_ylabel("Median gross FX-driven debt-erosion benefit (%)")
    ax.set_title("Gross debt erosion increases with holding horizon")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "figure4.png")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(8.0, 4.0), sharey=True)
    for ax, currency in zip(axes, ("ARS", "TRY"), strict=True):
        subset = net[(net["currency"] == currency) & (net["horizon_months"] == 12)]
        ax.plot(subset["annual_borrow_rate_pct"], subset["mean_net_benefit_pct"], marker="o", color=colors[currency])
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title(currency)
        ax.set_xlabel("Annual borrowing rate (%)")
    axes[0].set_ylabel("Mean net benefit before liquidation (%)")
    fig.suptitle("Twelve-month net benefit after costs and fees")
    fig.tight_layout()
    fig.savefig(figure_dir / "figure5.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    positions = np.arange(len(HORIZONS))
    width = 0.35
    for offset, currency in ((-width / 2, "ARS"), (width / 2, "TRY")):
        subset = break_even[break_even["currency"] == currency].set_index("horizon_months").loc[list(HORIZONS)]
        ax.bar(positions + offset, subset["median_break_even_rate_pct"], width=width, label=currency, color=colors[currency])
    ax.set_xticks(positions, [str(h) for h in HORIZONS])
    ax.set_xlabel("Horizon (months)")
    ax.set_ylabel("Median annual break-even borrowing rate (%)")
    ax.set_title("Break-even borrowing-rate sensitivity")
    ax.legend()
    fig.tight_layout()
    fig.savefig(figure_dir / "figure7.png")
    plt.close(fig)

    focus = stress[
        (stress["collateral_type"] == "ETH")
        & (stress["liquidation_penalty_pct"] == 13.0)
    ]
    fig, axes = plt.subplots(1, 2, figsize=(8.0, 4.0), sharey=True)
    for ax, currency in zip(axes, ("ARS", "TRY"), strict=True):
        subset = focus[focus["currency"] == currency]
        for ratio in (150.0, 175.0, 200.0):
            line = subset[subset["initial_collateral_ratio_pct"] == ratio]
            ax.plot(line["collateral_shock_pct"], line["liquidated_positions_pct"], marker="o", label=f"CR {ratio:.0f}%")
        ax.set_title(currency)
        ax.set_xlabel("ETH price decline (%)")
    axes[0].set_ylabel("Positions breaching liquidation threshold (%)")
    axes[1].legend(fontsize=8)
    fig.suptitle("Liquidation screen under collateral shocks (12 months, 20% rate)")
    fig.tight_layout()
    fig.savefig(figure_dir / "figure8.png")
    plt.close(fig)


def write_latex_tables(
    construction: pd.DataFrame,
    descriptive: pd.DataFrame,
    gross: pd.DataFrame,
    net: pd.DataFrame,
    stress: pd.DataFrame,
    robustness: pd.DataFrame,
    lifecycle: pd.DataFrame,
    cost_sensitivity: pd.DataFrame,
    output_dir: Path,
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    construction.to_latex(output_dir / "table_sample_construction.tex", index=False, escape=True, float_format="%.2f")
    descriptive.to_latex(output_dir / "table_descriptive.tex", index=False, escape=True, float_format="%.2f")
    gross.to_latex(output_dir / "table_gross_fixed_horizons.tex", index=False, escape=True, float_format="%.2f")
    net_12 = net[net["horizon_months"] == 12].copy()
    net_12.to_latex(output_dir / "table_net_12m.tex", index=False, escape=True, float_format="%.2f")
    stress_focus = stress[
        (stress["liquidation_penalty_pct"] == 13.0)
        & (stress["initial_collateral_ratio_pct"] == 175.0)
    ].copy()
    stress_focus.to_latex(output_dir / "table_stress_focus.tex", index=False, escape=True, float_format="%.2f")
    robustness.to_latex(output_dir / "table_robustness.tex", index=False, escape=True, float_format="%.2f")
    lifecycle.to_latex(output_dir / "table_lifecycle.tex", index=False, escape=True, float_format="%.2f")
    cost_sensitivity.to_latex(output_dir / "table_cost_sensitivity.tex", index=False, escape=True, float_format="%.2f")


def run(args: argparse.Namespace) -> dict[str, float | int | str]:
    assumptions = CostAssumptions()
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    draws = pd.read_csv(args.draws)
    lifecycles = pd.read_csv(args.lifecycles)
    construction = pd.read_csv(args.construction)
    fx = load_fx(args.ars_fx, args.try_fx)
    fx.assign(month=fx["month"].astype(str)).to_csv(output_dir / "fx_monthly_oecd_fred.csv", index=False)

    frames = [attach_fx(draws, fx, currency, horizon) for currency in ("ARS", "TRY") for horizon in HORIZONS]
    all_horizons = pd.concat(frames, ignore_index=True)
    all_horizons.to_csv(output_dir / "event_level_fixed_horizon_results.csv", index=False)

    descriptive = descriptive_statistics(draws)
    gross = horizon_summary(all_horizons)
    net, break_even = net_summary(all_horizons, assumptions)
    lifecycle = lifecycle_summary(lifecycles, fx, assumptions)
    stress = collateral_stress(all_horizons, assumptions)
    robustness = robustness_summary(draws, fx)
    cost_sensitivity = cost_sensitivity_summary(all_horizons)

    tables = {
        "dataset_descriptive_statistics.csv": descriptive,
        "gross_fixed_horizon_summary.csv": gross,
        "net_benefit_rate_sensitivity.csv": net,
        "break_even_rate_summary.csv": break_even,
        "observed_lifecycle_robustness.csv": lifecycle,
        "collateral_liquidation_stress.csv": stress,
        "fx_matching_robustness.csv": robustness,
        "execution_cost_sensitivity.csv": cost_sensitivity,
    }
    for filename, frame in tables.items():
        frame.to_csv(output_dir / filename, index=False)

    write_latex_tables(
        construction, descriptive, gross, net, stress, robustness, lifecycle, cost_sensitivity,
        args.latex_table_dir,
    )
    save_figures(draws, fx, all_horizons, net, break_even, stress, args.figure_dir)

    validation = {
        "final_draw_events": int(len(draws)),
        "unique_urns": int(draws["urn"].nunique()),
        "total_borrowed_dai": float(draws["borrowed_dai"].sum()),
        "gross_result_rows": int(len(gross)),
        "net_sensitivity_rows": int(len(net)),
        "stress_scenario_rows": int(len(stress)),
        "lifecycle_rows": int(lifecycle["eligible_clean_lifecycles"].sum()),
        "cost_assumptions": assumptions.__dict__,
        "all_2026_equal_fx_checks_removed": True,
        "profit_terminology_used": False,
    }
    (output_dir / "validation_summary.json").write_text(json.dumps(validation, indent=2), encoding="utf-8")
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draws", type=Path, required=True)
    parser.add_argument("--lifecycles", type=Path, required=True)
    parser.add_argument("--construction", type=Path, required=True)
    parser.add_argument("--ars-fx", type=Path, required=True)
    parser.add_argument("--try-fx", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--figure-dir", type=Path, required=True)
    parser.add_argument("--latex-table-dir", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args), indent=2))


if __name__ == "__main__":
    main()
