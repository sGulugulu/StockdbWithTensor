from __future__ import annotations

import argparse
import csv
import json
import shutil
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.build_union_kline_panel import build_union_kline_panel
from stock_tensor.market import SymbolNormalizer


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


def _copy_tree(src: Path, dst: Path, *, excluded_relative_paths: set[str] | None = None) -> None:
    if not src.exists():
        return
    excluded = excluded_relative_paths or set()
    for path in src.rglob("*"):
        if path.name.endswith("_30.csv"):
            continue
        relative = path.relative_to(src)
        if relative.as_posix() in excluded:
            continue
        target = dst / relative
        if path.is_dir():
            target.mkdir(parents=True, exist_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, target)


def _load_normalized_code_set(path: Path, column: str, market_id: str = "cn_a") -> set[str]:
    if not path.exists():
        return set()
    normalizer = SymbolNormalizer(market_id)
    codes: set[str] = set()
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get(column):
                codes.add(normalizer.normalize(row[column]))
    return codes


def _load_factor_panel_code_set(formal_root: Path) -> set[str]:
    codes: set[str] = set()
    for universe_id in ("hs300", "sz50", "zz500"):
        factor_path = formal_root / "factors" / f"{universe_id}_factor_panel.csv"
        if not factor_path.exists():
            factor_path = formal_root / f"{universe_id}_factor_panel.csv"
        codes.update(_load_normalized_code_set(factor_path, "stock_code"))
    return codes


def _sample_codes(codes: set[str], limit: int = 8) -> list[str]:
    return sorted(codes)[:limit]


def _build_shared_stage3_outputs(canonical_root: Path, formal_root: Path) -> tuple[Path, Path]:
    shared_master_path = formal_root / "master" / "shared_kline_panel.csv"
    if shared_master_path.exists():
        output_path = canonical_root / "kline_panel.csv"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(shared_master_path, output_path)
        selected_codes_output = canonical_root / "metadata" / "selected_codes.csv"
        build_union_kline_panel(
            input_paths=[shared_master_path],
            output_path=output_path,
            selected_codes_output=selected_codes_output,
        )
        return output_path, selected_codes_output

    input_paths = [
        formal_root / "hs300_kline_panel.csv",
        formal_root / "sz50_kline_panel.csv",
        formal_root / "zz500_kline_panel.csv",
    ]
    existing_inputs = [path for path in input_paths if path.exists()]
    if not existing_inputs:
        raise FileNotFoundError("No formal per-universe kline panels exist for canonical Stage 3 generation.")

    output_path = canonical_root / "kline_panel.csv"
    selected_codes_output = canonical_root / "metadata" / "selected_codes.csv"
    build_union_kline_panel(
        input_paths=existing_inputs,
        output_path=output_path,
        selected_codes_output=selected_codes_output,
    )
    return output_path, selected_codes_output


def _assert_shared_stage3_consistency(
    *,
    kline_path: Path,
    selected_codes_path: Path,
    formal_root: Path,
) -> None:
    kline_codes = _load_normalized_code_set(kline_path, "code")
    selected_codes = _load_normalized_code_set(selected_codes_path, "code")
    if kline_codes != selected_codes:
        missing_from_selected = kline_codes - selected_codes
        missing_from_kline = selected_codes - kline_codes
        raise ValueError(
            "Canonical shared selected codes must exactly match the canonical kline code set. "
            f"missing_from_selected={len(missing_from_selected)} sample={_sample_codes(missing_from_selected)}; "
            f"missing_from_kline={len(missing_from_kline)} sample={_sample_codes(missing_from_kline)}"
        )

    factor_codes = _load_factor_panel_code_set(formal_root)
    if not factor_codes.issubset(kline_codes):
        missing_factor_codes = factor_codes - kline_codes
        raise ValueError(
            "Canonical shared kline code set must cover every code used by formal factor panels. "
            f"missing_factor_codes={len(missing_factor_codes)} sample={_sample_codes(missing_factor_codes)}"
        )


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
        _copy_tree(
            source,
            canonical_root,
            excluded_relative_paths={"metadata/selected_codes.csv"},
        )

    kline_path, selected_codes_path = _build_shared_stage3_outputs(canonical_root, formal_root)
    _assert_shared_stage3_consistency(
        kline_path=kline_path,
        selected_codes_path=selected_codes_path,
        formal_root=formal_root,
    )

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
        history_path = formal_root / "universes" / f"{universe_id}_history.csv"
        factor_path = formal_root / "factors" / f"{universe_id}_factor_panel.csv"
        if not history_path.exists():
            history_path = formal_root / f"{universe_id}_history.csv"
        if not factor_path.exists():
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

    kline_start, kline_end = _csv_date_range(kline_path, "date")
    manifest["stages"]["stage_3_formal_outputs"]["shared_kline_panel"] = {
        "kline_panel_path": str(kline_path),
        "kline_panel_rows": _csv_row_count(kline_path),
        "kline_panel_start_date": kline_start,
        "kline_panel_end_date": kline_end,
    }
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
