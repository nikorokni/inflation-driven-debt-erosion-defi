# Additional methodological comments and changes

## 1. Why use MakerDAO draws?

We use the publicly decoded ETH-A draw size, UTC date and urn as observed *inputs* to a counterfactual loan-accounting exercise. MakerDAO offers a transparent, reproducible on-chain sequence of collateralized debt events, so it permits transparent exposure windows and dependence checks. DAI draw behavior is not a sample of prospective ARS or TRY borrowers. The manuscript now explains this choice and its external-validity limits in the data section, including repeated draws, skewed sizes, selection of clean repayments, one vault asset and one historical window. The size, urn and month checks remain descriptive rather than estimates of a local-currency borrower population.

## 2. Daily FX for short spells

The previously used monthly OECD/FRED endpoints mechanically gave zero FX movement when entry and exit shared a month. We archived official BCRA A3500 daily ARS/USD and ECB daily TRY/EUR and USD/EUR reference inputs, calculating TRY/USD as their ratio. The code selects the latest published *date no later than* the UTC event date; it never interpolates or pulls a future-date quote. For the identical 7,105 selected spells per currency, 57.21% begin and end in one calendar month. Daily marks produce median net benefits of -2.86% ARS and -4.30% TRY at the illustrative 20% effective annual rate; OECD/FRED monthly gives -3.00% and -4.14%, while arithmetic monthly means derived from the same daily sources give -3.02% and -4.16%. Gross FX movement is nonzero in 57.07% and 58.62% of same-month spells under daily marks. Tables and generated CSVs show the full comparison. These are *reference valuations*; same-date publication time and executable transaction prices remain unobserved.

## 3. Financing rate and official FX realism

The 20% effective annual rate is identified in the main text as a round hypothetical financing scenario, with no claim of calibration to an observed local-currency protocol or domestic credit offer. The main-text rate table and `results/observed_daily_rate_sensitivity.csv` show six rates from 5% to 120%; the medians are negative for both currencies even at 5%. Fixed 12-month scenarios retain their own rate grid in `results/rate_sensitivity.csv`. A BCRA wholesale reference, ECB reference cross and OECD/FRED monthly averages are not demonstrated executable rates. We cannot infer a parallel-market ARS path or convert this sensitivity into an estimate of realized borrower gains. The manuscript makes that restriction visible in the abstract, methods, results and conclusion.

## 4. Paper focus

The empirical result remains the duration-sensitive hypothetical FX-debt comparison. The state-dependent liquidation formula is retained as a necessary accounting boundary: voluntary repayment and collateral sale cannot both be charged to one borrower. Its numerical examples and conservation tests are in the separate model note and code. The terminal collateral-ratio grid, table and figure now sit in a clearly labelled Appendix and are never used to adjust the empirical net-benefit medians. The balance-sheet identity is shortened to a schematic accounting boundary, without an estimated solvency result or claims about peg performance.

## Reproduce and inspect

Run `bash run_all.sh` from the repository root. The source URLs, SHA-256 values and transformations are in `documentation/SOURCES.md`; see `analysis/daily_fx.py`, `analysis/reproduce_analysis.py`, `tests/test_daily_fx.py`, `results/observed_fx_frequency_comparison.csv`, `results/observed_daily_rate_sensitivity.csv`, and `tables/daily_fx.tex` / `tables/daily_rate.tex`. The archived MakerDAO draw and lifecycle data, original monthly series and daily reference input files are tracked in the repository.
