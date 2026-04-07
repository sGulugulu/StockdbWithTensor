from __future__ import annotations

import argparse
import csv
from pathlib import Path


def build_tdx_year_slice(
    *,
    input_path: Path,
    output_path: Path,
    year: int,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with input_path.open("r", encoding="utf-8-sig", newline="") as src:
        reader = csv.DictReader(src)
        fieldnames = reader.fieldnames or []
        rows = [row for row in reader if row.get("trade_date", "").startswith(f"{year}-")]
    with output_path.open("w", encoding="utf-8", newline="") as dst:
        writer = csv.DictWriter(dst, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)
        else:
            dst.write("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract one calendar year from a TDX raw daily CSV.")
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--year", type=int, required=True)
    args = parser.parse_args()
    build_tdx_year_slice(
        input_path=args.input_path,
        output_path=args.output_path,
        year=args.year,
    )


if __name__ == "__main__":
    main()
