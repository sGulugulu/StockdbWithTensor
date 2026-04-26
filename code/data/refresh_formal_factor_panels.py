from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.build_extended_factor_panel import build_extended_factor_panel
from data.build_formal_factor_panel import build_formal_factor_panel


DEFAULT_MAX_TRADE_DATE = "2026-03-30"


@dataclass(frozen=True, slots=True)
class UniverseSpec:
    universe_id: str
    history_filename: str
    baseline_panel_filename: str
    extended_panel_filename: str
    market_index_filename: str


UNIVERSE_SPECS = (
    UniverseSpec("HS300", "hs300_history.csv", "hs300_factor_panel.csv", "hs300_factor_panel_extended.csv", "hs300_index_daily.csv"),
    UniverseSpec("SZ50", "sz50_history.csv", "sz50_factor_panel.csv", "sz50_factor_panel_extended.csv", "000050_index_daily.csv"),
    UniverseSpec("ZZ500", "zz500_history.csv", "zz500_factor_panel.csv", "zz500_factor_panel_extended.csv", "csi_a500_index_daily.csv"),
)


def refresh_formal_factor_panels(*, formal_root: Path, max_trade_date: str = DEFAULT_MAX_TRADE_DATE) -> list[Path]:
    normalized_root = formal_root.resolve()
    outputs: list[Path] = []
    shared_kline_path = normalized_root / "master" / "shared_kline_panel.csv"
    industry_path = normalized_root / "baostock" / "metadata" / "stock_industry.csv"
    profit_data_path = normalized_root / "baostock" / "financial" / "profit_data.csv"
    performance_express_path = normalized_root / "baostock" / "reports" / "performance_express_report"
    forecast_report_path = normalized_root / "baostock" / "reports" / "forecast_report"

    for spec in UNIVERSE_SPECS:
        baseline_output = normalized_root / "factors" / spec.baseline_panel_filename
        build_formal_factor_panel(
            kline_path=shared_kline_path,
            industry_path=industry_path,
            membership_path=normalized_root / "universes" / spec.history_filename,
            output_path=baseline_output,
            max_trade_date=max_trade_date,
        )
        outputs.append(baseline_output)

        extended_output = normalized_root / "factors" / spec.extended_panel_filename
        build_extended_factor_panel(
            base_panel_path=baseline_output,
            profit_data_path=profit_data_path,
            performance_express_path=performance_express_path,
            forecast_report_path=forecast_report_path,
            market_index_path=normalized_root / "index_daily" / spec.market_index_filename,
            output_path=extended_output,
            max_trade_date=max_trade_date,
        )
        outputs.append(extended_output)
    return outputs


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh baseline and extended formal factor panels.")
    parser.add_argument(
        "--formal-root",
        type=Path,
        default=Path(__file__).resolve().parent / "formal",
        help="formal 数据根目录，默认使用 code/data/formal",
    )
    parser.add_argument(
        "--max-trade-date",
        type=str,
        default=DEFAULT_MAX_TRADE_DATE,
        help="提交版 formal factor panel 的统一截断日期",
    )
    args = parser.parse_args()

    outputs = refresh_formal_factor_panels(
        formal_root=args.formal_root,
        max_trade_date=args.max_trade_date,
    )
    for path in outputs:
        print(path.as_posix())


if __name__ == "__main__":
    main()
