"""Read archived official daily reference rates and match past quotes to UTC dates.

The BCRA A3500 workbook quotes ARS per USD. ECB daily reference rates
quote both TRY and USD per EUR, so TRY/USD is TRY/EUR divided by USD/EUR.
Neither reference rate is evidence of an executable borrower conversion.
"""
from __future__ import annotations

from pathlib import Path
import zipfile

import numpy as np
import pandas as pd


def load_daily_references(bcra_xls: Path, ecb_zip: Path) -> pd.DataFrame:
    raw = pd.read_excel(bcra_xls, sheet_name="TCR diario y TCNPM", header=None, engine="xlrd")
    ars = pd.DataFrame({
        "date": pd.to_datetime(raw.iloc[4:, 2], errors="coerce", format="%Y-%m-%d"),
        "local_per_usd": pd.to_numeric(raw.iloc[4:, 3], errors="coerce"),
    }).dropna()
    ars["currency"] = "ARS"

    with zipfile.ZipFile(ecb_zip) as archive:
        raw = pd.read_csv(archive.open("eurofxref-hist.csv"), low_memory=False)
    eur_usd = pd.to_numeric(raw["USD"], errors="coerce")
    eur_try = pd.to_numeric(raw["TRY"], errors="coerce")
    tr = pd.DataFrame({
        "date": pd.to_datetime(raw["Date"], errors="coerce"),
        "local_per_usd": eur_try / eur_usd,
    }).dropna()
    tr["currency"] = "TRY"

    data = pd.concat([ars, tr], ignore_index=True)
    data = data[(data.local_per_usd > 0) & (data.date >= "2019-12-01") &
                (data.date <= "2023-08-31")].copy()
    if data.duplicated(["currency", "date"]).any():
        raise ValueError("Duplicate published FX reference dates")
    return data[["currency", "date", "local_per_usd"]].sort_values(
        ["currency", "date"]).reset_index(drop=True)


def asof_published_quote(daily: pd.DataFrame, timestamps: pd.Series) -> tuple[np.ndarray, np.ndarray]:
    """Most recent reference date no later than each UTC calendar date.

    Rates are retrospective valuation marks: the publication time within a
    date can be later than an individual MakerDAO event on that date.
    """
    dates = daily.date.to_numpy(dtype="datetime64[D]")
    values = daily.local_per_usd.to_numpy(dtype=float)
    event_dates = pd.to_datetime(timestamps, utc=True).dt.tz_convert(None).to_numpy(dtype="datetime64[D]")
    indices = np.searchsorted(dates, event_dates, side="right") - 1
    if (indices < 0).any() or (event_dates > dates[-1]).any():
        raise ValueError("Event has no applicable archived FX quote")
    lag_days = (event_dates - dates[indices]).astype("timedelta64[D]").astype(int)
    return values[indices], lag_days


def same_source_monthly(daily: pd.DataFrame) -> dict[pd.Period, float]:
    grouped = daily.assign(month=daily.date.dt.to_period("M")).groupby("month")
    return grouped.local_per_usd.mean().to_dict()
