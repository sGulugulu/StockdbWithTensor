#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

YEAR="${1:?Usage: run_baostock_stage3_year.sh <year>}"

if [[ "$YEAR" == "2026" ]]; then
  YEAR_END="2026-04-01"
else
  YEAR_END="${YEAR}-12-31"
fi

.venv/bin/python code/data/fetch_baostock_kline.py \
  --codes-file code/data/formal/baostock/metadata/all_a_codes.csv \
  --output-path code/data/formal/master/shared_kline_panel.csv \
  --progress-path "code/data/formal/master/shared_kline_panel_${YEAR}.progress.json" \
  --start-date "${YEAR}-01-01" \
  --end-date "$YEAR_END" \
  --adjustflag 2
