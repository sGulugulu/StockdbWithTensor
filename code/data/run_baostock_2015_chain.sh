#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

LOG_DIR="code/outputs/logs"
mkdir -p "$LOG_DIR"

STAGE2_PID_FILE="$LOG_DIR/stage2_2015.pid"
STAGE2_LOG="$LOG_DIR/stage2_2015.log"

if [[ ! -f "$STAGE2_PID_FILE" ]]; then
  echo "[stage2015-chain] Missing PID file: $STAGE2_PID_FILE" >&2
  exit 1
fi

STAGE2_PID="$(cat "$STAGE2_PID_FILE")"
while ps -p "$STAGE2_PID" >/dev/null 2>&1; do
  sleep 30
done

if ! grep -q "Fetched baostock bundle:" "$STAGE2_LOG"; then
  echo "[stage2015-chain] Stage 2 2015 did not finish successfully; aborting follow-up." >&2
  exit 1
fi

bash code/data/run_baostock_stage3_year.sh 2015
bash code/data/run_baostock_stage4.sh
