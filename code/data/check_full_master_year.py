from __future__ import annotations

import argparse
import csv
import json
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


def _nonempty_ratio(rows: list[dict[str, str]], field: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if str(row.get(field, "")).strip()) / len(rows)


def check_full_master_year(
    *,
    master_dir: Path,
    year: int,
    output_path: Path | None = None,
) -> dict[str, object]:
    master_path = master_dir / f"full_master_{year}.csv"
    result: dict[str, object] = {
        "year": year,
        "path": str(master_path),
        "exists": master_path.exists(),
    }
    if not master_path.exists():
        result["status"] = "MISSING"
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return result

    with master_path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))

    dates = sorted({row["date"] for row in rows if row.get("date")})
    codes = {row["code"] for row in rows if row.get("code")}
    result["rows"] = len(rows)
    result["stock_count"] = len(codes)
    result["min_date"] = dates[0] if dates else None
    result["max_date"] = dates[-1] if dates else None
    result["field_nonempty"] = {
        field: {
            "count": sum(1 for row in rows if str(row.get(field, "")).strip()),
            "ratio": round(_nonempty_ratio(rows, field), 6),
        }
        for field in SUPPLEMENT_FIELDS
    }

    issues: list[str] = []
    if not rows:
        issues.append("文件为空")
    if result["min_date"] is None or result["max_date"] is None:
        issues.append("缺少有效日期范围")
    else:
        if not str(result["min_date"]).startswith(f"{year}-"):
            issues.append(f"最小日期不在目标年份: {result['min_date']}")
        if not str(result["max_date"]).startswith(f"{year}-"):
            issues.append(f"最大日期不在目标年份: {result['max_date']}")

    low_fields = [
        field for field, detail in result["field_nonempty"].items()
        if detail["ratio"] < 0.95
    ]
    if low_fields:
        issues.append("补字段非空率过低: " + ", ".join(low_fields))

    result["status"] = "OK" if not issues else "ISSUES"
    result["issues"] = issues

    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Check one year's full master CSV completeness.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--master-dir", type=Path, default=Path("code/data/formal/master"))
    parser.add_argument("--output-path", type=Path, default=None)
    args = parser.parse_args()

    output_path = args.output_path
    if output_path is None:
        output_path = args.master_dir / f"full_master_{args.year}_check.json"

    result = check_full_master_year(
        master_dir=args.master_dir,
        year=args.year,
        output_path=output_path,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
