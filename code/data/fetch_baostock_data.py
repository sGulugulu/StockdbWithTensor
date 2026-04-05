from __future__ import annotations

import argparse
import csv
import json
import time
from bisect import bisect_left
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from stock_tensor.market import SymbolNormalizer
from data.year_windows import iter_year_date_ranges

try:
    import baostock as bs
except ImportError:
    bs = None


def _require_baostock() -> object:
    if bs is None:
        raise ModuleNotFoundError(
            "baostock is required for live data fetching. Install it in the active environment first."
        )
    return bs


def _index_queries() -> dict[str, Callable[[str], object]]:
    client = _require_baostock()
    return {
        "hs300": client.query_hs300_stocks,
        "sz50": client.query_sz50_stocks,
        "zz500": client.query_zz500_stocks,
    }


def _financial_queries() -> dict[str, Callable[..., object]]:
    client = _require_baostock()
    return {
        "profit_data": client.query_profit_data,
        "operation_data": client.query_operation_data,
        "growth_data": client.query_growth_data,
        "balance_data": client.query_balance_data,
        "cash_flow_data": client.query_cash_flow_data,
        "dupont_data": client.query_dupont_data,
    }


def _report_queries() -> dict[str, Callable[..., object]]:
    client = _require_baostock()
    return {
        "performance_express_report": client.query_performance_express_report,
        "forecast_report": client.query_forecast_report,
    }


def _log(message: str) -> None:
    print(message, flush=True)


@dataclass(slots=True)
class FetchStats:
    index_snapshot_rows: int = 0
    index_change_rows: int = 0
    unique_codes: int = 0
    stock_basic_rows: int = 0
    stock_industry_rows: int = 0
    all_a_history_rows: int = 0
    financial_rows: int = 0
    report_rows: int = 0


def _empty_stats() -> dict[str, int]:
    return {
        "index_snapshot_rows": 0,
        "index_change_rows": 0,
        "unique_codes": 0,
        "stock_basic_rows": 0,
        "stock_industry_rows": 0,
        "all_a_history_rows": 0,
        "financial_rows": 0,
        "report_rows": 0,
    }


def _today_iso() -> str:
    return date.today().isoformat()


def _query_to_rows(resultset: object) -> list[dict[str, str]]:
    if getattr(resultset, "error_code", None) != "0":
        raise RuntimeError(
            f"baostock query failed: {getattr(resultset, 'error_code', '?')} "
            f"{getattr(resultset, 'error_msg', '')}"
        )
    rows: list[dict[str, str]] = []
    fields = list(getattr(resultset, "fields", []))
    while resultset.next():
        rows.append(dict(zip(fields, resultset.get_row_data(), strict=False)))
    return rows


def _write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _append_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = list(rows[0].keys())
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def _normalize_index_date(rows: list[dict[str, str]], snapshot_date: str, index_id: str) -> list[dict[str, str]]:
    normalized: list[dict[str, str]] = []
    for row in rows:
        normalized.append(
            {
                "index_id": index_id,
                "snapshot_date": snapshot_date,
                "effective_date": row.get("updateDate", ""),
                "code": row.get("code", ""),
                "code_name": row.get("code_name", ""),
            }
        )
    return normalized


def _derive_change_rows(snapshot_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    if not snapshot_rows:
        return []

    grouped_by_date: dict[str, dict[str, str]] = {}
    for row in snapshot_rows:
        grouped_by_date.setdefault(row["snapshot_date"], {})
        grouped_by_date[row["snapshot_date"]][row["code"]] = row["code_name"]

    dates = sorted(grouped_by_date)
    change_rows: list[dict[str, str]] = []
    previous_codes: set[str] = set()
    previous_date = ""
    index_id = snapshot_rows[0]["index_id"]

    for current_date in dates:
        current_map = grouped_by_date[current_date]
        current_codes = set(current_map)

        for code in sorted(current_codes - previous_codes):
            change_rows.append(
                {
                    "index_id": index_id,
                    "change_date": current_date,
                    "previous_snapshot_date": previous_date,
                    "change_type": "add",
                    "code": code,
                    "code_name": current_map[code],
                }
            )
        for code in sorted(previous_codes - current_codes):
            change_rows.append(
                {
                    "index_id": index_id,
                    "change_date": current_date,
                    "previous_snapshot_date": previous_date,
                    "change_type": "remove",
                    "code": code,
                    "code_name": grouped_by_date[previous_date][code] if previous_date else "",
                }
            )
        previous_codes = current_codes
        previous_date = current_date

    return change_rows


def _iter_quarters(start_year: int, end_year: int) -> list[tuple[int, int]]:
    pairs: list[tuple[int, int]] = []
    for year in range(start_year, end_year + 1):
        for quarter in (1, 2, 3, 4):
            pairs.append((year, quarter))
    return pairs


def _is_cn_a_equity_row(row: dict[str, str]) -> bool:
    code = row.get("code", "").strip().lower()
    stock_type = row.get("type", "").strip()
    if stock_type and stock_type != "1":
        return False
    if code.startswith("sh.60") or code.startswith("sh.68"):
        return True
    if code.startswith("sz.000") or code.startswith("sz.001") or code.startswith("sz.002"):
        return True
    if code.startswith("sz.003") or code.startswith("sz.300"):
        return True
    return False


def build_all_a_tradable_history_rows(
    stock_basic_rows: list[dict[str, str]],
    *,
    horizon_date: str,
) -> list[dict[str, str]]:
    normalizer = SymbolNormalizer("cn_a")
    history_rows: list[dict[str, str]] = []
    for row in stock_basic_rows:
        if not _is_cn_a_equity_row(row):
            continue
        ipo_date = row.get("ipoDate", "").strip()
        if not ipo_date:
            continue
        out_date = row.get("outDate", "").strip() or horizon_date
        history_rows.append(
            {
                "market_id": "cn_a",
                "universe_id": "ALL_A",
                "stock_code": normalizer.normalize(row["code"]),
                "start_date": ipo_date,
                "end_date": out_date,
            }
        )
    history_rows.sort(key=lambda item: (item["stock_code"], item["start_date"]))
    return history_rows


def _to_baostock_code(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if "." not in cleaned:
        return cleaned.lower()
    left, right = cleaned.split(".", 1)
    if left in {"SH", "SZ", "BJ"} and right.isdigit():
        return f"{left.lower()}.{right}"
    if right in {"SH", "SZ", "BJ"} and left.isdigit():
        return f"{right.lower()}.{left}"
    return cleaned.lower()


def _load_stock_basic_rows_from_output(output_root: Path) -> list[dict[str, str]]:
    path = output_root / "metadata" / "stock_basic.csv"
    if not path.exists():
        raise FileNotFoundError(f"stock_basic.csv not found: {path}")
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _all_a_codes_from_stock_basic_rows(stock_basic_rows: list[dict[str, str]]) -> list[str]:
    codes = {
        _to_baostock_code(row["code"])
        for row in stock_basic_rows
        if row.get("code") and _is_cn_a_equity_row(row)
    }
    return sorted(codes)


def _resolve_stage2_codes(
    *,
    stage2_scope: str,
    selected_codes: list[str],
    stock_basic_rows: list[dict[str, str]] | None,
    output_root: Path,
) -> list[str]:
    if stage2_scope == "selected":
        return selected_codes
    effective_rows = stock_basic_rows if stock_basic_rows is not None else _load_stock_basic_rows_from_output(output_root)
    return _all_a_codes_from_stock_basic_rows(effective_rows)


def _fetch_trade_dates(start_date: str, end_date: str) -> list[str]:
    client = _require_baostock()
    rows = _query_to_rows(client.query_trade_dates(start_date=start_date, end_date=end_date))
    return [row["calendar_date"] for row in rows if row.get("is_trading_day") == "1"]


def _fetch_index_snapshots(
    *,
    index_id: str,
    trade_dates: list[str],
    sleep_seconds: float,
) -> list[dict[str, str]]:
    query = _index_queries()[index_id]
    snapshot_cache: dict[str, list[dict[str, str]]] = {}
    effective_date_cache: dict[str, str] = {}

    def get_snapshot(query_date: str) -> list[dict[str, str]]:
        if query_date not in snapshot_cache:
            raw_rows = _query_to_rows(query(query_date))
            snapshot_cache[query_date] = _normalize_index_date(raw_rows, query_date, index_id)
            effective_date_cache[query_date] = (
                snapshot_cache[query_date][0]["effective_date"] if snapshot_cache[query_date] else ""
            )
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
        return snapshot_cache[query_date]

    if not trade_dates:
        return []

    snapshots: list[dict[str, str]] = []
    seen_snapshot_dates: set[str] = set()
    first_trade_date = trade_dates[0]
    current_query_date = trade_dates[-1]
    step_count = 0

    while True:
        rows = get_snapshot(current_query_date)
        effective_date = effective_date_cache[current_query_date]
        snapshot_date = effective_date if effective_date >= first_trade_date else first_trade_date
        if snapshot_date not in seen_snapshot_dates:
            for row in rows:
                snapshots.append({**row, "snapshot_date": snapshot_date})
            seen_snapshot_dates.add(snapshot_date)
            step_count += 1
            if step_count == 1 or step_count % 10 == 0:
                _log(
                    f"[{index_id}] snapshot #{step_count}: "
                    f"query_date={current_query_date}, effective_date={effective_date}, snapshot_date={snapshot_date}"
                )

        if effective_date <= first_trade_date:
            break

        pos = bisect_left(trade_dates, effective_date)
        previous_idx = pos - 1
        if previous_idx < 0:
            break
        current_query_date = trade_dates[previous_idx]

    start_rows = get_snapshot(first_trade_date)
    if first_trade_date not in seen_snapshot_dates:
        for row in start_rows:
            snapshots.append({**row, "snapshot_date": first_trade_date})

    snapshots.sort(key=lambda row: (row["snapshot_date"], row["code"]))
    return snapshots


def _fetch_stock_basic(codes: set[str] | None = None) -> list[dict[str, str]]:
    client = _require_baostock()
    rows = _query_to_rows(client.query_stock_basic())
    filtered = rows if codes is None else [row for row in rows if row.get("code") in codes]
    filtered.sort(key=lambda row: row["code"])
    return filtered


def _fetch_stock_industry(codes: set[str] | None, as_of_date: str) -> list[dict[str, str]]:
    client = _require_baostock()
    rows = _query_to_rows(client.query_stock_industry(date=as_of_date))
    filtered = rows if codes is None else [row for row in rows if row.get("code") in codes]
    filtered.sort(key=lambda row: row["code"])
    return filtered


def _load_selected_codes_from_output(output_root: Path) -> list[str]:
    path = output_root / "metadata" / "selected_codes.csv"
    if not path.exists():
        raise FileNotFoundError(f"Selected codes file not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [row["code"] for row in reader if row.get("code")]


def _load_selected_codes_from_file(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Selected codes file not found: {path}")
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [row["code"] for row in reader if row.get("code")]


def _load_progress(path: Path) -> dict[str, list[str]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_progress(path: Path, payload: dict[str, list[str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _fetch_financial_rows(
    *,
    query_name: str,
    codes: list[str],
    quarter_pairs: list[tuple[int, int]],
    sleep_seconds: float,
) -> list[dict[str, str]]:
    query = _financial_queries()[query_name]
    rows: list[dict[str, str]] = []
    for code in codes:
        for year, quarter in quarter_pairs:
            query_rows = _query_to_rows(query(code=code, year=year, quarter=quarter))
            for row in query_rows:
                row["dataset"] = query_name
                row["query_year"] = str(year)
                row["query_quarter"] = str(quarter)
            rows.extend(query_rows)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
    return rows


def _fetch_report_rows(
    *,
    query_name: str,
    codes: list[str],
    start_date: str,
    end_date: str,
    sleep_seconds: float,
) -> list[dict[str, str]]:
    query = _report_queries()[query_name]
    rows: list[dict[str, str]] = []
    date_windows = iter_year_date_ranges(start_date, end_date)
    for code in codes:
        for window_start, window_end, year_label in date_windows:
            query_rows = _query_to_rows(query(code=code, start_date=window_start, end_date=window_end))
            for row in query_rows:
                row["dataset"] = query_name
                row["query_year"] = str(year_label)
            rows.extend(query_rows)
            if sleep_seconds > 0:
                time.sleep(sleep_seconds)
    return rows


def fetch_baostock_bundle(
    *,
    output_root: Path,
    start_date: str,
    end_date: str,
    indices: list[str],
    financial_start_year: int,
    financial_end_year: int,
    max_codes: int | None,
    sleep_seconds: float,
    skip_financials: bool,
    skip_reports: bool,
    skip_index_memberships: bool,
    skip_metadata: bool,
    metadata_scope: str,
    stage2_scope: str,
    all_a_history_output: Path | None,
    selected_codes_file: Path | None,
    resume: bool,
) -> FetchStats:
    output_root.mkdir(parents=True, exist_ok=True)
    if all_a_history_output is not None and metadata_scope != "all_a":
        raise ValueError("all_a_history_output requires metadata_scope=all_a.")
    _log(
        f"[baostock] start fetch: output_root={output_root}, start_date={start_date}, "
        f"end_date={end_date}, indices={indices}, financial_years={financial_start_year}-{financial_end_year}"
    )
    client = _require_baostock()
    login_result = client.login()
    if login_result.error_code != "0":
        raise RuntimeError(f"baostock login failed: {login_result.error_code} {login_result.error_msg}")
    _log("[baostock] login success")

    stats = FetchStats()
    try:
        selected_codes: list[str]
        if skip_index_memberships:
            _log("[baostock] skip index membership stage")
            selected_codes = _load_selected_codes_from_output(output_root) if selected_codes_file is None else []
        else:
            trade_dates = _fetch_trade_dates(start_date, end_date)
            _log(f"[baostock] trading dates loaded: {len(trade_dates)}")
            unique_codes: set[str] = set()

            for index_id in indices:
                _log(f"[baostock] fetching index snapshots: {index_id}")
                snapshot_rows = _fetch_index_snapshots(
                    index_id=index_id,
                    trade_dates=trade_dates,
                    sleep_seconds=sleep_seconds,
                )
                change_rows = _derive_change_rows(snapshot_rows)
                _log(
                    f"[baostock] index complete: {index_id}, snapshots={len(snapshot_rows)}, changes={len(change_rows)}"
                )

                _write_csv(output_root / "index_memberships" / f"{index_id}_snapshots.csv", snapshot_rows)
                _write_csv(output_root / "index_memberships" / f"{index_id}_changes.csv", change_rows)

                unique_codes.update(row["code"] for row in snapshot_rows)
                stats.index_snapshot_rows += len(snapshot_rows)
                stats.index_change_rows += len(change_rows)

            selected_codes = sorted(unique_codes)

        if selected_codes_file is not None:
            selected_codes = _load_selected_codes_from_file(selected_codes_file)
        if max_codes is not None:
            selected_codes = selected_codes[:max_codes]
        stats.unique_codes = len(selected_codes)
        _log(f"[baostock] unique selected codes: {stats.unique_codes}")

        stock_basic_rows: list[dict[str, str]] | None = None
        if not skip_metadata:
            metadata_codes = None if metadata_scope == "all_a" else set(selected_codes)
            stock_basic_rows = _fetch_stock_basic(metadata_codes)
            stock_industry_rows = _fetch_stock_industry(metadata_codes, end_date)
            _write_csv(output_root / "metadata" / "stock_basic.csv", stock_basic_rows)
            _write_csv(output_root / "metadata" / "stock_industry.csv", stock_industry_rows)
            _write_csv(output_root / "metadata" / "selected_codes.csv", [{"code": code} for code in selected_codes])
            if metadata_scope == "all_a":
                _write_csv(
                    output_root / "metadata" / "all_a_codes.csv",
                    [{"code": code} for code in _all_a_codes_from_stock_basic_rows(stock_basic_rows)],
                )
            if all_a_history_output is not None:
                all_a_history_rows = build_all_a_tradable_history_rows(stock_basic_rows, horizon_date=end_date)
                _write_csv(all_a_history_output, all_a_history_rows)
                stats.all_a_history_rows = len(all_a_history_rows)
            stats.stock_basic_rows = len(stock_basic_rows)
            stats.stock_industry_rows = len(stock_industry_rows)
            _log(
                f"[baostock] metadata complete: stock_basic={stats.stock_basic_rows}, "
                f"stock_industry={stats.stock_industry_rows}, all_a_history={stats.all_a_history_rows}"
            )
        else:
            _log("[baostock] skip metadata stage")
            if not (output_root / "metadata" / "selected_codes.csv").exists():
                _write_csv(output_root / "metadata" / "selected_codes.csv", [{"code": code} for code in selected_codes])

        if not skip_financials:
            stage2_codes = _resolve_stage2_codes(
                stage2_scope=stage2_scope,
                selected_codes=selected_codes,
                stock_basic_rows=stock_basic_rows,
                output_root=output_root,
            )
            quarter_pairs = _iter_quarters(financial_start_year, financial_end_year)
            progress_path = output_root / "financial" / "_progress.json"
            progress = _load_progress(progress_path) if resume else {}
            for query_name in _financial_queries():
                _log(f"[baostock] fetching financial dataset: {query_name}")
                completed_codes = set(progress.get(query_name, []))
                dataset_rows = 0
                for index, code in enumerate(stage2_codes, start=1):
                    if code in completed_codes:
                        continue
                    rows = _fetch_financial_rows(
                        query_name=query_name,
                        codes=[code],
                        quarter_pairs=quarter_pairs,
                        sleep_seconds=sleep_seconds,
                    )
                    _append_csv(output_root / "financial" / f"{query_name}.csv", rows)
                    dataset_rows += len(rows)
                    stats.financial_rows += len(rows)
                    completed_codes.add(code)
                    progress[query_name] = sorted(completed_codes)
                    _save_progress(progress_path, progress)
                    if index == 1 or index % 25 == 0 or index == len(stage2_codes):
                        _log(
                            f"[baostock] financial progress: dataset={query_name}, "
                            f"code_index={index}/{len(stage2_codes)}, code={code}, rows_written={dataset_rows}"
                        )
                _log(f"[baostock] financial dataset complete: {query_name}, rows={dataset_rows}")

        if not skip_reports:
            stage2_codes = _resolve_stage2_codes(
                stage2_scope=stage2_scope,
                selected_codes=selected_codes,
                stock_basic_rows=stock_basic_rows,
                output_root=output_root,
            )
            progress_path = output_root / "reports" / "_progress.json"
            progress = _load_progress(progress_path) if resume else {}
            for query_name in _report_queries():
                _log(f"[baostock] fetching report dataset: {query_name}")
                completed_codes = set(progress.get(query_name, []))
                dataset_rows = 0
                for index, code in enumerate(stage2_codes, start=1):
                    if code in completed_codes:
                        continue
                    rows = _fetch_report_rows(
                        query_name=query_name,
                        codes=[code],
                        start_date=start_date,
                        end_date=end_date,
                        sleep_seconds=sleep_seconds,
                    )
                    _append_csv(output_root / "reports" / f"{query_name}.csv", rows)
                    dataset_rows += len(rows)
                    stats.report_rows += len(rows)
                    completed_codes.add(code)
                    progress[query_name] = sorted(completed_codes)
                    _save_progress(progress_path, progress)
                    if index == 1 or index % 25 == 0 or index == len(stage2_codes):
                        _log(
                            f"[baostock] report progress: dataset={query_name}, "
                            f"code_index={index}/{len(stage2_codes)}, code={code}, rows_written={dataset_rows}"
                        )
                _log(f"[baostock] report dataset complete: {query_name}, rows={dataset_rows}")

        manifest_path = output_root / "manifest.json"
        existing_manifest = (
            json.loads(manifest_path.read_text(encoding="utf-8"))
            if manifest_path.exists()
            else {
                "source": "baostock",
                "start_date": start_date,
                "end_date": end_date,
                "indices": indices,
                "financial_start_year": financial_start_year,
                "financial_end_year": financial_end_year,
                "max_codes": max_codes,
                "sleep_seconds": sleep_seconds,
                "stages": {},
                "stats": _empty_stats(),
            }
        )
        stage_key = "stage_index_and_metadata" if not skip_index_memberships else "stage_financial_and_reports"
        stage_stats = {
            "index_snapshot_rows": stats.index_snapshot_rows,
            "index_change_rows": stats.index_change_rows,
            "unique_codes": stats.unique_codes,
            "stock_basic_rows": stats.stock_basic_rows,
            "stock_industry_rows": stats.stock_industry_rows,
            "all_a_history_rows": stats.all_a_history_rows,
            "financial_rows": stats.financial_rows,
            "report_rows": stats.report_rows,
        }
        existing_manifest["stages"][stage_key] = {
            "skip_index_memberships": skip_index_memberships,
            "skip_metadata": skip_metadata,
            "skip_financials": skip_financials,
            "skip_reports": skip_reports,
            "stats": stage_stats,
        }
        merged_stats = existing_manifest.get("stats", _empty_stats())
        for key, value in stage_stats.items():
            merged_stats[key] = max(int(merged_stats.get(key, 0)), int(value))
        existing_manifest["stats"] = merged_stats
        manifest_path.write_text(
            json.dumps(existing_manifest, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        return stats
    finally:
        client.logout()
        _log("[baostock] logout success")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch constituent and financial data via baostock.")
    parser.add_argument("--output-root", type=Path, default=Path("code/data/formal/baostock"))
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--end-date", default=_today_iso())
    parser.add_argument("--indices", default="hs300,sz50,zz500")
    parser.add_argument("--financial-start-year", type=int, default=2015)
    parser.add_argument("--financial-end-year", type=int, default=date.today().year)
    parser.add_argument("--max-codes", type=int, default=None)
    parser.add_argument("--sleep-seconds", type=float, default=0.0)
    parser.add_argument("--skip-index-memberships", action="store_true")
    parser.add_argument("--skip-metadata", action="store_true")
    parser.add_argument("--metadata-scope", choices=["selected", "all_a"], default="selected")
    parser.add_argument("--stage2-scope", choices=["selected", "all_a"], default="selected")
    parser.add_argument(
        "--all-a-history-output",
        type=Path,
        default=None,
    )
    parser.add_argument("--skip-financials", action="store_true")
    parser.add_argument("--skip-reports", action="store_true")
    parser.add_argument("--selected-codes-file", type=Path, default=None)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    stats = fetch_baostock_bundle(
        output_root=args.output_root.resolve(),
        start_date=args.start_date,
        end_date=args.end_date,
        indices=[item.strip() for item in args.indices.split(",") if item.strip()],
        financial_start_year=args.financial_start_year,
        financial_end_year=args.financial_end_year,
        max_codes=args.max_codes,
        sleep_seconds=args.sleep_seconds,
        skip_financials=args.skip_financials,
        skip_reports=args.skip_reports,
        skip_index_memberships=args.skip_index_memberships,
        skip_metadata=args.skip_metadata,
        metadata_scope=args.metadata_scope,
        stage2_scope=args.stage2_scope,
        all_a_history_output=args.all_a_history_output.resolve() if args.all_a_history_output else None,
        selected_codes_file=args.selected_codes_file.resolve() if args.selected_codes_file else None,
        resume=not args.no_resume,
    )
    print(
        "Fetched baostock bundle:",
        json.dumps(
            {
                "index_snapshot_rows": stats.index_snapshot_rows,
                "index_change_rows": stats.index_change_rows,
                "unique_codes": stats.unique_codes,
                "stock_basic_rows": stats.stock_basic_rows,
                "stock_industry_rows": stats.stock_industry_rows,
                "all_a_history_rows": stats.all_a_history_rows,
                "financial_rows": stats.financial_rows,
                "report_rows": stats.report_rows,
            },
            ensure_ascii=False,
        ),
    )


if __name__ == "__main__":
    main()
