from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.build_extended_factor_panel import build_extended_factor_panel
from data.build_formal_extended_sources import build_formal_extended_sources
from data.build_formal_factor_panel import build_formal_factor_panel


DEFAULT_MAX_TRADE_DATE = "2026-03-30"


@dataclass(frozen=True, slots=True)
class UniverseSpec:
    universe_id: str
    history_filename: str
    baseline_panel_filename: str
    extended_panel_filename: str
    market_index_filename: str


@dataclass(frozen=True, slots=True)
class ExtendedSourcePaths:
    macro_interest_rate_path: Path
    macro_monthly_path: Path
    dividend_events_path: Path
    major_event_notice_path: Path
    announcement_text_path: Path


UNIVERSE_SPECS = (
    UniverseSpec("HS300", "hs300_history.csv", "hs300_factor_panel.csv", "hs300_factor_panel_extended.csv", "hs300_index_daily.csv"),
    UniverseSpec("SZ50", "sz50_history.csv", "sz50_factor_panel.csv", "sz50_factor_panel_extended.csv", "000050_index_daily.csv"),
    UniverseSpec("ZZ500", "zz500_history.csv", "zz500_factor_panel.csv", "zz500_factor_panel_extended.csv", "zz500_index_daily.csv"),
)


def _cached_source_paths(formal_root: Path) -> ExtendedSourcePaths:
    return ExtendedSourcePaths(
        macro_interest_rate_path=formal_root / "external" / "macro_interest_rate.csv",
        macro_monthly_path=formal_root / "external" / "macro_monthly_indicator.csv",
        dividend_events_path=formal_root / "events" / "dividend_event.csv",
        major_event_notice_path=formal_root / "events" / "major_event_notice.csv",
        announcement_text_path=formal_root / "events" / "announcement_text.csv",
    )


def _read_required_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing cached extended source snapshot: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if not rows:
        raise ValueError(f"Cached extended source snapshot has no data rows: {path}")
    return rows


def _validate_cached_source_snapshots(source_paths: ExtendedSourcePaths, *, max_trade_date: str) -> None:
    # 公告全集按日抓取，必须覆盖到实验截断日；其它低频源只校验存在且非空。
    for path in (
        source_paths.macro_interest_rate_path,
        source_paths.macro_monthly_path,
        source_paths.dividend_events_path,
        source_paths.major_event_notice_path,
        source_paths.announcement_text_path,
    ):
        _read_required_csv_rows(path)
    announcement_rows = _read_required_csv_rows(source_paths.announcement_text_path)
    max_notice_date = max((row.get("pub_date") or "" for row in announcement_rows), default="")
    if max_notice_date < max_trade_date:
        raise ValueError(
            f"Cached announcement snapshot ends at {max_notice_date}, before max_trade_date {max_trade_date}: "
            f"{source_paths.announcement_text_path}"
        )


def refresh_formal_factor_panels(*, formal_root: Path, max_trade_date: str = DEFAULT_MAX_TRADE_DATE) -> list[Path]:
    return refresh_formal_factor_panels_with_sources(
        formal_root=formal_root,
        max_trade_date=max_trade_date,
        build_extended_source_tables=False,
    )


def refresh_formal_factor_panels_with_sources(
    *,
    formal_root: Path,
    max_trade_date: str = DEFAULT_MAX_TRADE_DATE,
    build_extended_source_tables: bool = False,
) -> list[Path]:
    normalized_root = formal_root.resolve()
    outputs: list[Path] = []
    baseline_outputs: dict[str, Path] = {}
    shared_kline_path = normalized_root / "master" / "shared_kline_panel.csv"
    industry_path = normalized_root / "baostock" / "metadata" / "stock_industry.csv"
    profit_data_path = normalized_root / "baostock" / "financial" / "profit_data.csv"
    performance_express_path = normalized_root / "baostock" / "reports" / "performance_express_report"
    forecast_report_path = normalized_root / "baostock" / "reports" / "forecast_report"
    source_paths = _cached_source_paths(normalized_root)
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
        baseline_outputs[spec.universe_id] = baseline_output

    if build_extended_source_tables:
        # 显式重建才调用 AKShare，默认复用已提交快照以保证离线复现。
        extended_sources = build_formal_extended_sources(
            formal_root=normalized_root,
            max_trade_date=max_trade_date,
        )
    else:
        _validate_cached_source_snapshots(source_paths, max_trade_date=max_trade_date)
        extended_sources = source_paths

    for spec in UNIVERSE_SPECS:
        extended_output = normalized_root / "factors" / spec.extended_panel_filename
        build_extended_factor_panel(
            base_panel_path=baseline_outputs[spec.universe_id],
            profit_data_path=profit_data_path,
            performance_express_path=performance_express_path,
            forecast_report_path=forecast_report_path,
            market_index_path=normalized_root / "index_daily" / spec.market_index_filename,
            macro_interest_rate_path=extended_sources.macro_interest_rate_path,
            macro_monthly_path=extended_sources.macro_monthly_path,
            dividend_event_path=extended_sources.dividend_events_path,
            major_event_notice_path=extended_sources.major_event_notice_path,
            announcement_text_path=extended_sources.announcement_text_path,
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
    parser.add_argument(
        "--rebuild-extended-sources",
        action="store_true",
        help="联网重建宏观、分红和公告源表；默认复用已提交的 source CSV 快照",
    )
    args = parser.parse_args()

    outputs = refresh_formal_factor_panels_with_sources(
        formal_root=args.formal_root,
        max_trade_date=args.max_trade_date,
        build_extended_source_tables=args.rebuild_extended_sources,
    )
    for path in outputs:
        print(path.as_posix())


if __name__ == "__main__":
    main()
