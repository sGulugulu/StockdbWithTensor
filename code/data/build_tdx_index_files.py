from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_members(
    path: Path,
    symbol_column: str,
    start_column: str,
    end_column: str,
) -> list[tuple[str, str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            (
                row[symbol_column].strip(),
                row[start_column].strip(),
                row[end_column].strip(),
            )
            for row in csv.DictReader(handle)
        ]


def filter_daily_csv(
    *,
    raw_daily_path: Path,
    memberships: list[tuple[str, str, str]],
    symbol_column: str,
    date_column: str,
    output_path: Path,
) -> None:
    with raw_daily_path.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as dst:
            writer = csv.DictWriter(dst, fieldnames=reader.fieldnames or [])
            writer.writeheader()
            for row in reader:
                symbol = row[symbol_column].strip()
                trade_date = row[date_column].strip()
                if any(
                    member_symbol == symbol and start_date <= trade_date <= end_date
                    for member_symbol, start_date, end_date in memberships
                ):
                    writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build index-specific daily CSV files from Tongdaxin exports.")
    parser.add_argument("--raw-daily", type=Path, required=True)
    parser.add_argument("--symbol-column", default="stock_code")
    parser.add_argument("--date-column", default="trade_date")
    parser.add_argument("--hs300-members", type=Path, required=True)
    parser.add_argument("--csi-a500-members", type=Path, required=True)
    parser.add_argument("--csi-a50-members", type=Path, required=True)
    parser.add_argument("--member-symbol-column", default="stock_code")
    parser.add_argument("--member-start-column", default="start_date")
    parser.add_argument("--member-end-column", default="end_date")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    filter_daily_csv(
        raw_daily_path=args.raw_daily,
        memberships=read_members(
            args.hs300_members,
            args.member_symbol_column,
            args.member_start_column,
            args.member_end_column,
        ),
        symbol_column=args.symbol_column,
        date_column=args.date_column,
        output_path=args.output_dir / "hs300_daily.csv",
    )
    filter_daily_csv(
        raw_daily_path=args.raw_daily,
        memberships=read_members(
            args.csi_a500_members,
            args.member_symbol_column,
            args.member_start_column,
            args.member_end_column,
        ),
        symbol_column=args.symbol_column,
        date_column=args.date_column,
        output_path=args.output_dir / "csi_a500_daily.csv",
    )
    filter_daily_csv(
        raw_daily_path=args.raw_daily,
        memberships=read_members(
            args.csi_a50_members,
            args.member_symbol_column,
            args.member_start_column,
            args.member_end_column,
        ),
        symbol_column=args.symbol_column,
        date_column=args.date_column,
        output_path=args.output_dir / "csi_a50_daily.csv",
    )


if __name__ == "__main__":
    main()
