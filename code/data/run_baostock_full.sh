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

.venv/bin/python code/data/fetch_baostock_data.py \
  --output-root code/data/formal/baostock \
  --start-date 2015-01-01 \
  --end-date 2026-04-04 \
  --indices hs300,sz50,zz500 \
  --skip-index-memberships \
  --skip-metadata
