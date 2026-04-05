from __future__ import annotations

import argparse
import importlib.util
import json
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


def _csv_row_count(path: Path) -> int:
    pandas_module = _require_pandas()
    return len(pandas_module.read_csv(path))


def summarize_parquet_outputs(formal_root: Path) -> list[dict[str, object]]:
    summaries: list[dict[str, object]] = []
    engine_ready = parquet_engine_available()
    pandas_module = _require_pandas() if pd is not None else None
    for csv_path, parquet_path in collect_formal_csv_targets(formal_root):
        entry: dict[str, object] = {
            "csv_path": str(csv_path),
            "parquet_path": str(parquet_path),
            "parquet_exists": parquet_path.exists(),
            "parquet_engine_available": engine_ready,
        }
        if not csv_path.exists():
            summaries.append(entry)
            continue
        if pandas_module is not None:
            csv_df = pandas_module.read_csv(csv_path)
            entry["csv_rows"] = len(csv_df)
            entry["csv_columns"] = list(csv_df.columns)
            date_column = next((column for column in ["trade_date", "date", "start_date"] if column in csv_df.columns), None)
            if date_column is not None and not csv_df.empty:
                entry["csv_min_date"] = str(csv_df[date_column].min())
                entry["csv_max_date"] = str(csv_df[date_column].max())
            if engine_ready and parquet_path.exists():
                parquet_df = pandas_module.read_parquet(parquet_path)
                entry["parquet_rows"] = len(parquet_df)
                entry["parquet_columns"] = list(parquet_df.columns)
                entry["row_count_match"] = len(csv_df) == len(parquet_df)
                entry["column_match"] = list(csv_df.columns) == list(parquet_df.columns)
                if date_column is not None and date_column in parquet_df.columns and not parquet_df.empty:
                    entry["parquet_min_date"] = str(parquet_df[date_column].min())
                    entry["parquet_max_date"] = str(parquet_df[date_column].max())
                    entry["date_range_match"] = (
                        entry.get("csv_min_date") == entry.get("parquet_min_date")
                        and entry.get("csv_max_date") == entry.get("parquet_max_date")
                    )
        summaries.append(entry)
    return summaries


def main() -> None:
    parser = argparse.ArgumentParser(description="Convert structured formal CSV outputs to parquet.")
    parser.add_argument("--formal-root", type=Path, default=Path("code/data/formal"))
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()
    converted = convert_formal_csv_to_parquet(
        formal_root=args.formal_root,
        overwrite=args.overwrite,
    )
    print(
        json.dumps(
            {
                "converted_count": len(converted),
                "summaries": summarize_parquet_outputs(args.formal_root),
            },
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
