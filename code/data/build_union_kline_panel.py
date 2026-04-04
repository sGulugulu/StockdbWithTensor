from __future__ import annotations

import argparse
import csv
from pathlib import Path


def build_union_kline_panel(
    *,
    input_paths: list[Path],
    output_path: Path,
    selected_codes_output: Path,
) -> None:
    merged: dict[tuple[str, str], dict[str, str]] = {}
    all_codes: set[str] = set()
    fieldnames: list[str] | None = None

    for path in input_paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if fieldnames is None:
                fieldnames = reader.fieldnames or []
            for row in reader:
                key = (row["date"], row["code"])
                merged[key] = row
                all_codes.add(row["code"])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or [])
        if fieldnames:
            writer.writeheader()
            for key in sorted(merged):
                writer.writerow(merged[key])

    selected_codes_output.parent.mkdir(parents=True, exist_ok=True)
    with selected_codes_output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["code"])
        writer.writeheader()
        for code in sorted(all_codes):
            writer.writerow({"code": code})


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a canonical union kline panel and selected code list.")
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--selected-codes-output", type=Path, required=True)
    args = parser.parse_args()

    build_union_kline_panel(
        input_paths=args.inputs,
        output_path=args.output_path,
        selected_codes_output=args.selected_codes_output,
    )


if __name__ == "__main__":
    main()
