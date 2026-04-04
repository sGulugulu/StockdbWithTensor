from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import baostock as bs


DEFAULT_FIELDS = (
    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,"
    "turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST"
)


def _read_codes(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [row["code"] for row in csv.DictReader(handle) if row.get("code")]


def _load_progress(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"completed_codes": []}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_progress(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


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
) -> None:
    codes = _read_codes(codes_path)
    if max_codes is not None:
        codes = codes[:max_codes]

    effective_progress_path = progress_path or output_path.with_suffix(".progress.json")
    progress = _load_progress(effective_progress_path) if resume else {"completed_codes": []}
    completed_codes = set(progress.get("completed_codes", []))
    pending_codes = [code for code in codes if code not in completed_codes]

    login_result = bs.login()
    if login_result.error_code != "0":
        raise RuntimeError(f"baostock login failed: {login_result.error_code} {login_result.error_msg}")

    try:
        fieldnames = fields.split(",")
        batch_counter = 0
        for batch_start in range(0, len(pending_codes), batch_size):
            batch_counter += 1
            batch_codes = pending_codes[batch_start : batch_start + batch_size]
            batch_rows: list[dict[str, str]] = []
            for code in batch_codes:
                rs = bs.query_history_k_data_plus(
                    code,
                    fields,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    adjustflag=adjustflag,
                )
                rows = _query_to_rows(rs)
                batch_rows.extend(rows)
                completed_codes.add(code)

            if batch_rows:
                _append_rows(output_path, batch_rows, list(batch_rows[0].keys()))
            elif not output_path.exists():
                _append_rows(output_path, [], fieldnames)

            progress = {
                "total_codes": len(codes),
                "completed_count": len(completed_codes),
                "completed_codes": sorted(completed_codes),
                "batch_size": batch_size,
                "last_completed_code": batch_codes[-1] if batch_codes else None,
                "output_path": str(output_path),
            }
            _save_progress(effective_progress_path, progress)
            print(
                f"[baostock-kline] batch {batch_counter}: "
                f"completed={len(completed_codes)}/{len(codes)} rows_written={len(batch_rows)}",
                flush=True,
            )
            if stop_after_batches is not None and batch_counter >= stop_after_batches:
                break
    finally:
        bs.logout()


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch daily kline and valuation panel from baostock.")
    parser.add_argument("--codes-file", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--start-date", default="2015-01-01")
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--fields", default=DEFAULT_FIELDS)
    parser.add_argument("--frequency", default="d")
    parser.add_argument("--adjustflag", default="3")
    parser.add_argument("--max-codes", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--progress-path", type=Path, default=None)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--stop-after-batches", type=int, default=None)
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
    )


if __name__ == "__main__":
    main()
