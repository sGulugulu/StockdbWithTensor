from __future__ import annotations

import argparse
import csv
from bisect import bisect_right
from dataclasses import dataclass
from collections import defaultdict
from pathlib import Path
from typing import Iterable
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from stock_tensor.market import SymbolNormalizer


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
    market_volatility_20d: float
    market_amount_change_5d: float


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
    normalizer = SymbolNormalizer("cn_a")
    snapshots: dict[str, list[ProfitSnapshot]] = {}
    for row in _iter_partitioned_csv_rows(path):
        code = row.get("code")
        pub_date = row.get("pubDate")
        if not code or not pub_date:
            continue
        normalized = normalizer.normalize(code)
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
    normalizer = SymbolNormalizer("cn_a")
    snapshots: dict[str, list[PerformanceExpressSnapshot]] = {}
    for row in _iter_partitioned_csv_rows(path):
        code = row.get("code")
        pub_date = row.get("performanceExpPubDate")
        if not code or not pub_date:
            continue
        normalized = normalizer.normalize(code)
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
    normalizer = SymbolNormalizer("cn_a")
    snapshots: dict[str, list[ForecastSnapshot]] = defaultdict(list)
    for row in _iter_partitioned_csv_rows(path):
        code = row.get("code")
        pub_date = row.get("profitForcastExpPubDate")
        if not code or not pub_date:
            continue
        normalized = normalizer.normalize(code)
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


def _load_market_features(path: Path) -> dict[str, MarketFeatureRow]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: row["trade_date"])
    closes = [_to_float(row.get("close")) or 0.0 for row in rows]
    amounts = [_to_float(row.get("amount")) or 0.0 for row in rows]
    market_returns = _rolling_return(closes, 1)
    market_momentum_5d = _rolling_return(closes, 5)
    market_volatility_20d = _rolling_std(market_returns, 20)
    market_amount_change_5d = _rolling_return(amounts, 5)
    return {
        row["trade_date"]: MarketFeatureRow(
            trade_date=row["trade_date"],
            market_return_1d=market_returns[index],
            market_momentum_5d=market_momentum_5d[index],
            market_volatility_20d=market_volatility_20d[index],
            market_amount_change_5d=market_amount_change_5d[index],
        )
        for index, row in enumerate(rows)
    }


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


def build_extended_factor_panel(
    *,
    base_panel_path: Path,
    profit_data_path: Path,
    performance_express_path: Path,
    forecast_report_path: Path,
    market_index_path: Path,
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

    extended_rows: list[dict[str, str | float]] = []
    for row in rows:
        if max_trade_date is not None and row["trade_date"] > max_trade_date:
            continue
        stock_code = row["stock_code"]
        trade_date = row["trade_date"]
        profit_snapshot = _latest_snapshot(profit_snapshots.get(stock_code, []), trade_date)
        performance_snapshot = _latest_snapshot(performance_snapshots.get(stock_code, []), trade_date)
        forecast_snapshot = _latest_snapshot(forecast_snapshots.get(stock_code, []), trade_date)
        market_feature = market_features.get(
            trade_date,
            MarketFeatureRow(
                trade_date=trade_date,
                market_return_1d=0.0,
                market_momentum_5d=0.0,
                market_volatility_20d=0.0,
                market_amount_change_5d=0.0,
            ),
        )

        extended_rows.append(
            {
                **row,
                "market_return_1d": market_feature.market_return_1d,
                "market_momentum_5d": market_feature.market_momentum_5d,
                "market_volatility_20d": market_feature.market_volatility_20d,
                "market_amount_change_5d": market_feature.market_amount_change_5d,
                "pit_roe_avg": 0.0 if profit_snapshot is None else profit_snapshot.roe_avg,
                "pit_np_margin": 0.0 if profit_snapshot is None else profit_snapshot.np_margin,
                "pit_gp_margin": 0.0 if profit_snapshot is None else profit_snapshot.gp_margin,
                "pit_eps_ttm": 0.0 if profit_snapshot is None else profit_snapshot.eps_ttm,
                "perf_express_eps_chg_pct": 0.0 if performance_snapshot is None else performance_snapshot.eps_chg_pct,
                "perf_express_roe_wa": 0.0 if performance_snapshot is None else performance_snapshot.roe_wa,
                "perf_express_gryoy": 0.0 if performance_snapshot is None else performance_snapshot.gryoy,
                "perf_express_opyoy": 0.0 if performance_snapshot is None else performance_snapshot.opyoy,
                "perf_express_flag": 0 if performance_snapshot is None else 1,
                "forecast_direction": 0.0 if forecast_snapshot is None else forecast_snapshot.forecast_direction,
                "forecast_chg_pct_up": 0.0 if forecast_snapshot is None else forecast_snapshot.chg_pct_up,
                "forecast_chg_pct_dwn": 0.0 if forecast_snapshot is None else forecast_snapshot.chg_pct_dwn,
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
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--max-trade-date", type=str, default=None)
    args = parser.parse_args()

    build_extended_factor_panel(
        base_panel_path=args.base_panel_path,
        profit_data_path=args.profit_data_path,
        performance_express_path=args.performance_express_path,
        forecast_report_path=args.forecast_report_path,
        market_index_path=args.market_index_path,
        output_path=args.output_path,
        max_trade_date=args.max_trade_date,
    )


if __name__ == "__main__":
    main()
