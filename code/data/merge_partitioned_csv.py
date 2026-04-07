from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path


def _row_completeness(row: dict[str, str]) -> int:
    return sum(1 for value in row.values() if str(value).strip())


def merge_partitioned_csv(
    *,
    input_paths: list[Path],
    output_path: Path,
    sort_keys: list[str] | None = None,
) -> dict[str, int]:
    rows: list[dict[str, str]] = []
    fieldnames: list[str] | None = None
    duplicate_keys = 0
    replaced_with_more_complete = 0
    dedupe_map: dict[tuple[str, ...], dict[str, str]] | None = {} if sort_keys else None
    for path in input_paths:
        if not path.exists():
            continue
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if fieldnames is None:
                fieldnames = reader.fieldnames or []
            for row in reader:
                if dedupe_map is None:
                    rows.append(row)
                    continue
                key = tuple(row.get(part, "") for part in sort_keys)
                if key in dedupe_map:
                    duplicate_keys += 1
                    existing = dedupe_map[key]
                    if _row_completeness(row) >= _row_completeness(existing):
                        if _row_completeness(row) > _row_completeness(existing):
                            replaced_with_more_complete += 1
                        dedupe_map[key] = row
                else:
                    dedupe_map[key] = row

    if dedupe_map is not None:
        rows = list(dedupe_map.values())

    if sort_keys:
        rows.sort(key=lambda row: tuple(row.get(key, "") for key in sort_keys))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames or [])
        if fieldnames:
            writer.writeheader()
            writer.writerows(rows)
        else:
            handle.write("")
    return {
        "input_rows": len(rows) + duplicate_keys if sort_keys else len(rows),
        "output_rows": len(rows),
        "duplicate_keys": duplicate_keys,
        "replaced_with_more_complete": replaced_with_more_complete,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge partitioned CSV files into one CSV.")
    parser.add_argument("--inputs", nargs="+", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    parser.add_argument("--sort-keys", default="")
    args = parser.parse_args()
    sort_keys = [item.strip() for item in args.sort_keys.split(",") if item.strip()]
    stats = merge_partitioned_csv(
        input_paths=args.inputs,
        output_path=args.output_path,
        sort_keys=sort_keys or None,
    )
    print(json.dumps(stats, ensure_ascii=False))


if __name__ == "__main__":
    main()
