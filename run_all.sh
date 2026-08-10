#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: bash run_all.sh /path/to/Data_July_2023.zip" >&2
  exit 2
fi

replication_root="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
raw_makerdao_archive="$1"

python "$replication_root/analysis/decode_makerdao.py" \
  "$raw_makerdao_archive" \
  "$replication_root/data/processed"

python "$replication_root/analysis/reproduce_analysis.py" \
  --draws "$replication_root/data/processed/makerdao_eth_a_draw_events_analysis.csv" \
  --lifecycles "$replication_root/data/processed/makerdao_eth_a_lifecycles.csv" \
  --construction "$replication_root/data/processed/sample_construction.csv" \
  --ars-fx "$replication_root/data/raw_fx/ars_usd_fred.csv" \
  --try-fx "$replication_root/data/raw_fx/try_usd_fred.csv" \
  --output-dir "$replication_root/results" \
  --figure-dir "$replication_root/figures" \
  --latex-table-dir "$replication_root/tables"

mkdir -p "$replication_root/manuscript/figures"
cp "$replication_root"/figures/figure*.png "$replication_root/manuscript/figures/"

echo "Reproduction complete. See results/validation_summary.json."
