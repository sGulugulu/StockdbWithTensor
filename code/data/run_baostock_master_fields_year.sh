#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

YEAR="${1:?Usage: run_baostock_master_fields_year.sh <year> [max_parallel_months]}"
MAX_PARALLEL_MONTHS="${2:-2}"

FIELDS="date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST"
BASE_DIR="code/data/formal/master/baostock_fields/${YEAR}"
YEAR_OUT="code/data/formal/master/baostock_fields/${YEAR}.csv"
TDX_BASE_PATH="code/data/formal/master/tdx_full_master_base_${YEAR}.csv"
CODES_FILE="${BASE_DIR}/_codes_${YEAR}.csv"

mkdir -p "$BASE_DIR"

if [[ -f "$TDX_BASE_PATH" ]]; then
  .venv/bin/python code/data/extract_tdx_year_codes.py \
    --input-path "$TDX_BASE_PATH" \
    --output-path "$CODES_FILE"
else
  cp code/data/formal/baostock/metadata/all_a_codes.csv "$CODES_FILE"
fi

.venv/bin/python - "$YEAR" "$BASE_DIR" <<'PY' > "${BASE_DIR}/_monthly_plan.txt"
from pathlib import Path
import sys
sys.path.insert(0, "code")
from data.year_windows import iter_month_date_ranges
year = int(sys.argv[1])
base = Path(sys.argv[2])
start = f"{year}-01-01"
end = "2026-04-01" if year == 2026 else f"{year}-12-31"
for window_start, window_end, _, month in iter_month_date_ranges(start, end):
    month_file = base / f"{year}-{month:02d}.csv"
    progress_file = base / f"{year}-{month:02d}.progress.json"
    print(f"{window_start}|{window_end}|{month_file.as_posix()}|{progress_file.as_posix()}")
PY

running=0
while IFS='|' read -r WINDOW_START WINDOW_END MONTH_FILE PROGRESS_FILE; do
  (
    .venv/bin/python code/data/fetch_baostock_kline.py \
      --codes-file "$CODES_FILE" \
      --output-path "$MONTH_FILE" \
      --progress-path "$PROGRESS_FILE" \
      --start-date "$WINDOW_START" \
      --end-date "$WINDOW_END" \
      --fields "$FIELDS" \
      --adjustflag 2
  ) &
  running=$((running + 1))
  if [[ "$running" -ge "$MAX_PARALLEL_MONTHS" ]]; then
    wait -n
    running=$((running - 1))
  fi
done < "${BASE_DIR}/_monthly_plan.txt"

wait

MONTH_FILES=$(awk -F'|' '{print $3}' "${BASE_DIR}/_monthly_plan.txt")
.venv/bin/python code/data/merge_partitioned_csv.py \
  --inputs ${MONTH_FILES} \
  --output-path "$YEAR_OUT" \
  --sort-keys date,code
