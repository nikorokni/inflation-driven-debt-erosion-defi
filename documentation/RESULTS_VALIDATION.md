# Results validation sheet

This sheet records the checks used to validate the revised manuscript and links every reported result to a machine-readable output. All percentage values are recalculated by `analysis/reproduce_analysis.py`; none are typed into the result files manually.

## Core identities

For event `i`, origination amount `P_i`, and local-currency-per-USD rates `E_0` and `E_h`:

```text
gross_benefit_pct = 100 * (1 - E_0 / E_h)
debt_service_usd = P_i * (E_0 / E_h) * (1 + annual_rate)^(h/12)
net_benefit_usd = P_i - debt_service_usd - protocol_fee - two_way_conversion_cost - gas
expected_liquidation_loss = sum_s(probability_s * penalty * debt_service_usd * breach_indicator_s)
risk_adjusted_benefit = net_benefit - expected_liquidation_loss
```

An equal start and end FX rate therefore produces exactly zero gross benefit. Financing and execution costs are reported only in net measures.

## Dataset anchors

| Check | Validated value | Source |
|---|---:|---|
| Raw successful Vat traces | 4,466,880 | `data/processed/sample_construction.csv` |
| Decoded ETH-A debt-changing events | 229,224 | `data/processed/sample_construction.csv` |
| Positive ETH-A debt draws before date/size filters | 137,426 | `data/processed/sample_construction.csv` |
| Final debt-draw events | 130,742 | `results/validation_summary.json` |
| Unique urn identifiers | 16,846 | `results/validation_summary.json` |
| Verified unique borrowers | Unavailable | urns cannot be equated to persons or controlled addresses |
| Total positive debt change | 13,318,097,854.94 DAI | `results/dataset_descriptive_statistics.csv` |
| Clean lifecycle candidates | 7,947 | `data/processed/sample_construction.csv` |
| Lifecycle spells with FX coverage per currency | 7,105 | `results/observed_lifecycle_robustness.csv` |

## Main numerical anchors

| Manuscript result | ARS | TRY | Machine-readable source |
|---|---:|---:|---|
| 12-month median gross benefit | 24.61% | 25.30% | `results/gross_fixed_horizon_summary.csv` |
| 12-month amount-weighted gross benefit | 28.11% | 40.83% | `results/gross_fixed_horizon_summary.csv` |
| Median net benefit, 20% rate/base costs | 2.78% | 6.71% | `results/net_benefit_rate_sensitivity.csv` |
| Positive net mappings, 20% rate/base costs | 62.05% | 57.27% | `results/net_benefit_rate_sensitivity.csv` |
| Median 12-month break-even annual rate | 23.85% | 31.90% | `results/break_even_rate_summary.csv` |
| Adjacent-month conservative median gross benefit | 21.85% | 17.05% | `results/fx_matching_robustness.csv` |
| Observed-duration median net benefit | -2.99% | -4.13% | `results/observed_lifecycle_robustness.csv` |
| Positive observed-duration net mappings | 13.19% | 14.58% | `results/observed_lifecycle_robustness.csv` |
| Expected-loss case: median risk-adjusted benefit | -4.44% | -0.47% | `results/liquidation_expected_loss_summary.csv` |
| Expected-loss case: loss as share of principal | 5.60% | 4.84% | `results/liquidation_expected_loss_summary.csv` |

The expected-loss case uses a 12-month horizon, 20% annual rate, base costs, 175% initial collateral ratio, 150% threshold, 13% penalty, and illustrative 10/25/40/60% crypto shocks weighted 40/30/20/10%.

## Resolved inconsistencies

1. The former 1,000-versus-981 discrepancy is eliminated. The corrected paper uses all 130,742 eligible decoded draws and reports every exclusion.
2. The April 2026 common endpoint is removed. Every main observation uses a fixed 3-, 6-, 12-, or 24-month endpoint; a restricted observed-duration test is separate.
3. Rows with equal start and end FX values no longer report non-zero gross benefit. `results/validation_summary.json` records this check.
4. “Profit” is not used as an outcome label. Gross, pre-liquidation net, and risk-adjusted benefits are distinct variables.
5. Event-level unweighted means, medians, positive shares, and amount-weighted aggregates are not interchanged.

## Output-to-paper map

| Paper element | Generated input |
|---|---|
| Table 1 | `sample_construction.csv`, `dataset_descriptive_statistics.csv` |
| Table 2 | `assumptions_parameters.csv` |
| Table 3 | `gross_fixed_horizon_summary.csv` |
| Table 4 | `net_benefit_rate_sensitivity.csv` |
| Table 5 | `collateral_liquidation_stress.csv`, `liquidation_expected_loss_summary.csv` |
| Table 6 | `fx_matching_robustness.csv`, `observed_lifecycle_robustness.csv`, `execution_cost_sensitivity.csv` |
| Figures 2–8 | `figures/figure2.png` through `figures/figure8.png` |

## Re-run acceptance checks

The reproduction is accepted only if the script completes without error, `validation_summary.json` reports `all_2026_equal_fx_checks_removed: true` and `profit_terminology_used: false`, all citation/reference checks compile, and the PDF's displayed tables agree with the CSV anchors above after rounding.

