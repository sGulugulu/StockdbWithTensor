from __future__ import annotations

import argparse
import csv
from pathlib import Path

import baostock as bs


DEFAULT_FIELDS = (
    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,"
    "turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST"
)


def _read_codes(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return [row["code"] for row in csv.DictReader(handle) if row.get("code")]


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
) -> None:
    codes = _read_codes(codes_path)
    if max_codes is not None:
        codes = codes[:max_codes]

    login_result = bs.login()
    if login_result.error_code != "0":
        raise RuntimeError(f"baostock login failed: {login_result.error_code} {login_result.error_msg}")

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        writer = None
        handle = output_path.open("w", encoding="utf-8", newline="")
        try:
            for index, code in enumerate(codes, start=1):
                rs = bs.query_history_k_data_plus(
                    code,
                    fields,
                    start_date=start_date,
                    end_date=end_date,
                    frequency=frequency,
                    adjustflag=adjustflag,
                )
                rows = _query_to_rows(rs)
                if writer is None:
                    writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else fields.split(","))
                    writer.writeheader()
                for row in rows:
                    writer.writerow(row)
                if index == 1 or index % 50 == 0 or index == len(codes):
                    print(
                        f"[baostock-kline] progress: {index}/{len(codes)} code={code} rows={len(rows)}",
                        flush=True,
                    )
        finally:
            handle.close()
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
    )


if __name__ == "__main__":
    main()
