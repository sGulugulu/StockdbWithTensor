#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

.venv/bin/python code/data/convert_formal_csv_to_parquet.py \
  --formal-root code/data/formal \
  --overwrite

.venv/bin/python code/data/refresh_formal_baostock_manifest.py
