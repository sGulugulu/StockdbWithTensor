from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


SUPPLEMENT_FIELDS = [
    "turn",
    "tradestatus",
    "peTTM",
    "pbMRQ",
    "psTTM",
    "pcfNcfTTM",
    "isST",
]


def _load_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _key(row: dict[str, str]) -> tuple[str, str]:
    return (str(row.get("date", "")).strip(), str(row.get("code", "")).strip().lower())


def audit_baostock_fields_year(
    *,
    master_dir: Path,
    year: int,
    output_path: Path | None = None,
) -> dict[str, object]:
    tdx_base_path = master_dir / f"tdx_full_master_base_{year}.csv"
    baostock_path = master_dir / "baostock_fields" / f"{year}.csv"
    result: dict[str, object] = {
        "year": year,
        "tdx_base_path": str(tdx_base_path),
        "baostock_path": str(baostock_path),
    }

    missing = [str(path) for path in (tdx_base_path, baostock_path) if not path.exists()]
    if missing:
        result["status"] = "MISSING_INPUT"
        result["missing_files"] = missing
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    tdx_rows = _load_rows(tdx_base_path)
    baostock_rows = _load_rows(baostock_path)
    tdx_keys = {_key(row) for row in tdx_rows if all(_key(row))}
    intersection_keys = tdx_keys & {_key(row) for row in baostock_rows if all(_key(row))}

    key_counter = Counter(_key(row) for row in baostock_rows if all(_key(row)))
    duplicate_key_counts = {key: count for key, count in key_counter.items() if count > 1}
    duplicate_rows = [
        {"date": key[0], "code": key[1], "count": count}
        for key, count in sorted(duplicate_key_counts.items(), key=lambda item: (-item[1], item[0]))
    ]

    missing_field_counts = {field: 0 for field in SUPPLEMENT_FIELDS}
    missing_field_dates = {field: Counter() for field in SUPPLEMENT_FIELDS}
    missing_field_codes = {field: Counter() for field in SUPPLEMENT_FIELDS}
    for row in baostock_rows:
        row_key = _key(row)
        if row_key not in intersection_keys:
            continue
        for field in SUPPLEMENT_FIELDS:
            if not str(row.get(field, "")).strip():
                missing_field_counts[field] += 1
                missing_field_dates[field][row_key[0]] += 1
                missing_field_codes[field][row_key[1]] += 1

    issues: list[str] = []
    if duplicate_rows:
        issues.append("存在重复 date+code")
    low_or_empty_fields = [field for field, count in missing_field_counts.items() if count > 0]
    if low_or_empty_fields:
        issues.append("交集键上存在空补字段: " + ", ".join(low_or_empty_fields))

    result.update(
        {
            "tdx_rows": len(tdx_rows),
            "baostock_rows": len(baostock_rows),
            "intersection_keys": len(intersection_keys),
            "duplicate_key_count": len(duplicate_rows),
            "duplicate_keys": duplicate_rows[:200],
            "missing_field_counts": missing_field_counts,
            "missing_field_top_dates": {
                field: [{"date": date_value, "count": count} for date_value, count in counter.most_common(50)]
                for field, counter in missing_field_dates.items()
                if counter
            },
            "missing_field_top_codes": {
                field: [{"code": code, "count": count} for code, count in counter.most_common(50)]
                for field, counter in missing_field_codes.items()
                if counter
            },
        }
    )
    result["status"] = "OK" if not issues else "ISSUES"
    result["issues"] = issues

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit one year's baostock supplement file against TDX base keys.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--master-dir", type=Path, default=Path("code/data/formal/master"))
    parser.add_argument("--output-path", type=Path, default=None)
    args = parser.parse_args()

    output_path = args.output_path
    if output_path is None:
        output_path = args.master_dir / "logs" / f"baostock_fields_{args.year}_audit.json"

    result = audit_baostock_fields_year(master_dir=args.master_dir, year=args.year, output_path=output_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
