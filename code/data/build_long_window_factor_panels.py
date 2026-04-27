from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
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


def _concatenate_yearly_panels(*, source_paths: list[Path], output_path: Path) -> None:
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

    for spec in PANEL_SPECS:
        yearly_outputs: list[Path] = []
        for year in range(start_year, end_year + 1):
            master_path = normalized_root / "master" / f"full_master_{year}.csv"
            if not master_path.exists():
                raise FileNotFoundError(f"Missing yearly full master: {master_path}")
            yearly_output = yearly_root / str(year) / spec.output_filename
            build_formal_factor_panel(
                kline_path=master_path,
                industry_path=industry_path,
                membership_path=normalized_root / spec.history_path,
                output_path=yearly_output,
                max_trade_date=_year_end_cap(year, max_trade_date),
            )
            yearly_outputs.append(yearly_output)
            outputs.append(yearly_output)

        final_output = output_root / spec.output_filename
        _concatenate_yearly_panels(source_paths=yearly_outputs, output_path=final_output)
        outputs.append(final_output)

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
