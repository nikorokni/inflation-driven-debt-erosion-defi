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
- `results/`: gross, net, break-even, robustness, collateral-status, expected-loss, assumption, and validation outputs; the large event-level file is regenerated locally.
- `figures/`: generated 300-dpi figures.
- `tables/`: machine-generated LaTeX table fragments.
- `manuscript/`: English LaTeX source with an embedded manual bibliography, class files, figures, and compiled PDF.
- `documentation/`: exact BigQuery SQL, source provenance, results-validation sheet, point-by-point revision record, and target-journal checklist.
- `data/raw_makerdao/README.md`: public raw-archive link, checksum, and download/verification instructions.

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

The generated file `results/event_level_fixed_horizon_results.csv` is intentionally excluded from Git because it exceeds GitHub's normal per-file limit. Running `run_all.sh` recreates it and then synchronises the regenerated figures into `manuscript/figures/`.

## Reproduce from the included processed sample

If the decoded processed files are already present and only the reported analysis needs to be regenerated, run:

```bash
python analysis/reproduce_analysis.py \
  --draws data/processed/makerdao_eth_a_draw_events_analysis.csv \
  --lifecycles data/processed/makerdao_eth_a_lifecycles.csv \
  --construction data/processed/sample_construction.csv \
  --ars-fx data/raw_fx/ars_usd_fred.csv \
  --try-fx data/raw_fx/try_usd_fred.csv \
  --output-dir results \
  --figure-dir figures \
  --latex-table-dir tables
cp figures/figure*.png manuscript/figures/
```

The equations, rounded manuscript anchors, and table/figure map are documented in `documentation/RESULTS_VALIDATION.md`.

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

## Public repository

<https://github.com/nikorokni/inflation-driven-debt-erosion-defi>
