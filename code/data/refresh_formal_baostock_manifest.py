from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path


def _csv_row_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return sum(1 for _ in csv.DictReader(handle))


def _csv_date_range(path: Path, date_column: str) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, None
    dates: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get(date_column):
                dates.append(row[date_column])
    if not dates:
        return None, None
    return min(dates), max(dates)


def _history_date_range(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, None
    start_dates: list[str] = []
    end_dates: list[str] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("start_date"):
                start_dates.append(row["start_date"])
            if row.get("end_date"):
                end_dates.append(row["end_date"])
    start_value = min(start_dates) if start_dates else None
    end_value = max(end_dates) if end_dates else None
    return start_value, end_value


def _copy_tree(src: Path, dst: Path) -> None:
    if not src.exists():
        return
    for path in src.rglob("*"):
        if path.name.endswith("_30.csv"):
            continue
        relative = path.relative_to(src)
        target = dst / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def refresh_manifest(
    *,
    canonical_root: Path,
    hs300_src: Path,
    sz50_src: Path,
    zz500_src: Path,
    formal_root: Path,
) -> Path:
    canonical_root.mkdir(parents=True, exist_ok=True)
    stage_sources = {
        "hs300": hs300_src,
        "sz50": sz50_src,
        "zz500": zz500_src,
    }
    for source in stage_sources.values():
        _copy_tree(source, canonical_root)

    manifest = {
        "source": "baostock",
        "kline_adjustflag": "2",
        "stages": {
            "stage_1_stage_2_committed_sources": {},
            "stage_3_formal_outputs": {},
        },
    }

    for key, source in stage_sources.items():
        source_manifest = source / "manifest.json"
        manifest["stages"]["stage_1_stage_2_committed_sources"][key] = (
            json.loads(source_manifest.read_text(encoding="utf-8"))
            if source_manifest.exists()
            else None
        )

    for universe_id in ("hs300", "sz50", "zz500"):
        history_path = formal_root / f"{universe_id}_history.csv"
        factor_path = formal_root / f"{universe_id}_factor_panel.csv"
        history_start, history_end = _history_date_range(history_path)
        factor_start, factor_end = _csv_date_range(factor_path, "trade_date")
        manifest["stages"]["stage_3_formal_outputs"][universe_id] = {
            "history_path": str(history_path),
            "history_rows": _csv_row_count(history_path),
            "history_start_date": history_start,
            "history_end_date": history_end,
            "factor_panel_path": str(factor_path),
            "factor_panel_rows": _csv_row_count(factor_path),
            "factor_panel_start_date": factor_start,
            "factor_panel_end_date": factor_end,
        }

    kline_path = canonical_root / "kline_panel.csv"
    kline_start, kline_end = _csv_date_range(kline_path, "date")
    manifest["stages"]["stage_3_formal_outputs"]["shared_kline_panel"] = {
        "kline_panel_path": str(kline_path),
        "kline_panel_rows": _csv_row_count(kline_path),
        "kline_panel_start_date": kline_start,
        "kline_panel_end_date": kline_end,
    }
    selected_codes_path = canonical_root / "metadata" / "selected_codes.csv"
    manifest["stages"]["stage_3_formal_outputs"]["shared_selected_codes"] = {
        "selected_codes_path": str(selected_codes_path),
        "selected_codes_rows": _csv_row_count(selected_codes_path),
    }

    financial_dir = canonical_root / "financial"
    reports_dir = canonical_root / "reports"
    manifest["stages"]["stage_2_formal_outputs"] = {
        "financial_files": sorted(str(path) for path in financial_dir.glob("*.csv")),
        "report_files": sorted(str(path) for path in reports_dir.glob("*.csv")),
    }

    manifest_path = canonical_root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh canonical formal baostock manifest and root directory.")
    parser.add_argument("--canonical-root", type=Path, default=Path("code/data/formal/baostock"))
    parser.add_argument("--hs300-src", type=Path, default=Path("code/data/formal/baostock_fg_test"))
    parser.add_argument("--sz50-src", type=Path, default=Path("code/data/formal/baostock_sz50_fg"))
    parser.add_argument("--zz500-src", type=Path, default=Path("code/data/formal/baostock_zz500_fg"))
    parser.add_argument("--formal-root", type=Path, default=Path("code/data/formal"))
    args = parser.parse_args()
    manifest_path = refresh_manifest(
        canonical_root=args.canonical_root,
        hs300_src=args.hs300_src,
        sz50_src=args.sz50_src,
        zz500_src=args.zz500_src,
        formal_root=args.formal_root,
    )
    print(f"Updated canonical manifest: {manifest_path}")


if __name__ == "__main__":
    main()
