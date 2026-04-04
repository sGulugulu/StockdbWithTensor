#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

END_DATE="${1:-$(date +%F)}"

.venv/bin/python code/data/fetch_baostock_data.py \
  --output-root code/data/formal/baostock \
  --start-date 2015-01-01 \
  --end-date "$END_DATE" \
  --indices hs300,sz50,zz500 \
  --skip-financials \
  --skip-reports

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot code/data/formal/baostock/index_memberships/hs300_snapshots.csv \
  --output code/data/formal/hs300_history.csv \
  --horizon-date "$END_DATE"

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot code/data/formal/baostock/index_memberships/sz50_snapshots.csv \
  --output code/data/formal/sz50_history.csv \
  --horizon-date "$END_DATE"

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot code/data/formal/baostock/index_memberships/zz500_snapshots.csv \
  --output code/data/formal/zz500_history.csv \
  --horizon-date "$END_DATE"

.venv/bin/python code/data/fetch_baostock_kline.py \
  --codes-file code/data/formal/baostock/metadata/selected_codes.csv \
  --output-path code/data/formal/baostock/kline_panel.csv \
  --start-date 2015-01-01 \
  --end-date "$END_DATE" \
  --adjustflag 2

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path code/data/formal/baostock/kline_panel.csv \
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv \
  --membership-path code/data/formal/hs300_history.csv \
  --output-path code/data/formal/hs300_factor_panel.csv

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path code/data/formal/baostock/kline_panel.csv \
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv \
  --membership-path code/data/formal/sz50_history.csv \
  --output-path code/data/formal/sz50_factor_panel.csv

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path code/data/formal/baostock/kline_panel.csv \
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv \
  --membership-path code/data/formal/zz500_history.csv \
  --output-path code/data/formal/zz500_factor_panel.csv

.venv/bin/python code/data/fetch_baostock_data.py \
  --output-root code/data/formal/baostock \
  --start-date 2015-01-01 \
  --end-date "$END_DATE" \
  --indices hs300,sz50,zz500 \
  --skip-index-memberships \
  --skip-metadata

.venv/bin/python code/data/refresh_formal_baostock_manifest.py
