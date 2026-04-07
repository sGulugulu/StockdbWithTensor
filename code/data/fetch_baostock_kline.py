from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import sys

import baostock as bs

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.year_windows import iter_year_date_ranges


DEFAULT_FIELDS = (
    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,"
    "turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST"
)


def _normalize_query_code(code: str) -> str:
    return code.strip().lower()


def _is_supported_kline_code(code: str) -> bool:
    normalized = _normalize_query_code(code)
    return normalized.startswith("sh.") or normalized.startswith("sz.")


def _read_codes(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [
            _normalize_query_code(row["code"])
            for row in csv.DictReader(handle)
            if row.get("code") and row["code"].strip()
        ]


def _load_progress(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"completed_codes": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_progress(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _is_not_logged_in_error(error_code: str | None) -> bool:
    return str(error_code or "").strip() == "10001001"


def _safe_login() -> None:
    login_result = bs.login()
    if login_result.error_code != "0":
        raise RuntimeError(f"baostock login failed: {login_result.error_code} {login_result.error_msg}")
    print("[baostock-kline] login success", flush=True)


def _safe_logout() -> None:
    try:
        logout_result = bs.logout()
        if getattr(logout_result, "error_code", "0") not in {"0", None, ""}:
            print(
                f"[baostock-kline] logout failed: {getattr(logout_result, 'error_code', '?')} "
                f"{getattr(logout_result, 'error_msg', '')}",
                flush=True,
            )
            return
    except Exception as exc:
        print(f"[baostock-kline] logout failed: {exc}", flush=True)
        return
    print("[baostock-kline] logout success", flush=True)


def _query_to_rows(resultset: object, *, context: str = "") -> list[dict[str, str]]:
    if getattr(resultset, "error_code", None) != "0":
        raise RuntimeError(
            f"baostock query failed: {context} error_code={getattr(resultset, 'error_code', '?')} "
            f"{getattr(resultset, 'error_msg', '')}"
        )
    rows: list[dict[str, str]] = []
    fields = list(getattr(resultset, "fields", []))
    while resultset.next():
        rows.append(dict(zip(fields, resultset.get_row_data(), strict=False)))
    return rows


def _query_with_relogin(
    *,
    code: str,
    fields: str,
    start_date: str,
    end_date: str,
    frequency: str,
    adjustflag: str,
) -> list[dict[str, str]]:
    max_attempts = 2
    last_error: RuntimeError | None = None
    for attempt in range(1, max_attempts + 1):
        resultset = bs.query_history_k_data_plus(
            code,
            fields,
            start_date=start_date,
            end_date=end_date,
            frequency=frequency,
            adjustflag=adjustflag,
        )
        error_code = getattr(resultset, "error_code", None)
        if error_code == "0":
            return _query_to_rows(
                resultset,
                context=f"kline code={code} start_date={start_date} end_date={end_date}",
            )
        if _is_not_logged_in_error(str(error_code)) and attempt < max_attempts:
            print(f"[baostock-kline] session expired, relogin and retry: code={code}", flush=True)
            _safe_login()
            continue
        last_error = RuntimeError(
            f"baostock query failed: kline code={code} start_date={start_date} end_date={end_date} "
            f"error_code={error_code} {getattr(resultset, 'error_msg', '')}"
        )
        break
    if last_error is not None:
        raise last_error
    raise RuntimeError(f"baostock query failed without result: code={code}")


def _append_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def fetch_kline_panel(
    *,
    codes_path: Path,
    output_path: Path,
    start_date: str,
    end_date: str,
    fields: str,
    frequency: str,
    adjustflag: str,
    max_codes: int | None,
    batch_size: int,
    progress_path: Path | None,
    resume: bool,
    stop_after_batches: int | None,
    partition_by_year: bool,
) -> None:
    raw_codes = _read_codes(codes_path)
    unsupported_codes = [code for code in raw_codes if not _is_supported_kline_code(code)]
    if unsupported_codes:
        print(
            "[baostock-kline] skipping unsupported codes: "
            f"count={len(unsupported_codes)} sample={','.join(unsupported_codes[:3])}",
            flush=True,
        )
    codes = [code for code in raw_codes if _is_supported_kline_code(code)]
    if max_codes is not None:
        codes = codes[:max_codes]

    effective_progress_path = progress_path or output_path.with_suffix(".progress.json")
    progress = _load_progress(effective_progress_path) if resume else {}
    completed_codes = set(progress.get("completed_codes", []))
    completed_units = set(progress.get("completed_units", []))
    pending_codes = [code for code in codes if code not in completed_codes]
    date_windows = iter_year_date_ranges(start_date, end_date) if partition_by_year else [(start_date, end_date, 0)]

    _safe_login()

    try:
        fieldnames = fields.split(",")
        batch_counter = 0
        for window_start, window_end, year_label in date_windows:
            year_pending_codes = [
                code for code in pending_codes if f"{code}|{year_label}" not in completed_units
            ]
            for batch_start in range(0, len(year_pending_codes), batch_size):
                batch_counter += 1
                batch_codes = year_pending_codes[batch_start : batch_start + batch_size]
                batch_rows: list[dict[str, str]] = []
                for code in batch_codes:
                    rows = _query_with_relogin(
                        code=code,
                        fields=fields,
                        start_date=window_start,
                        end_date=window_end,
                        frequency=frequency,
                        adjustflag=adjustflag,
                    )
                    for row in rows:
                        row["query_year"] = str(year_label) if partition_by_year else ""
                    batch_rows.extend(rows)
                    completed_units.add(f"{code}|{year_label}")
                for code in batch_codes:
                    if all(f"{code}|{label}" in completed_units for _, _, label in date_windows):
                        completed_codes.add(code)

                if batch_rows:
                    _append_rows(output_path, batch_rows, list(batch_rows[0].keys()))
                elif not output_path.exists():
                    _append_rows(output_path, [], fieldnames + (["query_year"] if partition_by_year else []))

                progress = {
                    "total_codes": len(codes),
                    "completed_count": len(completed_codes),
                    "completed_codes": sorted(completed_codes),
                    "completed_units": sorted(completed_units),
                    "batch_size": batch_size,
                    "last_completed_code": batch_codes[-1] if batch_codes else None,
                    "last_completed_year": year_label,
                    "output_path": str(output_path),
                    "partition_by_year": partition_by_year,
                    "year_complete": False,
                    "run_complete": False,
                }
                _save_progress(effective_progress_path, progress)
                print(
                    f"[baostock-kline] batch {batch_counter}: year={year_label} "
                    f"completed_codes={len(completed_codes)}/{len(codes)} rows_written={len(batch_rows)}",
                    flush=True,
                )
                if stop_after_batches is not None and batch_counter >= stop_after_batches:
                    break
            progress = {
                **progress,
                "last_completed_year": year_label,
                "year_complete": True,
                "run_complete": False,
            }
            _save_progress(effective_progress_path, progress)
            print(f"[baostock-kline] year complete: {year_label}", flush=True)
            if stop_after_batches is not None and batch_counter >= stop_after_batches:
                break
        progress = {
            **progress,
            "run_complete": True,
        }
        _save_progress(effective_progress_path, progress)
        print("[baostock-kline] run complete", flush=True)
    finally:
        _safe_logout()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch daily kline and valuation panel from baostock.")
    parser.add_argument("--codes-file", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--fields", default=DEFAULT_FIELDS)
    parser.add_argument("--frequency", default="d")
    parser.add_argument("--adjustflag", default="2")
    parser.add_argument("--max-codes", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--progress-path", type=Path, default=None)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--stop-after-batches", type=int, default=None)
    parser.add_argument("--partition-by-year", action="store_true")
    args = parser.parse_args()

    fetch_kline_panel(
        codes_path=args.codes_file,
        output_path=args.output_path,
        start_date=args.start_date,
        end_date=args.end_date,
        fields=args.fields,
        frequency=args.frequency,
        adjustflag=args.adjustflag,
        max_codes=args.max_codes,
        batch_size=args.batch_size,
        progress_path=args.progress_path.resolve() if args.progress_path else None,
        resume=not args.no_resume,
        stop_after_batches=args.stop_after_batches,
        partition_by_year=args.partition_by_year,
    )


if __name__ == "__main__":
    main()
