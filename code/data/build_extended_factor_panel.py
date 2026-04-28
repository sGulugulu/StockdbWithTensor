from __future__ import annotations

import argparse
import csv
from datetime import date
from bisect import bisect_right
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from typing import Iterable
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))


def _normalize_cn_a_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if "." in cleaned:
        left, right = cleaned.split(".", 1)
        if left in {"SH", "SZ", "BJ"} and right.isdigit():
            return f"{right}.{left}"
        if right in {"SH", "SZ", "BJ"} and left.isdigit():
            return f"{left}.{right}"
        return cleaned
    if cleaned.startswith(("6", "9")):
        return f"{cleaned}.SH"
    return f"{cleaned}.SZ"


@dataclass(slots=True)
class ProfitSnapshot:
    pub_date: str
    available_date: str | None
    roe_avg: float
    np_margin: float
    gp_margin: float
    eps_ttm: float


@dataclass(slots=True)
class PerformanceExpressSnapshot:
    pub_date: str
    available_date: str | None
    eps_chg_pct: float
    roe_wa: float
    gryoy: float
    opyoy: float


@dataclass(slots=True)
class ForecastSnapshot:
    pub_date: str
    available_date: str | None
    forecast_direction: float
    chg_pct_up: float
    chg_pct_dwn: float


@dataclass(slots=True)
class MarketFeatureRow:
    trade_date: str
    market_return_1d: float
    market_momentum_5d: float
    market_momentum_20d: float
    market_volatility_20d: float
    market_drawdown_20d: float
    market_amount_change_5d: float
    market_amount_zscore_20d: float


@dataclass(slots=True)
class MacroSnapshot:
    pub_date: str
    available_date: str | None
    value: float


@dataclass(slots=True)
class DividendSnapshot:
    pub_date: str
    available_date: str | None
    cash_ratio: float
    bonus_ratio: float
    transfer_ratio: float


@dataclass(slots=True)
class NoticeSnapshot:
    pub_date: str
    available_date: str | None
    keyword_score: float
    title_length: float
    severity_score: float


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    try:
        return float(stripped)
    except ValueError:
        return None


def _rolling_return(prices: list[float], window: int) -> list[float]:
    result: list[float] = []
    for index, price in enumerate(prices):
        if index < window or prices[index - window] == 0:
            result.append(0.0)
            continue
        result.append(price / prices[index - window] - 1.0)
    return result


def _iter_partitioned_csv_rows(root: Path) -> Iterable[dict[str, str]]:
    if root.is_file():
        with root.open("r", encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)
        return

    for path in sorted(root.glob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)


def _next_trade_date_after(reference_date: str, trade_dates: list[str]) -> str | None:
    position = bisect_right(trade_dates, reference_date)
    if position >= len(trade_dates):
        return None
    return trade_dates[position]


def _load_profit_snapshots(path: Path, trade_dates: list[str]) -> dict[str, list[ProfitSnapshot]]:
    snapshots: dict[str, list[ProfitSnapshot]] = {}
    for row in _iter_partitioned_csv_rows(path):
        code = row.get("code")
        pub_date = row.get("pubDate")
        if not code or not pub_date:
            continue
        normalized = _normalize_cn_a_symbol(code)
        snapshots.setdefault(normalized, []).append(
            ProfitSnapshot(
                pub_date=pub_date,
                available_date=_next_trade_date_after(pub_date, trade_dates),
                roe_avg=_to_float(row.get("roeAvg")) or 0.0,
                np_margin=_to_float(row.get("npMargin")) or 0.0,
                gp_margin=_to_float(row.get("gpMargin")) or 0.0,
                eps_ttm=_to_float(row.get("epsTTM")) or 0.0,
            )
        )
    for items in snapshots.values():
        items.sort(key=lambda item: (item.available_date or "9999-99-99", item.pub_date))
    return snapshots


def _load_performance_express_snapshots(path: Path, trade_dates: list[str]) -> dict[str, list[PerformanceExpressSnapshot]]:
    snapshots: dict[str, list[PerformanceExpressSnapshot]] = {}
    for row in _iter_partitioned_csv_rows(path):
        code = row.get("code")
        pub_date = row.get("performanceExpPubDate")
        if not code or not pub_date:
            continue
        normalized = _normalize_cn_a_symbol(code)
        snapshots.setdefault(normalized, []).append(
            PerformanceExpressSnapshot(
                pub_date=pub_date,
                available_date=_next_trade_date_after(pub_date, trade_dates),
                eps_chg_pct=_to_float(row.get("performanceExpressEPSChgPct")) or 0.0,
                roe_wa=_to_float(row.get("performanceExpressROEWa")) or 0.0,
                gryoy=_to_float(row.get("performanceExpressGRYOY")) or 0.0,
                opyoy=_to_float(row.get("performanceExpressOPYOY")) or 0.0,
            )
        )
    for items in snapshots.values():
        items.sort(key=lambda item: (item.available_date or "9999-99-99", item.pub_date))
    return snapshots


def _forecast_direction_score(forecast_type: str | None) -> float:
    if forecast_type is None:
        return 0.0
    label = forecast_type.strip()
    if label in {"预增", "略增", "续盈", "扭亏", "大幅上升"}:
        return 1.0
    if label in {"预减", "略减", "首亏", "续亏", "大幅下降"}:
        return -1.0
    return 0.0


def _load_forecast_snapshots(path: Path, trade_dates: list[str]) -> dict[str, list[ForecastSnapshot]]:
    snapshots: dict[str, list[ForecastSnapshot]] = defaultdict(list)
    for row in _iter_partitioned_csv_rows(path):
        code = row.get("code")
        pub_date = row.get("profitForcastExpPubDate")
        if not code or not pub_date:
            continue
        normalized = _normalize_cn_a_symbol(code)
        snapshots[normalized].append(
            ForecastSnapshot(
                pub_date=pub_date,
                available_date=_next_trade_date_after(pub_date, trade_dates),
                forecast_direction=_forecast_direction_score(row.get("profitForcastType")),
                chg_pct_up=_to_float(row.get("profitForcastChgPctUp")) or 0.0,
                chg_pct_dwn=_to_float(row.get("profitForcastChgPctDwn")) or 0.0,
            )
        )
    for items in snapshots.values():
        items.sort(key=lambda item: (item.available_date or "9999-99-99", item.pub_date))
    return snapshots


def _rolling_std(values: list[float], window: int) -> list[float]:
    result: list[float] = []
    for index in range(len(values)):
        start = max(0, index - window + 1)
        window_slice = values[start : index + 1]
        if len(window_slice) < 2:
            result.append(0.0)
            continue
        mean_value = sum(window_slice) / len(window_slice)
        variance = sum((value - mean_value) ** 2 for value in window_slice) / len(window_slice)
        result.append(variance ** 0.5)
    return result


def _rolling_drawdown(prices: list[float], window: int) -> list[float]:
    result: list[float] = []
    for index, price in enumerate(prices):
        start = max(0, index - window + 1)
        window_peak = max(prices[start : index + 1], default=0.0)
        if window_peak == 0:
            result.append(0.0)
            continue
        result.append(price / window_peak - 1.0)
    return result


def _rolling_zscore(values: list[float], window: int) -> list[float]:
    result: list[float] = []
    for index, value in enumerate(values):
        start = max(0, index - window + 1)
        window_slice = values[start : index + 1]
        if len(window_slice) < 2:
            result.append(0.0)
            continue
        mean_value = sum(window_slice) / len(window_slice)
        variance = sum((item - mean_value) ** 2 for item in window_slice) / len(window_slice)
        std_value = variance ** 0.5
        result.append(0.0 if std_value == 0 else (value - mean_value) / std_value)
    return result


def _load_market_features(path: Path) -> dict[str, MarketFeatureRow]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: row["trade_date"])
    closes = [_to_float(row.get("close")) or 0.0 for row in rows]
    amounts = [_to_float(row.get("amount")) or 0.0 for row in rows]
    market_returns = _rolling_return(closes, 1)
    market_momentum_5d = _rolling_return(closes, 5)
    market_momentum_20d = _rolling_return(closes, 20)
    market_volatility_20d = _rolling_std(market_returns, 20)
    market_drawdown_20d = _rolling_drawdown(closes, 20)
    market_amount_change_5d = _rolling_return(amounts, 5)
    market_amount_zscore_20d = _rolling_zscore(amounts, 20)
    return {
        row["trade_date"]: MarketFeatureRow(
            trade_date=row["trade_date"],
            market_return_1d=market_returns[index],
            market_momentum_5d=market_momentum_5d[index],
            market_momentum_20d=market_momentum_20d[index],
            market_volatility_20d=market_volatility_20d[index],
            market_drawdown_20d=market_drawdown_20d[index],
            market_amount_change_5d=market_amount_change_5d[index],
            market_amount_zscore_20d=market_amount_zscore_20d[index],
        )
        for index, row in enumerate(rows)
    }


def _load_macro_snapshots(path: Path) -> dict[str, list[MacroSnapshot]]:
    snapshots: dict[str, list[MacroSnapshot]] = defaultdict(list)
    for row in _iter_partitioned_csv_rows(path):
        metric_id = row.get("metric_id")
        available_date = row.get("available_date")
        pub_date = row.get("pub_date")
        if not metric_id or not available_date or not pub_date:
            continue
        snapshots[metric_id].append(
            MacroSnapshot(
                pub_date=pub_date,
                available_date=available_date,
                value=_to_float(row.get("value")) or 0.0,
            )
        )
    for items in snapshots.values():
        items.sort(key=lambda item: (item.available_date or "9999-99-99", item.pub_date))
    return snapshots


def _load_dividend_snapshots(path: Path) -> dict[str, list[DividendSnapshot]]:
    snapshots: dict[str, list[DividendSnapshot]] = defaultdict(list)
    for row in _iter_partitioned_csv_rows(path):
        stock_code = row.get("stock_code")
        available_date = row.get("available_date")
        pub_date = row.get("pub_date")
        if not stock_code or not available_date or not pub_date:
            continue
        snapshots[_normalize_cn_a_symbol(stock_code)].append(
            DividendSnapshot(
                pub_date=pub_date,
                available_date=available_date,
                cash_ratio=_to_float(row.get("cash_ratio")) or 0.0,
                bonus_ratio=_to_float(row.get("bonus_ratio")) or 0.0,
                transfer_ratio=_to_float(row.get("transfer_ratio")) or 0.0,
            )
        )
    for items in snapshots.values():
        items.sort(key=lambda item: (item.available_date or "9999-99-99", item.pub_date))
    return snapshots


def _load_notice_snapshots(path: Path, *, major_event: bool) -> dict[str, list[NoticeSnapshot]]:
    snapshots: dict[str, list[NoticeSnapshot]] = defaultdict(list)
    for row in _iter_partitioned_csv_rows(path):
        stock_code = row.get("stock_code")
        available_date = row.get("available_date")
        pub_date = row.get("pub_date")
        if not stock_code or not available_date or not pub_date:
            continue
        snapshots[_normalize_cn_a_symbol(stock_code)].append(
            NoticeSnapshot(
                pub_date=pub_date,
                available_date=available_date,
                keyword_score=_to_float(row.get("keyword_score")) or 0.0,
                title_length=_to_float(row.get("title_length")) or 0.0,
                severity_score=(_to_float(row.get("severity_score")) or 0.0) if major_event else 0.0,
            )
        )
    for items in snapshots.values():
        items.sort(key=lambda item: (item.available_date or "9999-99-99", item.pub_date))
    return snapshots


def _latest_snapshot(snapshots: list, trade_date: str):
    if not snapshots:
        return None
    available_dates = [item.available_date or "9999-99-99" for item in snapshots]
    position = bisect_right(available_dates, trade_date) - 1
    while position >= 0:
        candidate = snapshots[position]
        if candidate.available_date is not None and candidate.available_date <= trade_date:
            return candidate
        position -= 1
    return None


def _window_snapshots(snapshots: list, trade_date: str, *, window_days: int) -> list:
    if not snapshots:
        return []
    result: list = []
    trade_day = date.fromisoformat(trade_date)
    for snapshot in snapshots:
        if snapshot.available_date is None or snapshot.available_date > trade_date:
            continue
        try:
            available_day = date.fromisoformat(snapshot.available_date)
        except ValueError:
            continue
        if (trade_day - available_day).days <= window_days:
            result.append(snapshot)
    return result


def _latest_from_window(window: list):
    if not window:
        return None
    return max(window, key=lambda item: (item.available_date or "", item.pub_date))


def _days_since(pub_date: str | None, trade_date: str) -> int:
    if not pub_date:
        return 0
    try:
        return max((date.fromisoformat(trade_date) - date.fromisoformat(pub_date)).days, 0)
    except ValueError:
        return 0


def _snapshot_age_days(snapshot, trade_date: str) -> int:
    if snapshot is None:
        return 0
    return _days_since(snapshot.available_date or snapshot.pub_date, trade_date)


def _forecast_midpoint(snapshot: ForecastSnapshot | None) -> float:
    if snapshot is None:
        return 0.0
    return (snapshot.chg_pct_up + snapshot.chg_pct_dwn) / 2.0


def _forecast_width(snapshot: ForecastSnapshot | None) -> float:
    if snapshot is None:
        return 0.0
    return abs(snapshot.chg_pct_up - snapshot.chg_pct_dwn)


def _macro_proxy_risk_score(market_feature: MarketFeatureRow) -> float:
    return market_feature.market_volatility_20d + abs(min(market_feature.market_drawdown_20d, 0.0))


def _macro_proxy_liquidity_score(market_feature: MarketFeatureRow) -> float:
    return market_feature.market_amount_zscore_20d + market_feature.market_amount_change_5d


def _event_positive_flag(
    performance_snapshot: PerformanceExpressSnapshot | None,
    forecast_snapshot: ForecastSnapshot | None,
) -> int:
    if forecast_snapshot is not None and forecast_snapshot.forecast_direction > 0:
        return 1
    if performance_snapshot is not None and performance_snapshot.eps_chg_pct > 0:
        return 1
    return 0


def _event_negative_flag(
    performance_snapshot: PerformanceExpressSnapshot | None,
    forecast_snapshot: ForecastSnapshot | None,
) -> int:
    if forecast_snapshot is not None and forecast_snapshot.forecast_direction < 0:
        return 1
    if performance_snapshot is not None and performance_snapshot.eps_chg_pct < 0:
        return 1
    return 0


def _event_age_decay_score(
    performance_snapshot: PerformanceExpressSnapshot | None,
    forecast_snapshot: ForecastSnapshot | None,
    trade_date: str,
) -> float:
    score = 0.0
    if performance_snapshot is not None:
        score += 1.0 / (1.0 + _snapshot_age_days(performance_snapshot, trade_date))
    if forecast_snapshot is not None:
        score += 1.0 / (1.0 + _snapshot_age_days(forecast_snapshot, trade_date))
    return score


def _macro_metric_value(snapshots_by_metric: dict[str, list[MacroSnapshot]], metric_id: str, trade_date: str) -> float:
    snapshot = _latest_snapshot(snapshots_by_metric.get(metric_id, []), trade_date)
    return 0.0 if snapshot is None else snapshot.value


def _dividend_flag(snapshot: DividendSnapshot | None) -> int:
    if snapshot is None:
        return 0
    return 1 if snapshot.cash_ratio > 0 or snapshot.bonus_ratio > 0 or snapshot.transfer_ratio > 0 else 0


def build_extended_factor_panel(
    *,
    base_panel_path: Path,
    profit_data_path: Path,
    performance_express_path: Path,
    forecast_report_path: Path,
    market_index_path: Path,
    macro_interest_rate_path: Path,
    macro_monthly_path: Path,
    dividend_event_path: Path,
    major_event_notice_path: Path,
    announcement_text_path: Path,
    output_path: Path,
    max_trade_date: str | None = None,
) -> None:
    with base_panel_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    trade_dates = sorted({row["trade_date"] for row in rows})

    profit_snapshots = _load_profit_snapshots(profit_data_path, trade_dates)
    performance_snapshots = _load_performance_express_snapshots(performance_express_path, trade_dates)
    forecast_snapshots = _load_forecast_snapshots(forecast_report_path, trade_dates)
    market_features = _load_market_features(market_index_path)
    macro_interest_snapshots = _load_macro_snapshots(macro_interest_rate_path)
    macro_monthly_snapshots = _load_macro_snapshots(macro_monthly_path)
    dividend_snapshots = _load_dividend_snapshots(dividend_event_path)
    major_event_snapshots = _load_notice_snapshots(major_event_notice_path, major_event=True)
    announcement_snapshots = _load_notice_snapshots(announcement_text_path, major_event=False)

    extended_rows: list[dict[str, str | float]] = []
    for row in rows:
        if max_trade_date is not None and row["trade_date"] > max_trade_date:
            continue
        stock_code = row["stock_code"]
        trade_date = row["trade_date"]
        profit_snapshot = _latest_snapshot(profit_snapshots.get(stock_code, []), trade_date)
        performance_snapshot = _latest_snapshot(performance_snapshots.get(stock_code, []), trade_date)
        forecast_snapshot = _latest_snapshot(forecast_snapshots.get(stock_code, []), trade_date)
        dividend_snapshot = _latest_snapshot(dividend_snapshots.get(stock_code, []), trade_date)
        market_feature = market_features.get(
            trade_date,
            MarketFeatureRow(
                trade_date=trade_date,
                market_return_1d=0.0,
                market_momentum_5d=0.0,
                market_momentum_20d=0.0,
                market_volatility_20d=0.0,
                market_drawdown_20d=0.0,
                market_amount_change_5d=0.0,
                market_amount_zscore_20d=0.0,
            ),
        )
        forecast_midpoint = _forecast_midpoint(forecast_snapshot)
        forecast_width = _forecast_width(forecast_snapshot)
        stock_major_events = major_event_snapshots.get(stock_code, [])
        major_event_window = _window_snapshots(stock_major_events, trade_date, window_days=30)
        recent_major_event = _latest_from_window(major_event_window)
        stock_announcements = announcement_snapshots.get(stock_code, [])
        announcement_window = _window_snapshots(stock_announcements, trade_date, window_days=30)

        extended_rows.append(
            {
                **row,
                "market_return_1d": market_feature.market_return_1d,
                "market_momentum_5d": market_feature.market_momentum_5d,
                "market_momentum_20d": market_feature.market_momentum_20d,
                "market_volatility_20d": market_feature.market_volatility_20d,
                "market_drawdown_20d": market_feature.market_drawdown_20d,
                "market_amount_change_5d": market_feature.market_amount_change_5d,
                "market_amount_zscore_20d": market_feature.market_amount_zscore_20d,
                "macro_proxy_risk_score": _macro_proxy_risk_score(market_feature),
                "macro_proxy_liquidity_score": _macro_proxy_liquidity_score(market_feature),
                "macro_policy_rate": _macro_metric_value(macro_interest_snapshots, "policy_rate_current", trade_date),
                "macro_lpr_1y": _macro_metric_value(macro_interest_snapshots, "lpr_1y", trade_date),
                "macro_lpr_5y": _macro_metric_value(macro_interest_snapshots, "lpr_5y", trade_date),
                "macro_cpi_mom": _macro_metric_value(macro_monthly_snapshots, "cpi_mom", trade_date),
                "macro_m2_yoy": _macro_metric_value(macro_monthly_snapshots, "m2_yoy", trade_date),
                "macro_industrial_production_yoy": _macro_metric_value(macro_monthly_snapshots, "industrial_production_yoy", trade_date),
                "macro_exports_yoy": _macro_metric_value(macro_monthly_snapshots, "exports_yoy", trade_date),
                "macro_imports_yoy": _macro_metric_value(macro_monthly_snapshots, "imports_yoy", trade_date),
                "pit_roe_avg": 0.0 if profit_snapshot is None else profit_snapshot.roe_avg,
                "pit_np_margin": 0.0 if profit_snapshot is None else profit_snapshot.np_margin,
                "pit_gp_margin": 0.0 if profit_snapshot is None else profit_snapshot.gp_margin,
                "pit_eps_ttm": 0.0 if profit_snapshot is None else profit_snapshot.eps_ttm,
                "pit_data_age_days": _snapshot_age_days(profit_snapshot, trade_date),
                "dividend_cash_ratio": 0.0 if dividend_snapshot is None else dividend_snapshot.cash_ratio,
                "dividend_bonus_ratio": 0.0 if dividend_snapshot is None else dividend_snapshot.bonus_ratio,
                "dividend_transfer_ratio": 0.0 if dividend_snapshot is None else dividend_snapshot.transfer_ratio,
                "dividend_age_days": _snapshot_age_days(dividend_snapshot, trade_date),
                "dividend_flag": _dividend_flag(dividend_snapshot),
                "perf_express_eps_chg_pct": 0.0 if performance_snapshot is None else performance_snapshot.eps_chg_pct,
                "perf_express_roe_wa": 0.0 if performance_snapshot is None else performance_snapshot.roe_wa,
                "perf_express_gryoy": 0.0 if performance_snapshot is None else performance_snapshot.gryoy,
                "perf_express_opyoy": 0.0 if performance_snapshot is None else performance_snapshot.opyoy,
                "perf_express_age_days": _snapshot_age_days(performance_snapshot, trade_date),
                "perf_express_flag": 0 if performance_snapshot is None else 1,
                "forecast_direction": 0.0 if forecast_snapshot is None else forecast_snapshot.forecast_direction,
                "forecast_chg_pct_up": 0.0 if forecast_snapshot is None else forecast_snapshot.chg_pct_up,
                "forecast_chg_pct_dwn": 0.0 if forecast_snapshot is None else forecast_snapshot.chg_pct_dwn,
                "forecast_change_midpoint": forecast_midpoint,
                "forecast_change_width": forecast_width,
                "forecast_age_days": _snapshot_age_days(forecast_snapshot, trade_date),
                "event_positive_flag": _event_positive_flag(performance_snapshot, forecast_snapshot),
                "event_negative_flag": _event_negative_flag(performance_snapshot, forecast_snapshot),
                "event_uncertainty_score": forecast_width,
                "event_age_decay_score": _event_age_decay_score(performance_snapshot, forecast_snapshot, trade_date),
                "event_intensity_score": abs(forecast_midpoint)
                + (0.0 if performance_snapshot is None else abs(performance_snapshot.eps_chg_pct)),
                "major_event_count_30d": len(major_event_window),
                "major_event_severity_score_30d": sum(snapshot.severity_score for snapshot in major_event_window),
                "major_event_age_days": _snapshot_age_days(recent_major_event, trade_date),
                "major_event_flag": 1 if major_event_window else 0,
                "announcement_count_30d": len(announcement_window),
                "announcement_keyword_score_30d": sum(snapshot.keyword_score for snapshot in announcement_window),
                "announcement_title_length_mean_30d": 0.0
                if not announcement_window
                else sum(snapshot.title_length for snapshot in announcement_window) / len(announcement_window),
                "announcement_flag": 1 if announcement_window else 0,
                "forecast_flag": 0 if forecast_snapshot is None else 1,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(extended_rows[0].keys()) if extended_rows else [])
        if extended_rows:
            writer.writeheader()
            writer.writerows(extended_rows)
        else:
            handle.write("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build an extended formal factor panel with PIT and event features.")
    parser.add_argument("--base-panel-path", type=Path, required=True)
    parser.add_argument("--profit-data-path", type=Path, required=True)
    parser.add_argument("--performance-express-path", type=Path, required=True)
    parser.add_argument("--forecast-report-path", type=Path, required=True)
    parser.add_argument("--market-index-path", type=Path, required=True)
    parser.add_argument("--macro-interest-rate-path", type=Path, required=True)
    parser.add_argument("--macro-monthly-path", type=Path, required=True)
    parser.add_argument("--dividend-event-path", type=Path, required=True)
    parser.add_argument("--major-event-notice-path", type=Path, required=True)
    parser.add_argument("--announcement-text-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--max-trade-date", type=str, default=None)
    args = parser.parse_args()

    build_extended_factor_panel(
        base_panel_path=args.base_panel_path,
        profit_data_path=args.profit_data_path,
        performance_express_path=args.performance_express_path,
        forecast_report_path=args.forecast_report_path,
        market_index_path=args.market_index_path,
        macro_interest_rate_path=args.macro_interest_rate_path,
        macro_monthly_path=args.macro_monthly_path,
        dividend_event_path=args.dividend_event_path,
        major_event_notice_path=args.major_event_notice_path,
        announcement_text_path=args.announcement_text_path,
        output_path=args.output_path,
        max_trade_date=args.max_trade_date,
    )


if __name__ == "__main__":
    main()
