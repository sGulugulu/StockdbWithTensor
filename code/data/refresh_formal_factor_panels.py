from __future__ import annotations

import argparse
import csv
import json
import shutil
import tempfile
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.build_extended_factor_panel import build_extended_factor_panel
from data.build_formal_extended_sources import build_formal_extended_sources
from data.build_formal_factor_panel import build_formal_factor_panel


DEFAULT_MAX_TRADE_DATE = "2026-03-30"
NOTICE_FEATURE_WINDOW_DAYS = 30


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
    snapshot_metadata_path: Path


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
        snapshot_metadata_path=formal_root / "events" / "extended_source_snapshot.json",
    )


def _read_required_csv_rows(path: Path, *, allow_empty: bool = False) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"Missing cached extended source snapshot: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    if reader.fieldnames is None:
        raise ValueError(f"Cached extended source snapshot has no header: {path}")
    if not rows and not allow_empty:
        raise ValueError(f"Cached extended source snapshot has no data rows: {path}")
    return rows


def _earliest_trade_date(panel_paths: list[Path]) -> str:
    earliest: str | None = None
    for path in panel_paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                trade_date = row.get("trade_date")
                if trade_date and (earliest is None or trade_date < earliest):
                    earliest = trade_date
    if earliest is None:
        raise ValueError("No trade dates found in baseline factor panels.")
    return earliest


def _required_notice_start_date(earliest_trade_date: str) -> str:
    return (date.fromisoformat(earliest_trade_date) - timedelta(days=NOTICE_FEATURE_WINDOW_DAYS)).isoformat()


def _validate_cached_source_snapshots(
    source_paths: ExtendedSourcePaths,
    *,
    max_trade_date: str,
    earliest_trade_date: str,
) -> None:
    # CSV 只证明有数据；覆盖水位由显式 metadata 记录，避免 cutoff 当天无公告时误判过期。
    for csv_path, allow_empty in (
        (source_paths.macro_interest_rate_path, False),
        (source_paths.macro_monthly_path, False),
        (source_paths.dividend_events_path, True),
        (source_paths.major_event_notice_path, True),
        (source_paths.announcement_text_path, True),
    ):
        _read_required_csv_rows(csv_path, allow_empty=allow_empty)
    if not source_paths.snapshot_metadata_path.exists():
        raise FileNotFoundError(
            f"Missing cached extended source snapshot metadata: {source_paths.snapshot_metadata_path}"
        )
    metadata = json.loads(source_paths.snapshot_metadata_path.read_text(encoding="utf-8"))
    snapshot_max_trade_date = str(metadata.get("max_trade_date") or "")
    if snapshot_max_trade_date < max_trade_date:
        raise ValueError(
            f"Cached extended source snapshot ends at {snapshot_max_trade_date}, "
            f"before max_trade_date {max_trade_date}: {source_paths.snapshot_metadata_path}"
        )
    notice_lookback_days = int(metadata.get("notice_lookback_days") or 0)
    if notice_lookback_days < NOTICE_FEATURE_WINDOW_DAYS:
        raise ValueError(
            f"Cached extended source snapshot notice_lookback_days={notice_lookback_days} "
            f"is shorter than required {NOTICE_FEATURE_WINDOW_DAYS}: {source_paths.snapshot_metadata_path}"
        )
    notice_start_date = str(metadata.get("notice_start_date") or "")
    required_notice_start = _required_notice_start_date(earliest_trade_date)
    if not notice_start_date or notice_start_date > required_notice_start:
        raise ValueError(
            f"Cached extended source snapshot notice_start_date={notice_start_date or 'MISSING'} "
            f"is later than required {required_notice_start}: {source_paths.snapshot_metadata_path}"
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
    final_outputs: list[Path] = []
    shared_kline_path = normalized_root / "master" / "shared_kline_panel.csv"
    industry_path = normalized_root / "baostock" / "metadata" / "stock_industry.csv"
    profit_data_path = normalized_root / "baostock" / "financial" / "profit_data.csv"
    performance_express_path = normalized_root / "baostock" / "reports" / "performance_express_report"
    forecast_report_path = normalized_root / "baostock" / "reports" / "forecast_report"
    source_paths = _cached_source_paths(normalized_root)
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_factor_dir = Path(temp_dir) / "factors"
        baseline_outputs: dict[str, Path] = {}
        staged_outputs: list[tuple[Path, Path]] = []

        for spec in UNIVERSE_SPECS:
            final_baseline_output = normalized_root / "factors" / spec.baseline_panel_filename
            staged_baseline_output = temp_factor_dir / spec.baseline_panel_filename
            build_formal_factor_panel(
                kline_path=shared_kline_path,
                industry_path=industry_path,
                membership_path=normalized_root / "universes" / spec.history_filename,
                output_path=staged_baseline_output,
                max_trade_date=max_trade_date,
            )
            final_outputs.append(final_baseline_output)
            staged_outputs.append((staged_baseline_output, final_baseline_output))
            baseline_outputs[spec.universe_id] = staged_baseline_output

        if build_extended_source_tables:
            # 显式重建才调用 AKShare，默认复用已提交快照以保证离线复现。
            extended_sources = build_formal_extended_sources(
                formal_root=normalized_root,
                max_trade_date=max_trade_date,
                panel_paths=list(baseline_outputs.values()),
            )
        else:
            _validate_cached_source_snapshots(
                source_paths,
                max_trade_date=max_trade_date,
                earliest_trade_date=_earliest_trade_date(list(baseline_outputs.values())),
            )
            extended_sources = source_paths

        for spec in UNIVERSE_SPECS:
            final_extended_output = normalized_root / "factors" / spec.extended_panel_filename
            staged_extended_output = temp_factor_dir / spec.extended_panel_filename
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
                output_path=staged_extended_output,
                max_trade_date=max_trade_date,
            )
            final_outputs.append(final_extended_output)
            staged_outputs.append((staged_extended_output, final_extended_output))

        for staged_output, final_output in staged_outputs:
            final_output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(staged_output, final_output)

    return final_outputs


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
