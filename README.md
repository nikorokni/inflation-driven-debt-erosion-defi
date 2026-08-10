# Replication package

This package reproduces the empirical analysis in:

> *Inflation-Driven Debt Erosion in Local-Currency DeFi Lending: Counterfactual Evidence from MakerDAO ETH-A Borrowing Activity*

The paper is in `manuscript/main.tex`; the compiled version is `manuscript/main.pdf`.

## What is observed and what is counterfactual

- Observed: public successful MakerDAO Vat call traces, decoded ETH-A debt-draw timing and size, and official monthly ARS/USD and TRY/USD series.
- Counterfactual: the same event amounts are treated as if the liability were denominated in ARS or TRY rather than DAI.
- Not claimed: realised borrower profit, an implemented local-currency protocol, or representative user behaviour.

## Folder guide

- `analysis/`: event decoder and analysis/figure script.
- `data/raw_fx/`: original FRED CSV downloads.
- `data/processed/`: decoded analysis sample, lifecycle data, construction log, and metadata.
- `results/`: event-level and summary outputs.
- `figures/`: generated 300-dpi figures.
- `tables/`: machine-generated LaTeX table fragments.
- `manuscript/`: English LaTeX source, bibliography, class files, figures, and compiled PDF.
- `documentation/`: exact BigQuery SQL, source provenance, and revision record.

## Environment

Python 3.11 or later is recommended. Install dependencies with:

```bash
python -m pip install -r requirements.txt
```

## Reproduce from the public raw archive

Download the raw MakerDAO archive listed in `documentation/SOURCES.md`, then run:

```bash
bash run_all.sh /path/to/Data_July_2023.zip
```

The script uses the two FX CSV files already included in `data/raw_fx/`, rebuilds `data/processed/`, and regenerates `results/`, `tables/`, and `figures/`.

## Main operational definitions

- Borrowing event: a successful ETH-A `Vat.frob` call with positive signed `dart`.
- Amount: normalised debt change multiplied by the accumulated collateral-type `rate`.
- Vault identifier: MakerDAO `urn`; it is not treated as a verified person.
- Analysis window: 1 January 2020 through 31 July 2023.
- Minimum event size: 1 DAI.
- Fixed counterfactual horizons: 3, 6, 12, and 24 months.

The raw archive query omits top-level calls (`trace_address IS NOT NULL`). Therefore, observed-duration results use only internally consistent, single-draw, single-repayment lifecycles and are labelled as a restricted robustness check.

## Validation anchors

- Raw successful Vat traces: 4,466,880.
- Final ETH-A debt-draw events: 130,742.
- Unique urn identifiers: 16,846.
- Total DAI drawn: 13,318,097,854.94.
- Twelve-month median gross benefit: 24.61% (ARS), 25.30% (TRY).
- Twelve-month median net benefit at the base 20% annual rate: 2.78% (ARS), 6.71% (TRY).

The source checksums are in `documentation/SOURCES.md`.

