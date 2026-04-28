from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import tempfile
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.build_formal_factor_panel import build_formal_factor_panel


@dataclass(frozen=True, slots=True)
class PanelSpec:
    history_path: Path
    output_filename: str


PANEL_SPECS = (
    PanelSpec(Path("universes/segmented/all_a_active_history.csv"), "all_a_factor_panel_long_window.csv"),
    PanelSpec(Path("universes/segmented/industry_c27_history.csv"), "industry_c27_factor_panel_long_window.csv"),
    PanelSpec(Path("universes/segmented/industry_c35_history.csv"), "industry_c35_factor_panel_long_window.csv"),
    PanelSpec(Path("universes/segmented/industry_c39_history.csv"), "industry_c39_factor_panel_long_window.csv"),
    PanelSpec(Path("universes/segmented/size_small_history.csv"), "size_small_factor_panel_long_window.csv"),
    PanelSpec(Path("universes/segmented/size_mid_history.csv"), "size_mid_factor_panel_long_window.csv"),
    PanelSpec(Path("universes/segmented/size_large_history.csv"), "size_large_factor_panel_long_window.csv"),
)


def _year_end_cap(year: int, max_trade_date: str) -> str:
    return min(f"{year}-12-31", max_trade_date)


def _concatenate_yearly_masters(*, source_paths: list[Path], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames: list[str] | None = None
    with output_path.open("w", encoding="utf-8", newline="") as dst:
        writer: csv.DictWriter[str] | None = None
        for source_path in source_paths:
            with source_path.open("r", encoding="utf-8-sig", newline="") as src:
                reader = csv.DictReader(src)
                rows = list(reader)
                if not rows:
                    continue
                if fieldnames is None:
                    fieldnames = list(reader.fieldnames or [])
                    writer = csv.DictWriter(dst, fieldnames=fieldnames)
                    writer.writeheader()
                if writer is None:
                    raise ValueError("writer unexpectedly not initialized")
                writer.writerows(rows)
        if fieldnames is None:
            dst.write("")


def _split_panel_by_year(
    *,
    source_path: Path,
    yearly_root: Path,
    filename: str,
    start_year: int,
    end_year: int,
    max_trade_date: str,
) -> list[Path]:
    yearly_root.mkdir(parents=True, exist_ok=True)
    with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])
    outputs: list[Path] = []
    for year in range(start_year, end_year + 1):
        yearly_output = yearly_root / str(year) / filename
        yearly_output.parent.mkdir(parents=True, exist_ok=True)
        year_rows = [
            row
            for row in rows
            if row.get("trade_date", "").startswith(f"{year}-")
            and row.get("trade_date", "") <= _year_end_cap(year, max_trade_date)
        ]
        with yearly_output.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            if fieldnames:
                writer.writeheader()
                writer.writerows(year_rows)
            else:
                handle.write("")
        outputs.append(yearly_output)
    return outputs


def build_long_window_factor_panels(
    *,
    formal_root: Path,
    start_year: int,
    end_year: int,
    max_trade_date: str,
) -> list[Path]:
    normalized_root = formal_root.resolve()
    industry_path = normalized_root / "baostock" / "metadata" / "stock_industry.csv"
    output_root = normalized_root / "factors" / "long_window"
    yearly_root = output_root / "yearly"
    outputs: list[Path] = []
    master_paths = [
        normalized_root / "master" / f"full_master_{year}.csv"
        for year in range(start_year, end_year + 1)
    ]
    for master_path in master_paths:
        if not master_path.exists():
            raise FileNotFoundError(f"Missing yearly full master: {master_path}")

    with tempfile.TemporaryDirectory() as temp_dir:
        combined_master_path = Path(temp_dir) / "full_master_long_window.csv"
        _concatenate_yearly_masters(source_paths=master_paths, output_path=combined_master_path)

        for spec in PANEL_SPECS:
            final_output = output_root / spec.output_filename
            # 先用连续 master 计算滚动因子和未来收益，再拆回年度文件，避免年界截断信号。
            build_formal_factor_panel(
                kline_path=combined_master_path,
                industry_path=industry_path,
                membership_path=normalized_root / spec.history_path,
                output_path=final_output,
                max_trade_date=max_trade_date,
            )
            outputs.append(final_output)
            yearly_outputs = _split_panel_by_year(
                source_path=final_output,
                yearly_root=yearly_root,
                filename=spec.output_filename,
                start_year=start_year,
                end_year=end_year,
                max_trade_date=max_trade_date,
            )
            outputs.extend(yearly_outputs)

    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Build long-window factor panels from yearly full master files.")
    parser.add_argument("--formal-root", type=Path, default=Path(__file__).resolve().parent / "formal")
    parser.add_argument("--start-year", type=int, default=2015)
    parser.add_argument("--end-year", type=int, default=2026)
    parser.add_argument("--max-trade-date", type=str, default="2026-03-30")
    args = parser.parse_args()

    outputs = build_long_window_factor_panels(
        formal_root=args.formal_root,
        start_year=args.start_year,
        end_year=args.end_year,
        max_trade_date=args.max_trade_date,
    )
    for path in outputs:
        print(path.as_posix())


if __name__ == "__main__":
    main()
