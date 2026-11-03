#!/usr/bin/env python3
"""Reproduce additional checks prompted by the annotated manuscript.

All scenarios reuse the tracked MakerDAO and FX inputs and the existing
survivor cash-flow function. No synthetic exchange-rate history is introduced.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from borrower_cashflows import CostAssumptions
from daily_fx import asof_published_quote, load_daily_references
from reproduce_analysis import (CURRENCIES, fixed_frame, fx_lookup, load_fx,
                                metric, observed_fx_comparison, prepare_lifecycles,
                                tex_tabular, with_cashflows)

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "results"
TABLES = ROOT / "tables"
RELATIVE_PREMIUM_RATIOS = (0.80, 1.00, 1.10, 1.25, 1.50)
GAS_COSTS = (0.0, 20.0, 40.0, 80.0)
CONVERSION_COSTS = (0.0, 0.003, 0.01)


def selection_flow(lifecycles: pd.DataFrame) -> pd.DataFrame:
    clean = lifecycles.single_draw_clean.astype(str).str.lower().eq("true") & lifecycles.status.eq("repaid")
    stages = [("Single-draw repaid clean spells", int(clean.sum()))]
    clean &= lifecycles.start_dai.ge(1)
    stages.append(("After minimum 1 DAI", int(clean.sum())))
    clean &= lifecycles.duration_days.gt(0)
    stages.append(("After strictly positive duration", int(clean.sum())))
    start = pd.to_datetime(lifecycles.start_timestamp, utc=True)
    clean &= start.ge(pd.Timestamp("2020-01-01", tz="UTC"))
    stages.append(("After start on or after 2020-01-01", int(clean.sum())))
    return pd.DataFrame(stages, columns=["stage", "n"])


def sample_description(draws: pd.DataFrame, observed: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for label, amount, urns, dates in [
        ("All eligible draw events", draws.borrowed_dai, draws.urn,
         pd.to_datetime(draws.timestamp, utc=True)),
        ("Selected clean repaid spells", observed.borrowed_dai, observed.urn, observed.start_dt),
    ]:
        rows.append({"sample": label, "n": len(amount), "unique_urns": int(urns.nunique()),
                     "median_principal_usd": float(amount.median()),
                     "p90_principal_usd": float(amount.quantile(.9)),
                     "share_opened_2020_pct": float(100 * dates.dt.year.eq(2020).mean()),
                     "share_opened_2021_pct": float(100 * dates.dt.year.eq(2021).mean())})
    return pd.DataFrame(rows)


def cashflow_components(frame: pd.DataFrame, currency: str, sample: str) -> dict:
    p = frame.borrowed_dai.to_numpy()
    no_interest = p * frame.fx_start.to_numpy() / frame.fx_close.to_numpy()
    debt = frame.debt_usd.to_numpy()
    total = p.sum()
    components = {
        "gross_fx_pct": 100 * (p - no_interest).sum() / total,
        "interest_drag_pct": 100 * (debt - no_interest).sum() / total,
        "opening_fee_pct": 100 * (0.005 * p).sum() / total,
        "conversion_pct": 100 * (0.003 * (p + debt)).sum() / total,
        "gas_pct": 100 * (40.0 * len(frame)) / total,
    }
    weighted = 100 * frame.net_usd.sum() / total
    reconstructed = (components["gross_fx_pct"] - components["interest_drag_pct"]
                     - components["opening_fee_pct"] - components["conversion_pct"]
                     - components["gas_pct"])
    if not np.isclose(weighted, reconstructed, atol=1e-9):
        raise AssertionError(f"Cash-flow components do not reconcile: {sample} {currency}")
    return {"currency": currency, "sample": sample, "n": len(frame),
            "median_gross_pct": float(frame.gross_pct.median()),
            "median_net_pct": float(frame.net_pct.median()),
            "positive_net_pct": 100 * (frame.net_usd > 0).mean(),
            **components, "weighted_net_pct": weighted}


def run() -> None:
    OUT.mkdir(exist_ok=True)
    TABLES.mkdir(exist_ok=True)
    draws = pd.read_csv(ROOT / "data/processed/makerdao_eth_a_draw_events_analysis.csv", low_memory=False)
    lifecycles = pd.read_csv(ROOT / "data/processed/makerdao_eth_a_lifecycles.csv", low_memory=False)
    monthly = load_fx({"ARS": ROOT / "data/raw_fx/ars_usd_fred.csv",
                       "TRY": ROOT / "data/raw_fx/try_usd_fred.csv"})
    daily = load_daily_references(ROOT / "data/raw_fx/bcra_com3500.xls",
                                  ROOT / "data/raw_fx/ecb_eurofxref_hist.zip")
    flow = selection_flow(lifecycles)
    flow.to_csv(OUT / "selected_spells_flow.csv", index=False)
    samples, same_sample, lag_rows, premium_rows, cost_rows, components = [], [], [], [], [], []

    for currency in CURRENCIES:
        lookup = fx_lookup(monthly, currency)
        selected_monthly = prepare_lifecycles(lifecycles, lookup)
        selected_daily, _, _, _ = observed_fx_comparison(selected_monthly, daily, currency)
        assert len(selected_daily) == 7105 and int(flow.n.iloc[-1]) == len(selected_daily)
        if currency == "ARS":
            samples.append(sample_description(draws, selected_daily))

        prior = selected_daily.copy()
        daily_source = daily[daily.currency == currency]
        prior["fx_start"], start_lag = asof_published_quote(
            daily_source, prior.start_dt, strictly_prior_date=True)
        prior["fx_close"], end_lag = asof_published_quote(
            daily_source, prior.end_dt, strictly_prior_date=True)
        prior = with_cashflows(prior, prior.duration_days.to_numpy() / 365.25)
        for label, frame, lag in [
            ("On or before UTC date", selected_daily, None),
            ("Strictly prior reference date", prior, np.concatenate([start_lag, end_lag])),
        ]:
            row = metric(frame, label, currency=currency, horizon="observed")
            if lag is not None:
                row["median_quote_lag_days"] = float(np.median(lag))
                row["p95_quote_lag_days"] = float(np.percentile(lag, 95))
            lag_rows.append(row)

        selected_seed = selected_daily[["urn", "timestamp", "borrowed_dai"]].copy()
        selected_seed["event_id"] = [f"clean-{i}" for i in range(len(selected_seed))]
        selected_seed["order"] = np.arange(len(selected_seed))
        same_sample.append(metric(selected_daily, "Selected clean spells; daily FX",
                                  currency=currency, horizon="observed"))
        same_sample.append(metric(selected_monthly, "Selected clean spells; monthly FX",
                                  currency=currency, horizon="observed"))
        fixed12_all = None
        for months in (3, 6, 12, 24):
            selected_fixed = fixed_frame(selected_seed, lookup, months)
            if len(selected_fixed) != len(selected_seed):
                raise ValueError("Fixed-horizon coverage differs for selected spells")
            fixed_cash = with_cashflows(selected_fixed, months / 12)
            same_sample.append(metric(fixed_cash, "Selected clean spell starts; monthly FX",
                                      currency=currency, horizon=f"{months}m"))
            if months == 12:
                fixed12_all = with_cashflows(fixed_frame(draws, lookup, 12), 1)
                same_sample.append(metric(fixed12_all, "All eligible draw starts; monthly FX",
                                          currency=currency, horizon="12m"))
                components.append(cashflow_components(fixed12_all, currency, "All draws; 12m"))
        components.append(cashflow_components(selected_daily, currency, "Clean spells; observed"))

        for label, frame, years in [
            ("Clean spells; observed", selected_daily, selected_daily.duration_days.to_numpy() / 365.25),
            ("All draws; 12m", fixed12_all, 1),
        ]:
            for gas in GAS_COSTS:
                for spread in CONVERSION_COSTS:
                    costs = CostAssumptions(protocol_fee_fraction=.005,
                                            conversion_fraction_each_way=spread,
                                            gas_usd_round_trip=gas)
                    calculated = with_cashflows(frame, years, .20, costs)
                    cost_rows.append({**metric(calculated, label, currency=currency,
                                               horizon="observed" if "Clean" in label else "12m"),
                                      "gas_usd_round_trip": gas,
                                      "conversion_each_way_pct": 100 * spread})

        if currency == "ARS":
            for label, frame, years in [
                ("Clean spells; observed", selected_daily, selected_daily.duration_days.to_numpy() / 365.25),
                ("All draws; 12m", fixed12_all, 1),
            ]:
                for relative in RELATIVE_PREMIUM_RATIOS:
                    scenario = frame.copy()
                    scenario["fx_close"] *= relative
                    calculated = with_cashflows(scenario, years)
                    premium_rows.append({**metric(calculated, label, currency="ARS",
                                                  horizon="observed" if "Clean" in label else "12m"),
                                         "relative_exit_to_entry_premium": relative})

    sample = samples[0]
    cohort = pd.DataFrame(same_sample)
    lag = pd.DataFrame(lag_rows)
    premium = pd.DataFrame(premium_rows)
    costs = pd.DataFrame(cost_rows)
    decomp = pd.DataFrame(components)
    for name, frame in {
        "sample_comparison.csv": sample,
        "same_sample_horizon_comparison.csv": cohort,
        "prior_quote_sensitivity.csv": lag,
        "illustrative_ars_premium_sensitivity.csv": premium,
        "gas_conversion_sensitivity.csv": costs,
        "cashflow_decomposition.csv": decomp,
    }.items():
        frame.to_csv(OUT / name, index=False)

    tex_tabular(TABLES / "sample_comparison.tex",
                ["Sample", "$N$", "Urns", "Median USD", "P90 USD", "2020 share"],
                [[r.sample, f"{int(r.n):,}", f"{int(r.unique_urns):,}",
                  f"{r.median_principal_usd:,.0f}", f"{r.p90_principal_usd:,.0f}",
                  f"{r.share_opened_2020_pct:.1f}"] for r in sample.itertuples()], "lrrrrr")
    tex_tabular(TABLES / "same_sample.tex",
                ["FX", "Entry sample and FX", "Exit", "$N$", "Median net", "Positive"],
                [[r.currency, r.sample, r.horizon, f"{int(r.n):,}",
                  f"{r.median_net_pct:.2f}", f"{r.positive_net_pct:.2f}"]
                 for r in cohort.itertuples() if r.horizon in ("observed", "12m", "24m")], "lllrrr")
    tex_tabular(TABLES / "cashflow_decomposition.tex",
                ["FX", "Sample", "FX gross", "Interest", "Fee", "Swap", "Gas", "Net"],
                [[r.currency, r.sample, f"{r.gross_fx_pct:.2f}", f"{r.interest_drag_pct:.2f}",
                  f"{r.opening_fee_pct:.2f}", f"{r.conversion_pct:.2f}", f"{r.gas_pct:.2f}",
                  f"{r.weighted_net_pct:.2f}"] for r in decomp.itertuples()], "llrrrrrr")
    tex_tabular(TABLES / "prior_quote.tex",
                ["FX", "Reference-date rule", "Net median", "Positive"],
                [[r.currency, r.sample, f"{r.median_net_pct:.2f}", f"{r.positive_net_pct:.2f}"]
                 for r in lag.itertuples()], "llrr")
    subset = costs[((costs.gas_usd_round_trip == 0) & (costs.conversion_each_way_pct == 0)) |
                   ((costs.gas_usd_round_trip == 40) & np.isclose(costs.conversion_each_way_pct, .3)) |
                   ((costs.gas_usd_round_trip == 80) & np.isclose(costs.conversion_each_way_pct, 1))]
    tex_tabular(TABLES / "cost_sensitivity.tex",
                ["FX", "Sample", "Gas USD", "Swap each", "Net median", "Positive"],
                [[r.currency, r.sample, f"{r.gas_usd_round_trip:.0f}",
                  f"{r.conversion_each_way_pct:.1f}%", f"{r.median_net_pct:.2f}",
                  f"{r.positive_net_pct:.2f}"] for r in subset.itertuples()], "llrrrr")
    tex_tabular(TABLES / "ars_premium.tex",
                ["Sample", "Exit/entry premium", "Net median", "Positive"],
                [[r.sample, f"{r.relative_exit_to_entry_premium:.2f}",
                  f"{r.median_net_pct:.2f}", f"{r.positive_net_pct:.2f}"]
                 for r in premium.itertuples()], "lrrr")
    print("Additional sample, quote, premium, cost, horizon and decomposition checks generated")


if __name__ == "__main__":
    run()
