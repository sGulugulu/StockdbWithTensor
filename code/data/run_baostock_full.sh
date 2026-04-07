#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

END_DATE="${1:-2026-04-01}"
FORMAL_ROOT="code/data/formal"
BAOSTOCK_ROOT="$FORMAL_ROOT/baostock"
SHARED_MASTER_PATH="$FORMAL_ROOT/master/shared_kline_panel.csv"
SHARED_MASTER_PROGRESS="$FORMAL_ROOT/master/shared_kline_panel.progress.json"
FRESH_RUN="${BAOSTOCK_FULL_FRESH_RUN:-1}"

if [[ "$FRESH_RUN" == "1" ]]; then
  rm -f "$SHARED_MASTER_PATH" "$SHARED_MASTER_PROGRESS"
fi

.venv/bin/python code/data/fetch_baostock_data.py \
  --output-root "$BAOSTOCK_ROOT" \
  --start-date 2015-01-01 \
  --end-date "$END_DATE" \
  --indices hs300,sz50,zz500 \
  --metadata-scope all_a \
  --all-a-history-output "$FORMAL_ROOT/universes/all_a_tradable_history.csv" \
  --skip-financials \
  --skip-reports

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot "$BAOSTOCK_ROOT/index_memberships/hs300_snapshots.csv" \
  --output "$FORMAL_ROOT/universes/hs300_history.csv" \
  --horizon-date "$END_DATE"

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot "$BAOSTOCK_ROOT/index_memberships/sz50_snapshots.csv" \
  --output "$FORMAL_ROOT/universes/sz50_history.csv" \
  --horizon-date "$END_DATE"

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot "$BAOSTOCK_ROOT/index_memberships/zz500_snapshots.csv" \
  --output "$FORMAL_ROOT/universes/zz500_history.csv" \
  --horizon-date "$END_DATE"

.venv/bin/python code/data/fetch_baostock_kline.py \
  --codes-file "$BAOSTOCK_ROOT/metadata/all_a_codes.csv" \
  --output-path "$SHARED_MASTER_PATH" \
  --start-date 2015-01-01 \
  --end-date "$END_DATE" \
  --adjustflag 2 \
  --progress-path "$SHARED_MASTER_PROGRESS" \
  --partition-by-year

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path "$SHARED_MASTER_PATH" \
  --industry-path "$BAOSTOCK_ROOT/metadata/stock_industry.csv" \
  --membership-path "$FORMAL_ROOT/universes/hs300_history.csv" \
  --output-path "$FORMAL_ROOT/factors/hs300_factor_panel.csv"

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path "$SHARED_MASTER_PATH" \
  --industry-path "$BAOSTOCK_ROOT/metadata/stock_industry.csv" \
  --membership-path "$FORMAL_ROOT/universes/sz50_history.csv" \
  --output-path "$FORMAL_ROOT/factors/sz50_factor_panel.csv"

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path "$SHARED_MASTER_PATH" \
  --industry-path "$BAOSTOCK_ROOT/metadata/stock_industry.csv" \
  --membership-path "$FORMAL_ROOT/universes/zz500_history.csv" \
  --output-path "$FORMAL_ROOT/factors/zz500_factor_panel.csv"

.venv/bin/python code/data/fetch_baostock_data.py \
  --output-root "$BAOSTOCK_ROOT" \
  --start-date 2015-01-01 \
  --end-date "$END_DATE" \
  --indices hs300,sz50,zz500 \
  --stage2-scope all_a \
  --skip-index-memberships \
  --skip-metadata

.venv/bin/python code/data/convert_formal_csv_to_parquet.py \
  --formal-root "$FORMAL_ROOT" \
  --overwrite

.venv/bin/python code/data/refresh_formal_baostock_manifest.py
