from __future__ import annotations

import argparse
import csv
import struct
from datetime import datetime
from pathlib import Path


RECORD_STRUCT = struct.Struct("<IIIIIfII")


def _format_trade_date(raw_date: int) -> str:
    return datetime.strptime(str(raw_date), "%Y%m%d").strftime("%Y-%m-%d")


def _iter_tdx_day_rows(day_path: Path, stock_code: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    with day_path.open("rb") as handle:
        while chunk := handle.read(RECORD_STRUCT.size):
            if len(chunk) != RECORD_STRUCT.size:
                break
            date_raw, open_raw, high_raw, low_raw, close_raw, amount_raw, volume_raw, _ = RECORD_STRUCT.unpack(chunk)
            rows.append(
                {
                    "market": "sh",
                    "tdx_prefix": "sh",
                    "stock_code": stock_code,
                    "trade_date": _format_trade_date(date_raw),
                    "open": open_raw / 100.0,
                    "high": high_raw / 100.0,
                    "low": low_raw / 100.0,
                    "close": close_raw / 100.0,
                    "amount": float(amount_raw),
                    "volume": volume_raw / 100.0,
                    "source_file": str(day_path),
                }
            )
    return rows


def export_named_index_files(*, vipdoc_root: Path, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    file_specs = {
        "hs300_index_daily.csv": ("sh000300.day", "000300.SH"),
        "000050_index_daily.csv": ("sh000050.day", "000050.SH"),
        "csi_a500_index_daily.csv": ("sh000510.day", "000510.SH"),
        "zz500_index_daily.csv": ("sh000905.day", "000905.SH"),
    }
    fieldnames = [
        "market",
        "tdx_prefix",
        "stock_code",
        "trade_date",
        "open",
        "high",
        "low",
        "close",
        "amount",
        "volume",
        "source_file",
    ]
    for filename, (source_name, stock_code) in file_specs.items():
        source_path = vipdoc_root / "sh" / "lday" / source_name
        if not source_path.exists():
            continue
        with (output_dir / filename).open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            for row in _iter_tdx_day_rows(source_path, stock_code):
                writer.writerow(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Build tracked named index daily files from Tongdaxin vipdoc.")
    parser.add_argument("--vipdoc-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    export_named_index_files(vipdoc_root=args.vipdoc_root, output_dir=args.output_dir)


if __name__ == "__main__":
    main()
