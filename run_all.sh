#!/usr/bin/env bash
set -euo pipefail
replication_root="$(cd "$(dirname "$0")" && pwd)"

if [[ $# -gt 1 ]]; then
  echo "Usage: bash run_all.sh [path/to/Data_July_2023.zip]" >&2
  exit 2
fi
if [[ $# -eq 1 ]]; then
  python "$replication_root/analysis/decode_makerdao.py" "$1" "$replication_root/data/processed"
fi

python "$replication_root/tests/test_borrower_cashflows.py"
python "$replication_root/analysis/reproduce_analysis.py"

if command -v latexmk >/dev/null 2>&1; then
  (cd "$replication_root/manuscript" && latexmk -pdf -interaction=nonstopmode -halt-on-error main.tex)
  (cd "$replication_root/documentation" && latexmk -pdf -interaction=nonstopmode -halt-on-error BORROWER_CASHFLOW_MODEL.tex)
fi
if command -v pandoc >/dev/null 2>&1 && command -v xelatex >/dev/null 2>&1; then
  (cd "$replication_root/documentation" && pandoc RESPONSE_TO_SALMA.md --pdf-engine=xelatex -V papersize=a4 -o RESPONSE_TO_SALMA.pdf)
fi
echo "Updated machine-readable results, tables, figures and available PDFs."
