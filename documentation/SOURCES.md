# Data provenance and checksums

Access date for the original MakerDAO and OECD/FRED sources: **8 August 2026**. Daily BCRA and ECB archives downloaded **12 October 2026**.

## MakerDAO Vat trace archive

- Dataset paper: Yatipa Chaleenutthawut et al., "Loan Portfolio Dataset From MakerDAO Blockchain Project," *IEEE Access*, 12 (2024), 24843-24854. DOI: <https://doi.org/10.1109/ACCESS.2024.3363225>.
- Public repository: <https://github.com/Sudarut-kas/Data-Mining-for-MakerDAO>.
- Repository commit inspected: `fc3c10f1a56f351630ed2278c7f654ddaf09f149`.
- Public archive: <https://drive.google.com/file/d/1KJ551BYvw6vVx7pgHYkFPXU9Em0zkHuB/view>.
- Raw archive contents: one CSV (`Data_July_2023.csv`) containing 4,466,880 successful Vat call traces.
- Raw archive SHA-256: `85a43199a808c70575201e15cd367907e0dbc31d74869b47c15d37f312b80c23`.
- Exact SQL: `documentation/source_query.sql`.

No Dune Analytics query was used. The original manuscript requested a Dune ID, but the replacement dataset is the public BigQuery-derived archive associated with the peer-reviewed IEEE Access paper. This choice is recorded explicitly to avoid implying a nonexistent Dune provenance.

## MakerDAO contract interpretation

- Vat documentation (current official Sky Protocol docs, including urn ink/art, collateral rate and frob/grab): <https://developers.skyeco.com/protocol/core/vat/>. The earlier MakerDAO URL redirects to the Sky documentation as of 28 September 2026.
- Vat address used by the source query: `0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B`.
- `frob(bytes32,address,address,address,int256,int256)` selector: `0x76088703`.
- Event definition: ETH-A `frob` with positive signed `dart`.
- Actual DAI debt change: `dart * rate / 10^45`, reflecting WAD-normalised debt and RAY rate scaling.

## Foreign-exchange series

The fixed-horizon series are OECD monthly averages distributed by FRED. Both are national-currency units per US dollar. Selected observed durations instead use the separately archived daily official references below; daily-source arithmetic monthly means and original OECD/FRED monthly averages are compared for the *same selected spells*.

### Argentina

- Series ID: `ARGCCUSMA02STM`.
- Page: <https://fred.stlouisfed.org/series/ARGCCUSMA02STM>.
- Download: <https://fred.stlouisfed.org/graph/fredgraph.csv?id=ARGCCUSMA02STM>.
- Included file: `data/raw_fx/ars_usd_fred.csv`.
- SHA-256: `1dacf0b03e50660e0bbd819e3b73f6783576517a8d0cf9ac2559dbb92d0f455d`.
- Caveat: this is an official rate and may differ from executable parallel-market rates under exchange controls.

### Türkiye

- Series ID: `CCUSMA02TRM618N`.
- Page: <https://fred.stlouisfed.org/series/CCUSMA02TRM618N>.
- Download: <https://fred.stlouisfed.org/graph/fredgraph.csv?id=CCUSMA02TRM618N>.
- Included file: `data/raw_fx/try_usd_fred.csv`.
- SHA-256: `51d90a2eb45a989dcc078e04dacfcb06637026e90a3ead8d8290e8a61a32aad4`.

### Daily references for observed durations

- ARS per USD: Banco Central de la República Argentina, Communication A3500 wholesale reference, <https://www.bcra.gob.ar/archivos/Pdfs/PublicacionesEstadisticas/com3500.xls>. Archived workbook: `data/raw_fx/bcra_com3500.xls`; SHA-256 `966df64998ecb3ca4a41625b43293bf2057a7b88a954f2bedfa95e409638e712`. The code reads sheet `TCR diario y TCNPM`, date column C and numeric ARS/USD column D.
- TRY per USD: European Central Bank euro foreign exchange daily reference archive, <https://www.ecb.europa.eu/stats/eurofxref/eurofxref-hist.zip>. Archived ZIP: `data/raw_fx/ecb_eurofxref_hist.zip`; SHA-256 `f36e0affc225bc572cc589d4183352c5815f178769f04c2b27a452567c6f7649`. The code reads `eurofxref-hist.csv` and divides TRY per EUR by USD per EUR on each published date.
- Both sources are reference marks, not guaranteed prices available to a borrower at the transaction time. BCRA is an official wholesale series; the ECB discourages transaction use of its published references. No validated executable or parallel-market ARS observations are available here.
- The code retains dates from December 2019 through August 2023, normalizes and sorts rates, checks duplicate dates and positivity, and writes `results/fx_daily_reference.csv`; SHA-256 `9e603bbd4883fd1935f15ec313e58e4f1c2d3a769600ed59c01c7c2ac92ea673` with the pinned versions in `requirements.txt`. The archived raw files are the reproduction inputs, so newer upstream data cannot silently change these estimates.

## Missing values and horizon matching

FX dates are converted to monthly periods. Each debt-draw month is matched to the corresponding month and to month plus 3, 6, 12, or 24. Eligible observations require both endpoints. No endpoint interpolation is performed. The adjacent-month robustness check uses the highest of the three start-window rates and the lowest of the three end-window rates, which is adverse to the borrower under the stated units.

For the restricted observed-duration sample, only spells with both original monthly endpoints are retained (7,105 per currency). The code matches each UTC start/end *calendar date* to the most recent published daily reference date on or before it; weekends and holidays use the last published date. This is an ex-post mark and does not establish that a same-date reference had already been published at the transaction timestamp. No future-date quote or linear interpolation is allowed. The same-source monthly comparison averages daily observations within each month and applies them to the exact same spells. Borrowing rate, fee, conversion cost and gas are unchanged across alternatives. See `analysis/daily_fx.py`, `analysis/reproduce_analysis.py` and `results/observed_fx_frequency_comparison.csv`.
