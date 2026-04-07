#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

YEAR="${1:?Usage: run_baostock_stage2_year.sh <year>}"
for dataset in \
  profit_data \
  operation_data \
  growth_data \
  balance_data \
  cash_flow_data \
  dupont_data \
  performance_express_report \
  forecast_report
do
  bash code/data/run_baostock_stage2_dataset_year.sh "$dataset" "$YEAR"
done
