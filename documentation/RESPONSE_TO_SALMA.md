---
title: "Response to the major-revision comments"
author: "Niko Rokni Lamouki, corresponding author"
date: "28 September 2026"
geometry: margin=23mm
fontsize: 10pt
---

Dear Salma,

I am sending you my point-by-point revision record. I rebuilt the borrower accounting before revising the conclusions. I have removed the previously reported scenario-weighted risk-adjusted medians: the earlier calculation combined final-horizon repayment with a liquidation penalty, and terminal shock assumptions cannot identify an actual liquidation path. I reran the empirical analysis using the archived MakerDAO event and lifecycle files and the included official FX series. The revised manuscript, executable code, generated results and model note are in the accompanying package.

## Principal comment: repayment and liquidation are different outcomes

**Response.** I agree. Section 3 now specifies mutually exclusive branches. A voluntarily repaid position pays accrued LCU debt converted at its closing FX rate, exit conversion cost and closing gas; the collateral returns to the borrower. For a liquidated position at time $\tau$, marked collateral is sold, proceeds recover at most accrued debt, a penalty is collected only from surplus, and any residual is returned. The borrower does not also repay at the intended horizon. Any unrecovered claim impairs the issuer/lender asset under the explicit nonrecourse convention. The branch is implemented in analysis/borrower_cashflows.py and tested against independent numerical examples in tests/test_borrower_cashflows.py. With no defensible within-horizon collateral and auction path, I do not aggregate these branches into an expected borrower benefit.

## 1. Title and measured concept

**Response.** I changed the title to *FX-Driven Debt Erosion in Local-Currency DeFi Lending: Counterfactual Evidence from MakerDAO ETH-A Draws*. The introduction now distinguishes depreciation against USD from consumer-price inflation. I also updated the keywords and PDF metadata.

## 2. Hypothetical horizons and observed durations

**Response.** The abstract, results and conclusion now lead with the restricted clean-lifecycle check. There are 7,105 selected clean repaid spells with FX coverage per currency; the median observed duration is 6.95 days. At the illustrative 20% effective annual rate and specified costs, hypothetical median net benefits over those observed durations are -3.00% (ARS) and -4.14% (TRY). I explicitly call the positive 12- and 24-month figures imposed holding-period scenarios, not actual LCU loans or typical MakerDAO durations. The clean subset is selected and monthly FX cannot capture within-month moves; the duration-band table and figure make that clear.

## 3. Dependence within urns

**Response.** I no longer treat event mappings as independent borrowers. The sample has 16,846 urn identifiers and 130,742 draws. Only 6,221 urns have one eligible draw; 2,713 have more than ten, representing 70.29% of all events. I report the chronologically first eligible draw per urn and amount-aggregated urn summaries alongside all-event results. For TRY, the 12-month event median of 6.59% becomes -4.54% for first draws and -0.43% for urn-aggregate medians. The full draw counts and per-urn amounts are machine-readable. An urn is not a verified person, and I make no independence-based confidence-interval claim.

## 4. Amount-weighted concentration

**Response.** I rank events by original principal, without selecting on the outcome. In the illustrative 12-month base case, the largest 1% account for 64.52% of principal and 72.49% (ARS) or 66.85% (TRY) of the *signed* aggregate net-benefit numerator. I also report 5% and 10% shares. Monthly contribution files and a figure show origination-time concentration; October 2021 contributes 13.39% of the ARS signed total, and May 2021 contributes 15.21% of the TRY total. Denominators and potentially negative month contributions are explained. Large positions are not assumed to trade without market impact.

## 5. Minimum economically meaningful draw sizes

**Response.** I reran both the 12-month and clean-duration mappings with minimum draw sizes of USD 1, 100, 1,000, 5,000 and 10,000. The manuscript table gives counts, medians and weighted results; results/position_size_sensitivity.csv adds means and positive shares. At the USD 1 floor, unweighted 12-month means are -11.85% and -6.58%; above USD 100 they are 5.82% and 12.74%. Fixed gas causes the extreme tiny-position percentages. Even above USD 10,000, clean-duration median net effects remain negative (-1.24% and -1.27%).

## 6. Collateral assumptions and shock probabilities

**Response.** I chose the narrower alternative you suggested. Section 3 defines a *terminal collateral-ratio screen* using generic deterministic percentage declines. Results are only the share of event mappings whose month-12 mark is below an assumed threshold, not a probability of liquidation or an executed sale. I removed ETH/BTC labels from identical-shock results, removed arbitrary 40/30/20/10 scenario weights and the expected-loss output, and withdrew the old risk-adjusted claims. Asset-specific paths, supported probabilities, oracle timing and auction settlement would be needed to calculate expected outcomes. The conditional liquidation ledger is provided without pretending terminal marks identify its event time.

## 7. Fees, rate, conversion and gas

**Response.** The revised effective annual LCU rate compounds as $(1+r)^t$. A 0.5% protocol fee is paid externally in USD at opening and is not added to financed debt. A stipulated 0.3% conversion cost applies at the opening swap and, for voluntary repayment only, on reacquiring LCU at closing. The USD 40 gas budget is USD 20 at opening and USD 20 at *voluntary* closure. A liquidated borrower bears opening gas but not voluntary closing gas or an exit swap; any auction haircut and capped penalty are separate. These are assumptions, not measured gas transactions or executable FX quotes. Changing the fee timing slightly changes the baseline results; every number was regenerated.

## 8. Official versus executable ARS

**Response.** All ARS estimates are now explicitly limited to an *official-rate counterfactual*. If an executable rate is the official rate multiplied by an unknown premium $w_t$, the executable gross expression becomes $1-(w_0/w_h)(E_0^{official}/E_h^{official})$. A change in that premium can even reverse the sign. I have not substituted an unverified parallel-rate history. An adjacent-month FX check does not resolve official-versus-executable access. A separately sourced and audited parallel-market series would be needed.

## 9. Balance sheet and loss absorption

**Response.** Section 6 replaces the previous equation with a restricted equity identity for performing loan claims, cash from *settled* collateral recovery, unrestricted reserves, redeemable token liabilities and other funding obligations. Borrower-posted collateral is encumbered, not extra unrestricted issuer capital. A shortfall between accrued debt and sale recovery writes down a loan asset; it is not another liability. I state that token burn, liability settlement and reserve/equity effects require a complete issuer ledger. No solvency estimate follows without observed LCU liabilities and issuer reserves.

## 10. Empirical results versus design ideas

**Response.** I distinguish observed draw sizes and selected durations, official FX observations, hypothetical repayment outcomes, deterministic terminal screens and untested system recommendations. Rate rules, diverse auction participants, oracle fallbacks and reserves are design questions for later work. This study does not estimate peg stability, reserve adequacy, auction performance or protocol solvency.

## 11. Abstract and conclusion after correcting the model

**Response.** I rewrote both after regenerating results. They lead with the 6.95-day selected duration, negative clean-duration hypothetical medians and the counterfactual status of longer horizons. The old risk-adjusted medians are absent from the abstract, results tables and conclusion. I report the terminal threshold diagnostic without treating it as an expected borrower return.

## 12. Formatting and numerical consistency

**Response.** I rebuilt the PDF with larger figures, readable tables with stated denominators, consistent terminology and two-decimal rounding. Six results tables are generated from CSV outputs; the sample-construction and cost-assumption tables refer to tracked input records. I retained the supported background and methods material, with an expanded explanation of what the counterfactuals identify. A validation sheet maps every headline number to its machine-readable source. I rendered the pages to inspect clipping and page balance, checked equation rendering and verified the displayed values against the generated CSVs.

I have retained the boundaries that the data cannot resolve: no observed ARS/TRY vault, verified executable ARS parallel-rate series, within-horizon collateral path or complete issuer balance sheet. I hope the revision makes both the corrected findings and those limits clear.

Sincerely,

Niko Rokni Lamouki
Corresponding author
