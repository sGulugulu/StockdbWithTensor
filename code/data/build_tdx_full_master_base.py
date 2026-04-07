from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path


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


def _safe_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def build_tdx_full_master_base(
    *,
    input_path: Path,
    output_path: Path,
    adjustflag_value: str = "2",
) -> None:
    grouped_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    with input_path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            if not row.get("stock_code") or not row.get("trade_date"):
                continue
            grouped_rows[_to_baostock_code(row["stock_code"])].append(row)

    output_rows: list[dict[str, object]] = []
    for code, rows in grouped_rows.items():
        rows.sort(key=lambda row: row["trade_date"])
        previous_close: float | None = None
        for row in rows:
            close = _safe_float(row.get("close"))
            preclose = previous_close
            pct_chg = None
            if close is not None and preclose not in (None, 0):
                pct_chg = (close / preclose - 1.0) * 100.0
            output_rows.append(
                {
                    "date": row["trade_date"],
                    "code": code,
                    "open": row.get("open", ""),
                    "high": row.get("high", ""),
                    "low": row.get("low", ""),
                    "close": row.get("close", ""),
                    "preclose": "" if preclose is None else f"{preclose:.4f}",
                    "volume": row.get("volume", ""),
                    "amount": row.get("amount", ""),
                    "adjustflag": adjustflag_value,
                    "pctChg": "" if pct_chg is None else f"{pct_chg:.6f}",
                    "source_price_vendor": "tongdaxin",
                    "source_file": row.get("source_file", ""),
                }
            )
            previous_close = close if close is not None else previous_close

    output_rows.sort(key=lambda item: (str(item["date"]), str(item["code"])))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        fieldnames = list(output_rows[0].keys()) if output_rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if fieldnames:
            writer.writeheader()
            writer.writerows(output_rows)
        else:
            handle.write("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a standardized TDX-based full master base panel.")
    parser.add_argument("--input-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--adjustflag-value", default="2")
    args = parser.parse_args()
    build_tdx_full_master_base(
        input_path=args.input_path,
        output_path=args.output_path,
        adjustflag_value=args.adjustflag_value,
    )


if __name__ == "__main__":
    main()
