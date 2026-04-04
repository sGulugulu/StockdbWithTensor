#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

.venv/bin/python code/data/fetch_baostock_data.py \
  --output-root code/data/formal/baostock \
  --start-date 2015-01-01 \
  --end-date 2026-04-04 \
  --indices hs300,sz50,zz500 \
  --skip-financials \
  --skip-reports

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot code/data/formal/baostock/index_memberships/hs300_snapshots.csv \
  --output code/data/formal/hs300_history.csv

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot code/data/formal/baostock/index_memberships/sz50_snapshots.csv \
  --output code/data/formal/sz50_history.csv

.venv/bin/python code/data/build_baostock_member_history.py \
  --snapshot code/data/formal/baostock/index_memberships/zz500_snapshots.csv \
  --output code/data/formal/zz500_history.csv

.venv/bin/python code/data/fetch_baostock_kline.py \
  --codes-file code/data/formal/baostock/metadata/selected_codes.csv \
  --output-path code/data/formal/baostock/kline_panel.csv \
  --start-date 2015-01-01 \
  --end-date 2026-04-04

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path code/data/formal/baostock/kline_panel.csv \
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv \
  --output-path code/data/formal/hs300_factor_panel.csv

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path code/data/formal/baostock/kline_panel.csv \
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv \
  --output-path code/data/formal/sz50_factor_panel.csv

.venv/bin/python code/data/build_formal_factor_panel.py \
  --kline-path code/data/formal/baostock/kline_panel.csv \
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv \
  --output-path code/data/formal/zz500_factor_panel.csv

.venv/bin/python code/data/fetch_baostock_data.py \
  --output-root code/data/formal/baostock \
  --start-date 2015-01-01 \
  --end-date 2026-04-04 \
  --indices hs300,sz50,zz500 \
  --skip-index-memberships \
  --skip-metadata
