#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

FINANCIAL_DATASETS="profit_data,operation_data,growth_data,balance_data,cash_flow_data,dupont_data"
REPORT_DATASETS="performance_express_report,forecast_report"

if [[ $# -eq 1 ]]; then
  YEAR="${1:?Usage: run_baostock_stage2_dataset_year.sh <year> OR <dataset> <year>}"
  .venv/bin/python - "$YEAR" <<'PY'
import csv
import json
import sys
from pathlib import Path

year = sys.argv[1]
root = Path("code/data/formal/baostock")
year_start = f"{year}-01-01"
year_end = "2026-04-01" if year == "2026" else f"{year}-12-31"
all_a_history_path = Path("code/data/formal/universes/all_a_tradable_history.csv")
if not all_a_history_path.exists():
    raise SystemExit(f"Missing all_a_tradable_history.csv: {all_a_history_path}")

expected_codes = set()
with all_a_history_path.open("r", encoding="utf-8-sig", newline="") as handle:
    for row in csv.DictReader(handle):
        start_date = row.get("start_date", "")
        end_date = row.get("end_date", "")
        stock_code = row.get("stock_code", "")
        if stock_code and start_date <= year_end and end_date >= year_start:
            expected_codes.add(stock_code)
total_codes = len(expected_codes)

financial_progress = root / "financial" / "_progress.json"
reports_progress = root / "reports" / "_progress.json"
financial_payload = json.loads(financial_progress.read_text(encoding="utf-8")) if financial_progress.exists() else {}
reports_payload = json.loads(reports_progress.read_text(encoding="utf-8")) if reports_progress.exists() else {}

financial_datasets = ["profit_data", "operation_data", "growth_data", "balance_data", "cash_flow_data", "dupont_data"]
report_datasets = ["performance_express_report", "forecast_report"]

def row_count(path: Path):
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))

print(f"year={year}")
print(f"total_codes={total_codes}")
print("")
print("[financial]")
for dataset in financial_datasets:
    output_path = root / "financial" / dataset / f"{year}.csv"
    completed_units = {
        item for item in financial_payload.get(dataset, [])
        if item.endswith(f"|{year}")
    }
    completed_codes = {item.split("|", 1)[0] for item in completed_units}
    rows = row_count(output_path)
    status = "COMPLETE" if len(completed_codes) == total_codes else "INCOMPLETE"
    if len(completed_codes) == total_codes and rows in (None, 0):
        status = "COMPLETE_NO_ROWS"
    print(
        f"{dataset}: status={status} completed_codes={len(completed_codes)}/{total_codes} "
        f"file_exists={output_path.exists()} rows={rows}"
    )

print("")
print("[reports]")
for dataset in report_datasets:
    output_path = root / "reports" / dataset / f"{year}.csv"
    completed_units = {
        item for item in reports_payload.get(dataset, [])
        if item.endswith(f"|{year}")
    }
    completed_codes = {item.split("|", 1)[0] for item in completed_units}
    rows = row_count(output_path)
    status = "COMPLETE" if len(completed_codes) == total_codes else "INCOMPLETE"
    if len(completed_codes) == total_codes and rows in (None, 0):
        status = "COMPLETE_NO_ROWS"
    print(
        f"{dataset}: status={status} completed_codes={len(completed_codes)}/{total_codes} "
        f"file_exists={output_path.exists()} rows={rows}"
    )
PY
  exit 0
fi

DATASET="${1:?Usage: run_baostock_stage2_dataset_year.sh <year> OR <dataset> <year>}"
YEAR="${2:?Usage: run_baostock_stage2_dataset_year.sh <year> OR <dataset> <year>}"

if [[ "$YEAR" == "2026" ]]; then
  YEAR_END="2026-04-01"
else
  YEAR_END="${YEAR}-12-31"
fi

if [[ ",$FINANCIAL_DATASETS," == *",$DATASET,"* ]]; then
  .venv/bin/python code/data/fetch_baostock_data.py \
    --output-root code/data/formal/baostock \
    --start-date "${YEAR}-01-01" \
    --end-date "$YEAR_END" \
    --financial-start-year "$YEAR" \
    --financial-end-year "$YEAR" \
    --indices hs300,sz50,zz500 \
    --stage2-scope all_a \
    --financial-datasets "$DATASET" \
    --skip-index-memberships \
    --skip-metadata \
    --skip-reports
  exit 0
fi

if [[ ",$REPORT_DATASETS," == *",$DATASET,"* ]]; then
  .venv/bin/python code/data/fetch_baostock_data.py \
    --output-root code/data/formal/baostock \
    --start-date "${YEAR}-01-01" \
    --end-date "$YEAR_END" \
    --indices hs300,sz50,zz500 \
    --stage2-scope all_a \
    --report-datasets "$DATASET" \
    --skip-index-memberships \
    --skip-metadata \
    --skip-financials
  exit 0
fi

echo "Unsupported dataset: $DATASET" >&2
exit 1
