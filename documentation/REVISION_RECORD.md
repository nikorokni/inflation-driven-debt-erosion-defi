# Point-by-point revision record

This document maps the supervisor/reviewer requirements to the corrected manuscript and replication package. It distinguishes completed changes from limitations that cannot be resolved without fabricating unavailable data.

## 1. Empirical direction and title

- Reframed the study as a reproducible counterfactual empirical analysis rather than a validated protocol proposal.
- Retained the architecture only as system context.
- Replaced the title with one identifying the debt-erosion outcome, local-currency DeFi setting, counterfactual design, MakerDAO activity, and ETH-A scope.

## 2. Data and code before numerical claims

- Added the public raw-archive pointer, exact source query, immutable source commit, SHA-256 checksum, decoder, processed files, FX source files, analysis script, generated outputs, and one-command reproduction.
- Documented that the corrected dataset is BigQuery-derived and that no Dune Analytics query or query ID was used.
- Defined each observation as a positive-debt ETH-A `Vat.frob` draw, which may be a first draw or additional borrowing and is not necessarily a vault opening.

## 3. Numerical inconsistencies

- Eliminated the unsupported 1,000/981 sample. The corrected final sample is 130,742 draws after explicit filters.
- Removed the April 2026 common endpoint and all old annual tables.
- Enforced the identity that equal start/end FX rates imply zero gross benefit.
- Regenerated every manuscript number from code; validation anchors are in `RESULTS_VALIDATION.md`.

## 4. Interpretation

- Replaced profit and realised-gain terminology with gross FX-driven debt erosion, pre-liquidation net benefit, and risk-adjusted benefit.
- Repeated the counterfactual—not realised—interpretation in the abstract, methods, results, discussion, limitations, and conclusion.

## 5–6. Research questions and contributions

- Added RQ1–RQ4 on gross debt erosion, cost-adjusted benefit, collateral/liquidation risk, and protocol solvency.
- Mapped four completed contributions directly to those questions.

## 7. Dataset and empirical design

- Table 1 now combines sample construction and descriptive statistics: raw and removed events, final events, urns, total/mean/median/SD/min/max amounts, dates, and lifecycle availability.
- Explicitly reports verified unique borrower addresses as unavailable. MakerDAO `urn` identifiers are vault accounting positions and are not mislabelled as persons.
- Records official OECD/FRED series IDs, monthly frequency, units, missing-value rule, event-month matching, fixed endpoints, and the official-versus-parallel ARS caveat.
- Distinguishes CPI inflation, FX depreciation, borrowing rates, real debt burden, and USD-equivalent repayment reduction; only FX directly enters the repayment mapping.

## 8. Repayment horizon

- Added fixed 3-, 6-, 12-, and 24-month event-level analyses.
- Added an observed-duration robustness test limited to 7,105 internally consistent spells per currency.
- Removed rather than retained the unsupported April 2026 upper-bound scenario.

## 9–10. Net benefit, rates, and fees

- Added explicit gross, debt-service, fee/cost, pre-liquidation net, expected-loss, and risk-adjusted equations.
- Added rates of 5, 10, 20, 40, 80, and 120%, protocol fees, two-way conversion costs, gas, low/base/high execution scenarios, and event-level break-even rates.
- Table 2 makes every parameter machine-readable and visible.

## 11. Collateral and liquidation risk

- Added USD-stablecoin, ETH, and BTC collateral; 150/175/200% initial ratios; a 150% threshold; 5/10/13% penalties; and 10/25/40/60% crypto shocks.
- Added healthy, near-liquidation, and liquidated status fields to the event-level stress outputs.
- Added illustrative scenario-weighted expected losses and risk-adjusted benefit, clearly labelled as conditional rather than predictive.
- Table 5 and Figure 8 report the complete stress grid and expected-loss sensitivity.

## 12. Protocol solvency and loss allocation

- Added a balance-sheet equation and a loss-transmission table.
- Addressed backing, reserves, borrowers, liquidity providers, lenders, token holders, treasury/governance backstops, peg exits, dynamic rates, oracle failures, bank-run behaviour, protocol purpose, and conditions of unsustainability.

## 13. Manuscript organisation

- Rebuilt the manuscript around Introduction; Related Work; System Model; Data and Empirical Design; Results; Protocol Solvency; Discussion; Limitations; and Conclusion.
- Rewrote the abstract after recalculation and included gross, net, and risk-adjusted numerical findings.

## 14. Figures

- Removed repetitive infographic-style visuals.
- Figure 1 is a concise system context; Figures 2–8 are FX paths, event-size distribution, annual activity, gross horizons, rate sensitivity, break-even rates, and liquidation/risk-adjusted results.
- Regenerated all PNGs at 300 dpi and synchronised their original filenames (`figure2.png` through `figure8.png`) into the manuscript.

## 15. Tables

- Table 1: dataset construction and description.
- Table 2: assumptions and parameters.
- Table 3: gross fixed-horizon results including events, total DAI, mean, median, SD, IQR, positive share, and weighted result.
- Table 4: net rate/fee results.
- Table 5: collateral stress and expected liquidation loss.
- Table 6: FX timing, observed-duration, and execution-cost robustness.
- Table 7: protocol risk transmission and loss bearer.

## 16. Related work and referencing

- Expanded and critically integrated peer-reviewed work on lending pools, Aave, Compound, liquidations, oracles, stablecoin regulation, governance concentration, international finance, and crypto-dollarisation.
- Preserved the requested manual `thebibliography` format; no BibTeX compilation is required.

## 17. LaTeX and formatting

- Removed raw editing artefacts and audited terminology, citations, references, equations, captions, numbering, units, and figure-file mappings.
- Corrected the journal class's abstract syntax so the first character and heading render properly.
- Added PDF title, authors, subject, and keyword metadata.

## 18. Reproducibility and integrity

- Added source provenance, checksums, extraction SQL, decoding, FX matching, all analysis stages, final figure/table generation, data/code availability statements, and sharing limitations.
- The 396+ MB event-level fixed-horizon result is regenerated locally and excluded from Git because it exceeds GitHub's normal limit; its inputs and generating code are public.

## 19. Required deliverables

- Editable LaTeX and validated PDF: `manuscript/`.
- Raw-data pointer/checksum and exact extraction: `data/raw_makerdao/`, `documentation/`.
- Cleaned data and original FX CSVs: `data/processed/`, `data/raw_fx/`.
- Complete code and one-command runner: `analysis/`, `run_all.sh`.
- Validation sheet: `documentation/RESULTS_VALIDATION.md`.
- High-resolution figures: `figures/`.
- Target-journal checklist: `documentation/TARGET_JOURNAL_CHECKLIST.md`.

## 20. Order and validation

The work followed the requested order: source/data audit, methodological reconstruction, manuscript rewrite, and technical/submission preparation. Remaining author-controlled submission items—author contributions, coauthor approval, article type, cover letter, and any AI disclosure—are marked explicitly in the journal checklist and are not invented.

