from __future__ import annotations

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path


def _to_date(value: str) -> date:
    return date.fromisoformat(value)


def _to_iso(value: date) -> str:
    return value.isoformat()


def build_member_history(snapshot_path: Path, output_path: Path) -> None:
    with snapshot_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    snapshots_by_date: dict[str, set[str]] = {}
    for row in rows:
        snapshots_by_date.setdefault(row["snapshot_date"], set()).add(row["code"])

    ordered_dates = sorted(snapshots_by_date)
    history_rows: list[dict[str, str]] = []
    open_intervals: dict[str, str] = {}
    universe_id = snapshot_path.stem.replace("_snapshots", "").upper()

    for index, snapshot_date in enumerate(ordered_dates):
        current_codes = snapshots_by_date[snapshot_date]

        for code in sorted(current_codes):
            open_intervals.setdefault(code, snapshot_date)

        closing_codes = [code for code in list(open_intervals) if code not in current_codes]
        for code in closing_codes:
            history_rows.append(
                {
                    "market_id": "cn_a",
                    "universe_id": universe_id,
                    "stock_code": code.replace("sh.", "").replace("sz.", "").replace("bj.", ""),
                    "start_date": open_intervals.pop(code),
                    "end_date": _to_iso(_to_date(snapshot_date) - timedelta(days=1)),
                }
            )

        if index == len(ordered_dates) - 1:
            for code, start_date in open_intervals.items():
                history_rows.append(
                    {
                        "market_id": "cn_a",
                        "universe_id": universe_id,
                        "stock_code": code.replace("sh.", "").replace("sz.", "").replace("bj.", ""),
                        "start_date": start_date,
                        "end_date": snapshot_date,
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
