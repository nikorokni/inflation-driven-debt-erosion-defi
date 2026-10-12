# FX-Driven Debt Erosion in Local-Currency DeFi Lending

**Counterfactual evidence from MakerDAO ETH-A draws**
Niko Rokni Lamouki, Salma Soofiyan and Julie Wall

[Manuscript](manuscript/main.pdf) · [Response for Salma](documentation/RESPONSE_TO_SALMA.pdf) · [Conditional cash-flow note](documentation/BORROWER_CASHFLOW_MODEL.pdf)

This is a **counterfactual accounting exercise**, not observed ARS/TRY borrowing, realised profit, an estimated liquidation probability or a protocol-solvency test. The repository name preserves its historical GitHub URL; the revised paper title correctly names the measured *FX depreciation*.

## Findings and boundaries

| Item | ARS | TRY |
|---|---:|---:|
| Selected clean, repaid spells with FX coverage | 7,105 | 7,105 |
| Median observed spell duration | 6.95 days | 6.95 days |
| Median *hypothetical* net benefit over observed durations, daily reference FX | -2.86% | -4.30% |
| Median *hypothetical* net benefit over observed durations, monthly OECD/FRED FX | -3.00% | -4.14% |
| Positive share over observed durations, daily reference FX | 9.85% | 15.57% |
| Median *hypothetical* net benefit at fixed 12 months | 2.67% | 6.59% |
| Median *hypothetical* net benefit at fixed 24 months | 25.58% | 37.19% |
| First-draw-per-urn median at fixed 12 months | 0.86% | -4.54% |
| Largest 1% of draws: share of signed 12-month net benefit | 72.49% | 66.85% |

The raw selection contains **130,742 draw events** in **16,846 urns**, not 130,742 independent borrowers. We use DAI draw sizes and dates as a transparent *structural analog* for hypothetical LCU debts, without claiming that real ARS/TRY borrowers would choose the same sizes or dates. The clean repaid spells are a selected subset, and their reconstructed durations are used for *hypothetical* local-currency financing outcomes. **57.21%** of their entry/exit pairs are in the same calendar month: monthly matching forces zero FX movement for those pairs. Archived BCRA ARS/USD and ECB cross-derived TRY/USD daily references are now used for observed-duration results; a same-source monthly mean and the original OECD/FRED monthly data are separately compared on the same spells. Fixed 12- and 24-month holding periods still use archived monthly OECD/FRED FX and are imposed scenarios. Neither daily reference nor monthly average establishes an executable rate, particularly for ARS.

The **20% effective annual borrowing rate is a round illustrative scenario**, not an observed peso/lira lending rate. The selected daily-FX medians are negative for both currencies at 5%, 20% and 40%; [the full rate grid](results/observed_daily_rate_sensitivity.csv) and [the frequency/source comparison](results/observed_fx_frequency_comparison.csv) give exact counts, medians and positive shares. No validated parallel ARS price is supplied. A retrospective same-date reference quote could also have been published after a particular on-chain transaction.

The earlier risk-adjusted liquidation medians are **withdrawn**. The borrower cash-flow code has mutually exclusive voluntary repayment and collateral-sale branches. The manuscript reports only a terminal collateral-ratio screen because no within-horizon collateral path, auction close-out or defensible shock probability distribution is available. It does not claim ETH/BTC-specific returns from identical assumed percentage shocks.

## Reproduce

Requires Python with pandas, numpy, matplotlib and xlrd (pinned in requirements.txt). From the repository root:

    python -m pip install -r requirements.txt
    bash run_all.sh

This runs the borrower-accounting and daily-quote checks, rebuilds the CSV results, eight generated LaTeX results tables and four figures from the tracked processed files and archived monthly/daily FX inputs, and builds the PDFs when LaTeX and Pandoc are installed. The manuscript also includes two descriptive tables for sample construction and modelling assumptions, checked against tracked input records. To start from the original external MakerDAO trace archive, obtain it using [the documented source pointer and SHA-256](documentation/SOURCES.md), then run:

    bash run_all.sh /path/to/Data_July_2023.zip

The included processed draw and lifecycle files allow reproduction without downloading the large raw archive. Each event retains an urn identifier and a transaction hash. Dates, rates, and amounts are described in the manuscript; only clean repaid spells contribute to the observed-duration check. The cost assumptions are a 20% **effective annual** LCU rate, a 0.5% upfront fee paid outside the loan, 0.3% conversion friction at each voluntary entry/exit, and USD 20 opening plus USD 20 voluntary closing gas. These are scenarios, not observed LCU protocol prices.

## Files

- analysis/borrower_cashflows.py: conditional borrower and issuer sale accounting.
- analysis/reproduce_analysis.py: all empirical summaries, tables and charts.
- analysis/daily_fx.py: archived BCRA/ECB reference parsing, ECB cross-rate and as-of calendar matching.
- tests/test_daily_fx.py: verifies nonfuture quote matching and distinct within-month reference observations.
- tests/test_borrower_cashflows.py: mutually exclusive route and conservation examples.
- results/main_summary.csv: observed-duration and fixed-horizon outcomes.
- results/urn_robustness.csv and results/urn_draw_counts.csv: dependence checks.
- results/large_event_concentration.csv and results/origination_month_concentration.csv: signed benefit contribution.
- results/position_size_sensitivity.csv and results/observed_duration_bands.csv: robustness.
- results/terminal_collateral_ratio_screen.csv: deterministic screen, not a liquidation estimate.
- results/fx_daily_reference.csv, observed_fx_frequency_comparison.csv and observed_daily_rate_sensitivity.csv: archived daily marks, matched-source comparison and rate grid.
- documentation/RESULTS_VALIDATION.md: headline-to-output reconciliation.
- documentation/COLLEAGUE_COMMENTS_RESPONSE.md: four new comments and reproducible changes.
- manuscript/main.tex and manuscript/references.tex: article sources.

No unverified ARS parallel-market observations, deployed local-currency liabilities, reserve amounts or auction prices have been fabricated.
