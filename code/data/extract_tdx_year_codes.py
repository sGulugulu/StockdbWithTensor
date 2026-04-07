from __future__ import annotations

import argparse
import csv
from pathlib import Path


def extract_tdx_year_codes(*, input_path: Path, output_path: Path) -> int:
    codes: set[str] = set()
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            code = str(row.get("code", "")).strip().lower()
            if code:
                codes.add(code)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["code"])
        writer.writeheader()
        for code in sorted(codes):
            writer.writerow({"code": code})
    return len(codes)


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract one year's unique codes from TDX full master base CSV.")
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()

    count = extract_tdx_year_codes(input_path=args.input_path, output_path=args.output_path)
    print(f"extracted_codes={count}")


if __name__ == "__main__":
    main()
