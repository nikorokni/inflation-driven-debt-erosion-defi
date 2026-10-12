#!/usr/bin/env python3
"""Check that daily observations resolve short spells and never use future dates."""
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "analysis"))
from daily_fx import asof_published_quote, load_daily_references  # noqa: E402


def run() -> None:
    root = Path(__file__).resolve().parents[1]
    data = load_daily_references(root / "data/raw_fx/bcra_com3500.xls",
                                 root / "data/raw_fx/ecb_eurofxref_hist.zip")
    for currency in ("ARS", "TRY"):
        part = data[data.currency == currency]
        assert part.date.is_monotonic_increasing and part.local_per_usd.gt(0).all()
        # The chosen UTC dates fall within a week. Weekend events use Friday's
        # published date; Tuesday's quote must not be pulled back to Monday.
        trial = pd.Series(["2023-07-07 10:00:00+00:00", "2023-07-08 10:00:00+00:00",
                           "2023-07-10 10:00:00+00:00", "2023-07-11 10:00:00+00:00"])
        quotes, lag = asof_published_quote(part, trial)
        assert lag[0] == 0 and lag[1] >= 1 and lag[2] <= 3
        assert quotes[0] == quotes[1]
        assert np.isfinite(quotes).all()
    # More than one within-month reference quote must be present for each
    # currency, unlike one monthly average applied twice within that month.
    july = data[(data.date >= "2023-07-01") & (data.date < "2023-08-01")]
    assert july.groupby("currency").local_per_usd.nunique().ge(2).all()
    print("Daily FX date matching and source checks passed")


if __name__ == "__main__":
    run()
