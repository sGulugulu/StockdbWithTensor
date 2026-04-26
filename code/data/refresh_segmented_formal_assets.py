from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.build_formal_factor_panel import build_formal_factor_panel
from data.build_segmented_formal_universes import build_segmented_formal_universes


@dataclass(frozen=True, slots=True)
class PanelSpec:
    history_filename: str
    panel_filename: str


PANEL_SPECS = (
    PanelSpec("all_a_active_history.csv", "all_a_factor_panel.csv"),
    PanelSpec("industry_c39_history.csv", "industry_c39_factor_panel.csv"),
    PanelSpec("industry_c27_history.csv", "industry_c27_factor_panel.csv"),
    PanelSpec("industry_c35_history.csv", "industry_c35_factor_panel.csv"),
    PanelSpec("size_small_history.csv", "size_small_factor_panel.csv"),
    PanelSpec("size_mid_history.csv", "size_mid_factor_panel.csv"),
    PanelSpec("size_large_history.csv", "size_large_factor_panel.csv"),
)


def refresh_segmented_formal_assets(*, formal_root: Path, max_trade_date: str) -> list[Path]:
    normalized_root = formal_root.resolve()
    segmented_dir = normalized_root / "universes" / "segmented"
    result = build_segmented_formal_universes(
        all_a_history_path=normalized_root / "universes" / "all_a_tradable_history.csv",
        industry_path=normalized_root / "baostock" / "metadata" / "stock_industry.csv",
        profit_data_path=normalized_root / "baostock" / "financial" / "profit_data.csv",
        shared_kline_path=normalized_root / "master" / "shared_kline_panel.csv",
        output_dir=segmented_dir,
        as_of_date=max_trade_date,
    )
    generated_paths = [result.all_a_history_path, *result.industry_history_paths, *result.size_history_paths]

    outputs: list[Path] = list(generated_paths)
    for spec in PANEL_SPECS:
        history_path = segmented_dir / spec.history_filename
        output_path = normalized_root / "factors" / spec.panel_filename
        build_formal_factor_panel(
            kline_path=normalized_root / "master" / "shared_kline_panel.csv",
            industry_path=normalized_root / "baostock" / "metadata" / "stock_industry.csv",
            membership_path=history_path,
            output_path=output_path,
            max_trade_date=max_trade_date,
        )
        outputs.append(output_path)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh AC3 segmented formal universes and factor panels.")
    parser.add_argument("--formal-root", type=Path, default=Path(__file__).resolve().parent / "formal")
    parser.add_argument("--max-trade-date", type=str, default="2026-03-30")
    args = parser.parse_args()
    for path in refresh_segmented_formal_assets(formal_root=args.formal_root, max_trade_date=args.max_trade_date):
        print(path.as_posix())


if __name__ == "__main__":
    main()
