from __future__ import annotations

import argparse
import csv
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


def _key_set(rows: list[dict[str, str]]) -> set[tuple[str, str]]:
    return {
        (row.get("date", "").strip(), row.get("code", "").strip().lower())
        for row in rows
        if row.get("date") and row.get("code")
    }


def _row_nonempty_ratio(rows: list[dict[str, str]], field: str) -> float:
    if not rows:
        return 0.0
    return sum(1 for row in rows if str(row.get(field, "")).strip()) / len(rows)


def _dates_summary(rows: list[dict[str, str]]) -> tuple[str | None, str | None]:
    dates = sorted({row.get("date", "") for row in rows if row.get("date")})
    if not dates:
        return None, None
    return dates[0], dates[-1]


def _codes_summary(rows: list[dict[str, str]]) -> int:
    return len({row.get("code", "").strip().lower() for row in rows if row.get("code")})


def _top_counts(keys: set[tuple[str, str]], by_index: int, limit: int = 10) -> list[tuple[str, int]]:
    counter = Counter(key[by_index] for key in keys)
    return counter.most_common(limit)


def _all_counts(keys: set[tuple[str, str]], by_index: int) -> list[tuple[str, int]]:
    counter = Counter(key[by_index] for key in keys)
    return sorted(counter.items(), key=lambda item: (-item[1], item[0]))


def _append_count_section(
    lines: list[str],
    title: str,
    keys: set[tuple[str, str]],
    by_index: int,
) -> None:
    lines.append(title)
    for value, count in _all_counts(keys, by_index):
        lines.append(f"{value}: {count}")
    lines.append("")


def reconcile_full_master_year(
    *,
    master_dir: Path,
    year: int,
    output_path: Path | None = None,
) -> str:
    tdx_base_path = master_dir / f"tdx_full_master_base_{year}.csv"
    baostock_path = master_dir / "baostock_fields" / f"{year}.csv"
    full_master_path = master_dir / f"full_master_{year}.csv"

    lines: list[str] = [f"Full Master Reconcile Report: {year}", ""]
    lines.append(f"tdx_base={tdx_base_path}")
    lines.append(f"baostock_fields={baostock_path}")
    lines.append(f"full_master={full_master_path}")
    lines.append("")

    missing = [str(path) for path in [tdx_base_path, baostock_path, full_master_path] if not path.exists()]
    if missing:
        lines.append("STATUS: MISSING_INPUT")
        lines.append("Missing files:")
        for item in missing:
            lines.append(f"- {item}")
        report = "\n".join(lines)
        if output_path is not None:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(report, encoding="utf-8")
        return report

    tdx_rows = _load_rows(tdx_base_path)
    baostock_rows = _load_rows(baostock_path)
    full_rows = _load_rows(full_master_path)

    tdx_keys = _key_set(tdx_rows)
    baostock_keys = _key_set(baostock_rows)
    full_keys = _key_set(full_rows)

    tdx_min, tdx_max = _dates_summary(tdx_rows)
    bs_min, bs_max = _dates_summary(baostock_rows)
    full_min, full_max = _dates_summary(full_rows)

    lines.append("[row-counts]")
    lines.append(f"tdx_base_rows={len(tdx_rows)}")
    lines.append(f"baostock_rows={len(baostock_rows)}")
    lines.append(f"full_master_rows={len(full_rows)}")
    lines.append("")

    lines.append("[stock-counts]")
    lines.append(f"tdx_base_codes={_codes_summary(tdx_rows)}")
    lines.append(f"baostock_codes={_codes_summary(baostock_rows)}")
    lines.append(f"full_master_codes={_codes_summary(full_rows)}")
    lines.append("")

    lines.append("[date-ranges]")
    lines.append(f"tdx_base={tdx_min} -> {tdx_max}")
    lines.append(f"baostock={bs_min} -> {bs_max}")
    lines.append(f"full_master={full_min} -> {full_max}")
    lines.append("")

    only_in_tdx = tdx_keys - baostock_keys
    only_in_baostock = baostock_keys - tdx_keys
    only_in_full = full_keys - tdx_keys
    missing_from_full = tdx_keys - full_keys

    lines.append("[key-coverage]")
    lines.append(f"tdx_keys={len(tdx_keys)}")
    lines.append(f"baostock_keys={len(baostock_keys)}")
    lines.append(f"full_master_keys={len(full_keys)}")
    lines.append(f"tdx_minus_baostock={len(only_in_tdx)}")
    lines.append(f"baostock_minus_tdx={len(only_in_baostock)}")
    lines.append(f"full_minus_tdx={len(only_in_full)}")
    lines.append(f"tdx_minus_full={len(missing_from_full)}")
    lines.append("")

    if only_in_tdx:
        lines.append("[top-missing-from-baostock-by-code]")
        for code, count in _top_counts(only_in_tdx, 1):
            lines.append(f"{code}: {count}")
        lines.append("")
        lines.append("[top-missing-from-baostock-by-date]")
        for date_value, count in _top_counts(only_in_tdx, 0):
            lines.append(f"{date_value}: {count}")
        lines.append("")
        _append_count_section(lines, "[all-missing-from-baostock-by-code]", only_in_tdx, 1)
        _append_count_section(lines, "[all-missing-from-baostock-by-date]", only_in_tdx, 0)

    if only_in_baostock:
        lines.append("[top-extra-in-baostock-by-code]")
        for code, count in _top_counts(only_in_baostock, 1):
            lines.append(f"{code}: {count}")
        lines.append("")
        lines.append("[top-extra-in-baostock-by-date]")
        for date_value, count in _top_counts(only_in_baostock, 0):
            lines.append(f"{date_value}: {count}")
        lines.append("")
        _append_count_section(lines, "[all-extra-in-baostock-by-code]", only_in_baostock, 1)
        _append_count_section(lines, "[all-extra-in-baostock-by-date]", only_in_baostock, 0)

    lines.append("[full-master-supplement-field-ratios]")
    for field in SUPPLEMENT_FIELDS:
        lines.append(f"{field}={_row_nonempty_ratio(full_rows, field):.6f}")
    lines.append("")

    issues: list[str] = []
    if only_in_tdx:
        issues.append("baostock supplement 未覆盖全部 TDX date+code")
    if only_in_baostock:
        issues.append("baostock supplement 含有 TDX base 不存在的 date+code")
    if only_in_full:
        issues.append("full master 含有 TDX base 不存在的 date+code")
    if missing_from_full:
        issues.append("full master 缺少 TDX base 的 date+code")
    low_fields = [field for field in SUPPLEMENT_FIELDS if _row_nonempty_ratio(full_rows, field) < 0.95]
    if low_fields:
        issues.append("full master 补字段非空率过低: " + ", ".join(low_fields))

    lines.append("[status]")
    if issues:
        lines.append("ISSUES")
        for issue in issues:
            lines.append(f"- {issue}")
    else:
        lines.append("OK")

    report = "\n".join(lines)
    if output_path is not None:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Reconcile one year's TDX base, baostock supplement, and full master.")
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--master-dir", type=Path, default=Path("code/data/formal/master"))
    parser.add_argument("--output-path", type=Path, default=None)
    args = parser.parse_args()

    output_path = args.output_path
    if output_path is None:
        output_path = args.master_dir / "logs" / f"full_master_{args.year}_reconcile.log"

    report = reconcile_full_master_year(
        master_dir=args.master_dir,
        year=args.year,
        output_path=output_path,
    )
    print(report)


if __name__ == "__main__":
    main()
