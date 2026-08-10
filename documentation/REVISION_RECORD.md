# Revision record against the supervisor comments

## Empirical direction and reproducibility

- Reframed the paper as a counterfactual empirical study rather than a conceptual protocol proposal.
- Replaced the unsupported 1,000/981-event sample with 130,742 decoded ETH-A debt-draw events from a public, peer-reviewed dataset.
- Added exact source SQL, transaction-level hashes, raw-data checksum, FX series IDs, scripts, intermediate files, and one-command reproduction.
- Removed the April 2026 terminal date and all inconsistent equal-FX endpoint rows.

## Interpretation

- Replaced "profit" and "realised gain" language with gross FX-driven debt erosion, pre-liquidation net benefit, and risk-adjusted benefit.
- States throughout that the outcome is counterfactual and does not represent actual MakerDAO borrower returns.

## Research design

- Added RQ1-RQ4 and mapped contributions to them.
- Added fixed 3-, 6-, 12-, and 24-month horizons.
- Added annual-rate sensitivity from 5% to 120%, protocol fees, two-way conversion costs, and fixed gas.
- Added low/base/high execution-cost scenarios and event-level break-even rates.
- Added a restricted observed-duration lifecycle robustness check.
- Added collateral ratios, liquidation thresholds, penalties, crypto shocks, and a stablecoin-collateral benchmark.
- Added conservative adjacent-month FX matching.

## Manuscript structure and claims

- Rebuilt the related-work section around DeFi lending, stablecoin risk, and inflation-driven debt erosion, including a critical gap table.
- Simplified the system architecture and moved it to supporting context.
- Added a dedicated protocol-solvency, peg-sustainability, and loss-allocation section.
- Added explicit limitations for official ARS rates, missing top-level traces, counterfactual behaviour, scenario parameters, and static collateral stress.
- Replaced decorative conceptual figures with generated data figures.
- Added data- and code-availability statements.

