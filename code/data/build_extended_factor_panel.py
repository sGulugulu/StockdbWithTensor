from __future__ import annotations

import argparse
import csv
from bisect import bisect_right
from dataclasses import dataclass
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
    roe_avg: float
    np_margin: float
    gp_margin: float
    eps_ttm: float


@dataclass(slots=True)
class PerformanceExpressSnapshot:
    pub_date: str
    eps_chg_pct: float
    roe_wa: float
    gryoy: float
    opyoy: float


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


def _iter_partitioned_csv_rows(root: Path) -> Iterable[dict[str, str]]:
    if root.is_file():
        with root.open("r", encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)
        return

    for path in sorted(root.glob("*.csv")):
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            yield from csv.DictReader(handle)


def _load_profit_snapshots(path: Path) -> dict[str, list[ProfitSnapshot]]:
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
                roe_avg=_to_float(row.get("roeAvg")) or 0.0,
                np_margin=_to_float(row.get("npMargin")) or 0.0,
                gp_margin=_to_float(row.get("gpMargin")) or 0.0,
                eps_ttm=_to_float(row.get("epsTTM")) or 0.0,
            )
        )
    for items in snapshots.values():
        items.sort(key=lambda item: item.pub_date)
    return snapshots


def _load_performance_express_snapshots(path: Path) -> dict[str, list[PerformanceExpressSnapshot]]:
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
                eps_chg_pct=_to_float(row.get("performanceExpressEPSChgPct")) or 0.0,
                roe_wa=_to_float(row.get("performanceExpressROEWa")) or 0.0,
                gryoy=_to_float(row.get("performanceExpressGRYOY")) or 0.0,
                opyoy=_to_float(row.get("performanceExpressOPYOY")) or 0.0,
            )
        )
    for items in snapshots.values():
        items.sort(key=lambda item: item.pub_date)
    return snapshots


def _latest_snapshot(snapshots: list, trade_date: str):
    if not snapshots:
        return None
    pub_dates = [item.pub_date for item in snapshots]
    position = bisect_right(pub_dates, trade_date) - 1
    if position < 0:
        return None
    return snapshots[position]


def _days_between(left: str, right: str) -> int:
    return int((Path(right.replace("-", "")).stem != "")) if False else 0


def build_extended_factor_panel(
    *,
    base_panel_path: Path,
    profit_data_path: Path,
    performance_express_path: Path,
    output_path: Path,
    max_trade_date: str | None = None,
) -> None:
    profit_snapshots = _load_profit_snapshots(profit_data_path)
    performance_snapshots = _load_performance_express_snapshots(performance_express_path)

    with base_panel_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    extended_rows: list[dict[str, str | float]] = []
    for row in rows:
        if max_trade_date is not None and row["trade_date"] > max_trade_date:
            continue
        stock_code = row["stock_code"]
        trade_date = row["trade_date"]
        profit_snapshot = _latest_snapshot(profit_snapshots.get(stock_code, []), trade_date)
        performance_snapshot = _latest_snapshot(performance_snapshots.get(stock_code, []), trade_date)

        extended_rows.append(
            {
                **row,
                "pit_roe_avg": 0.0 if profit_snapshot is None else profit_snapshot.roe_avg,
                "pit_np_margin": 0.0 if profit_snapshot is None else profit_snapshot.np_margin,
                "pit_gp_margin": 0.0 if profit_snapshot is None else profit_snapshot.gp_margin,
                "pit_eps_ttm": 0.0 if profit_snapshot is None else profit_snapshot.eps_ttm,
                "perf_express_eps_chg_pct": 0.0 if performance_snapshot is None else performance_snapshot.eps_chg_pct,
                "perf_express_roe_wa": 0.0 if performance_snapshot is None else performance_snapshot.roe_wa,
                "perf_express_gryoy": 0.0 if performance_snapshot is None else performance_snapshot.gryoy,
                "perf_express_opyoy": 0.0 if performance_snapshot is None else performance_snapshot.opyoy,
                "perf_express_flag": 0 if performance_snapshot is None else 1,
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
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--max-trade-date", type=str, default=None)
    args = parser.parse_args()

    build_extended_factor_panel(
        base_panel_path=args.base_panel_path,
        profit_data_path=args.profit_data_path,
        performance_express_path=args.performance_express_path,
        output_path=args.output_path,
        max_trade_date=args.max_trade_date,
    )


if __name__ == "__main__":
    main()
