from __future__ import annotations

import argparse
import csv
from pathlib import Path


def build_member_history(snapshot_path: Path, output_path: Path) -> None:
    with snapshot_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    grouped: dict[str, list[str]] = {}
    for row in rows:
        grouped.setdefault(row["code"], []).append(row["snapshot_date"])

    history_rows: list[dict[str, str]] = []
    for code, dates in grouped.items():
        ordered_dates = sorted(set(dates))
        history_rows.append(
            {
                "market_id": "cn_a",
                "universe_id": snapshot_path.stem.replace("_snapshots", "").upper(),
                "stock_code": code.replace("sh.", "").replace("sz.", "").replace("bj.", ""),
                "start_date": ordered_dates[0],
                "end_date": ordered_dates[-1],
            }
        )

    history_rows.sort(key=lambda row: (row["stock_code"], row["start_date"]))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["market_id", "universe_id", "stock_code", "start_date", "end_date"],
        )
        writer.writeheader()
        writer.writerows(history_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build membership history files from baostock index snapshots.")
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    build_member_history(args.snapshot, args.output)


if __name__ == "__main__":
    main()
