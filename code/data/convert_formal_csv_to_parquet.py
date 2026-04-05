from __future__ import annotations

import argparse
import importlib.util
from pathlib import Path
import sys

try:
    import pandas as pd
except ImportError:
    pd = None


def _require_pandas():
    if pd is None:
        raise ModuleNotFoundError("pandas is required for CSV to Parquet conversion in this environment.")
    return pd


def parquet_engine_available() -> bool:
    return importlib.util.find_spec("pyarrow") is not None or importlib.util.find_spec("fastparquet") is not None


def collect_formal_csv_targets(formal_root: Path) -> list[tuple[Path, Path]]:
    targets: list[tuple[Path, Path]] = []
    include_dirs = [
        formal_root / "universes",
        formal_root / "factors",
        formal_root / "master",
        formal_root / "financial",
        formal_root / "reports",
    ]
    parquet_root = formal_root / "parquet"
    for directory in include_dirs:
        if not directory.exists():
            continue
        for csv_path in sorted(directory.rglob("*.csv")):
            relative = csv_path.relative_to(formal_root)
            targets.append((csv_path, parquet_root / relative.with_suffix(".parquet")))
    return targets


def convert_formal_csv_to_parquet(
    *,
    formal_root: Path,
    overwrite: bool,
) -> list[tuple[Path, Path]]:
    pandas_module = _require_pandas()
    if not parquet_engine_available():
        raise ModuleNotFoundError(
            "CSV to Parquet conversion requires either pyarrow or fastparquet in the active environment."
        )
    converted: list[tuple[Path, Path]] = []
    for csv_path, parquet_path in collect_formal_csv_targets(formal_root):
        parquet_path.parent.mkdir(parents=True, exist_ok=True)
        if parquet_path.exists() and not overwrite:
            continue
        dataframe = pandas_module.read_csv(csv_path)
        dataframe.to_parquet(parquet_path, index=False)
        converted.append((csv_path, parquet_path))
    return converted


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert structured formal CSV outputs to parquet.")
    parser.add_argument("--formal-root", type=Path, default=Path("code/data/formal"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    converted = convert_formal_csv_to_parquet(
        formal_root=args.formal_root,
        overwrite=args.overwrite,
    )
    print(f"Converted {len(converted)} CSV files to parquet.")


if __name__ == "__main__":
    main()
