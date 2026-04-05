from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.fetch_baostock_data import build_all_a_tradable_history_rows


def build_all_a_tradable_history(
    *,
    stock_basic_path: Path,
    output_path: Path,
    horizon_date: str,
) -> None:
    with stock_basic_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    history_rows = build_all_a_tradable_history_rows(rows, horizon_date=horizon_date)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["market_id", "universe_id", "stock_code", "start_date", "end_date"],
        )
        writer.writeheader()
        writer.writerows(history_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build tradable all-A-share universe history from stock_basic.csv.")
    parser.add_argument("--stock-basic-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--horizon-date", required=True)
    args = parser.parse_args()
    build_all_a_tradable_history(
        stock_basic_path=args.stock_basic_path,
        output_path=args.output_path,
        horizon_date=args.horizon_date,
    )


if __name__ == "__main__":
    main()
