# FX-Driven Debt Erosion in Local-Currency DeFi Lending

**Counterfactual evidence from MakerDAO ETH-A draws**
Niko Rokni Lamouki and Salma Soofiyan

[Revised paper](manuscript/main.pdf) · [Response to reviewer](documentation/RESPONSE_TO_REVIEWERS.pdf) · [Conditional cash-flow note](documentation/BORROWER_CASHFLOW_MODEL.pdf)

This is a **counterfactual accounting exercise**, not observed ARS/TRY borrowing, realised profit, an estimated liquidation probability or a protocol-solvency test. The repository name preserves its historical GitHub URL; the revised paper title correctly names the measured *FX depreciation*.

## Findings and boundaries

| Item | ARS | TRY |
|---|---:|---:|
| Selected clean, repaid spells with FX coverage | 7,105 | 7,105 |
| Median observed spell duration | 6.95 days | 6.95 days |
| Median *hypothetical* net benefit over observed durations | -3.00% | -4.14% |
| Median *hypothetical* net benefit at fixed 12 months | 2.67% | 6.59% |
| Median *hypothetical* net benefit at fixed 24 months | 25.58% | 37.19% |
| First-draw-per-urn median at fixed 12 months | 0.86% | -4.54% |
| Largest 1% of draws: share of signed 12-month net benefit | 72.49% | 66.85% |

The raw selection contains **130,742 draw events** in **16,846 urns**, not 130,742 independent borrowers. The clean repaid spells are a selected subset, and their reconstructed durations are used for *hypothetical* local-currency financing outcomes. Fixed 12- and 24-month holding periods are imposed scenarios. Official ARS/USD and TRY/USD monthly averages do not establish executable rates, particularly for ARS.

The earlier risk-adjusted liquidation medians are **withdrawn**. The borrower cash-flow code has mutually exclusive voluntary repayment and collateral-sale branches. The manuscript reports only a terminal collateral-ratio screen because no within-horizon collateral path, auction close-out or defensible shock probability distribution is available. It does not claim ETH/BTC-specific returns from identical assumed percentage shocks.

## Reproduce

Requires Python with pandas, numpy and matplotlib (pinned in requirements.txt). From the repository root:

    python -m pip install -r requirements.txt
    bash run_all.sh

This runs seven independent accounting checks, rebuilds the results, six generated LaTeX results tables and four figures from the tracked processed files and archived FX inputs, and builds the PDFs when LaTeX and Pandoc are installed. The manuscript also includes two descriptive tables for sample construction and modelling assumptions, checked against tracked input records. To start from the original external MakerDAO trace archive, obtain it using [the documented source pointer and SHA-256](documentation/SOURCES.md), then run:

    bash run_all.sh /path/to/Data_July_2023.zip

The included processed draw and lifecycle files allow reproduction without downloading the large raw archive. Each event retains an urn identifier and a transaction hash. Dates, rates, and amounts are described in the manuscript; only clean repaid spells contribute to the observed-duration check. The cost assumptions are a 20% **effective annual** LCU rate, a 0.5% upfront fee paid outside the loan, 0.3% conversion friction at each voluntary entry/exit, and USD 20 opening plus USD 20 voluntary closing gas. These are scenarios, not observed LCU protocol prices.

## Files

- analysis/borrower_cashflows.py: conditional borrower and issuer sale accounting.
- analysis/reproduce_analysis.py: all empirical summaries, tables and charts.
- tests/test_borrower_cashflows.py: mutually exclusive route and conservation examples.
- results/main_summary.csv: observed-duration and fixed-horizon outcomes.
- results/urn_robustness.csv and results/urn_draw_counts.csv: dependence checks.
- results/large_event_concentration.csv and results/origination_month_concentration.csv: signed benefit contribution.
- results/position_size_sensitivity.csv and results/observed_duration_bands.csv: robustness.
- results/terminal_collateral_ratio_screen.csv: deterministic screen, not a liquidation estimate.
- documentation/RESULTS_VALIDATION.md: headline-to-output reconciliation.
- manuscript/main.tex and manuscript/references.tex: article sources.

No unverified ARS parallel-market observations, deployed local-currency liabilities, reserve amounts or auction prices have been fabricated.
