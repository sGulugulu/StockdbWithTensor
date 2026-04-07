from __future__ import annotations

import argparse
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.build_tdx_year_slice import build_tdx_year_slice
from data.build_tdx_full_master_base import build_tdx_full_master_base
from data.merge_baostock_master_fields import merge_baostock_master_fields


def build_full_master_for_year(
    *,
    tdx_raw_path: Path,
    baostock_master_path: Path,
    output_dir: Path,
    year: int,
    adjustflag_value: str = "2",
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    tdx_slice_path = output_dir / f"tdx_{year}_raw.csv"
    tdx_base_path = output_dir / f"tdx_full_master_base_{year}.csv"
    full_master_path = output_dir / f"full_master_{year}.csv"

    build_tdx_year_slice(
        input_path=tdx_raw_path,
        output_path=tdx_slice_path,
        year=year,
    )
    build_tdx_full_master_base(
        input_path=tdx_slice_path,
        output_path=tdx_base_path,
        adjustflag_value=adjustflag_value,
    )
    merge_baostock_master_fields(
        tdx_base_path=tdx_base_path,
        baostock_path=baostock_master_path,
        output_path=full_master_path,
    )
    return tdx_slice_path, tdx_base_path, full_master_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a transitional full master CSV for one calendar year.")
    parser.add_argument("--tdx-raw-path", type=Path, required=True)
    parser.add_argument("--baostock-master-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--adjustflag-value", default="2")
    args = parser.parse_args()
    slice_path, base_path, full_path = build_full_master_for_year(
        tdx_raw_path=args.tdx_raw_path,
        baostock_master_path=args.baostock_master_path,
        output_dir=args.output_dir,
        year=args.year,
        adjustflag_value=args.adjustflag_value,
    )
    print(f"tdx_slice={slice_path}")
    print(f"tdx_base={base_path}")
    print(f"full_master={full_path}")


if __name__ == "__main__":
    main()
