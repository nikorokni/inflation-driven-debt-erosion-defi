# Data provenance and checksums

Access date for all online sources: **8 August 2026**.

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

- Vat documentation: <https://docs.makerdao.com/smart-contract-modules/core-module/vat-detailed-documentation>.
- Vat address used by the source query: `0x35D1b3F3D7966A1DFe207aa4514C12a259A0492B`.
- `frob(bytes32,address,address,address,int256,int256)` selector: `0x76088703`.
- Event definition: ETH-A `frob` with positive signed `dart`.
- Actual DAI debt change: `dart * rate / 10^45`, reflecting WAD-normalised debt and RAY rate scaling.

## Foreign-exchange series

The series are official monthly averages from OECD Main Economic Indicators, distributed by FRED. Both are national-currency units per US dollar.

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

## Missing values and horizon matching

FX dates are converted to monthly periods. Each debt-draw month is matched to the corresponding month and to month plus 3, 6, 12, or 24. Eligible observations require both endpoints. No endpoint interpolation is performed. The adjacent-month robustness check uses the highest of the three start-window rates and the lowest of the three end-window rates, which is adverse to the borrower under the stated units.

