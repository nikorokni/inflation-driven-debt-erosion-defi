# MakerDAO raw-trace archive

The analysis starts from the public archive accompanying Chaleenutthawut et al. (2024), *Loan Portfolio Dataset From MakerDAO Blockchain Project*, IEEE Access 12, 24843–24854, DOI: <https://doi.org/10.1109/ACCESS.2024.3363225>.

- Source repository: <https://github.com/Sudarut-kas/Data-Mining-for-MakerDAO>
- Public archive: <https://drive.google.com/file/d/1KJ551BYvw6vVx7pgHYkFPXU9Em0zkHuB/view>
- Expected filename: `Data_July_2023.zip`
- Expected SHA-256: `85a43199a808c70575201e15cd367907e0dbc31d74869b47c15d37f312b80c23`
- Uncompressed content: `Data_July_2023.csv`, containing 4,466,880 successful calls to MakerDAO's Vat contract.

The archive is not duplicated in this GitHub repository because it exceeds GitHub's normal per-file size limit. This pointer, checksum, exact source query, decoder, and processed outputs make the extraction auditable without implying that the raw archive is hosted here.

## Verify and reproduce

After downloading the archive, run:

```bash
sha256sum Data_July_2023.zip
```

The printed digest must exactly equal the value above. Then, from the repository root, run:

```bash
python -m pip install -r requirements.txt
bash run_all.sh /absolute/path/to/Data_July_2023.zip
```

The source's exact BigQuery extraction is preserved in `documentation/source_query.sql`. No Dune Analytics query or Dune query ID was used in the corrected analysis.

