from __future__ import annotations

import argparse
import csv
from pathlib import Path


def read_members(path: Path, symbol_column: str) -> set[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return {row[symbol_column].strip() for row in csv.DictReader(handle)}


def filter_daily_csv(
    *,
    raw_daily_path: Path,
    member_symbols: set[str],
    symbol_column: str,
    output_path: Path,
) -> None:
    with raw_daily_path.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src)
        rows = [row for row in reader if row[symbol_column].strip() in member_symbols]
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as dst:
            writer = csv.DictWriter(dst, fieldnames=reader.fieldnames or [])
            writer.writeheader()
            writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build index-specific daily CSV files from Tongdaxin exports.")
    parser.add_argument("--raw-daily", type=Path, required=True)
    parser.add_argument("--symbol-column", default="stock_code")
    parser.add_argument("--hs300-members", type=Path, required=True)
    parser.add_argument("--csi-a500-members", type=Path, required=True)
    parser.add_argument("--csi-a50-members", type=Path, required=True)
    parser.add_argument("--member-symbol-column", default="stock_code")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    filter_daily_csv(
        raw_daily_path=args.raw_daily,
        member_symbols=read_members(args.hs300_members, args.member_symbol_column),
        symbol_column=args.symbol_column,
        output_path=args.output_dir / "hs300_daily.csv",
    )
    filter_daily_csv(
        raw_daily_path=args.raw_daily,
        member_symbols=read_members(args.csi_a500_members, args.member_symbol_column),
        symbol_column=args.symbol_column,
        output_path=args.output_dir / "csi_a500_daily.csv",
    )
    filter_daily_csv(
        raw_daily_path=args.raw_daily,
        member_symbols=read_members(args.csi_a50_members, args.member_symbol_column),
        symbol_column=args.symbol_column,
        output_path=args.output_dir / "csi_a50_daily.csv",
    )


if __name__ == "__main__":
    main()
