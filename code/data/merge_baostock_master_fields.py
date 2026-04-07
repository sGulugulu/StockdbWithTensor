from __future__ import annotations

import argparse
import csv
from pathlib import Path


BAOSTOCK_SUPPLEMENT_FIELDS = [
    "turn",
    "tradestatus",
    "peTTM",
    "pbMRQ",
    "psTTM",
    "pcfNcfTTM",
    "isST",
]


def _load_baostock_lookup(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    lookup: dict[tuple[str, str], dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if not row.get("date") or not row.get("code"):
                continue
            lookup[(row["date"], row["code"].strip().lower())] = row
    return lookup


def merge_baostock_master_fields(
    *,
    tdx_base_path: Path,
    baostock_path: Path,
    output_path: Path,
) -> None:
    lookup = _load_baostock_lookup(baostock_path)
    merged_rows: list[dict[str, str]] = []
    with tdx_base_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        base_fields = reader.fieldnames or []
        for row in reader:
            key = (row["date"], row["code"].strip().lower())
            supplement = lookup.get(key, {})
            merged = dict(row)
            for field in BAOSTOCK_SUPPLEMENT_FIELDS:
                merged[field] = supplement.get(field, "")
            merged_rows.append(merged)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(base_fields) + [field for field in BAOSTOCK_SUPPLEMENT_FIELDS if field not in base_fields]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(merged_rows)
        else:
            handle.write("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge baostock valuation/state fields into a TDX-based master panel.")
    parser.add_argument("--tdx-base-path", type=Path, required=True)
    parser.add_argument("--baostock-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()
    merge_baostock_master_fields(
        tdx_base_path=args.tdx_base_path,
        baostock_path=args.baostock_path,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    main()
