from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from stock_tensor.market import SymbolNormalizer


@dataclass(frozen=True, slots=True)
class SegmentedUniverseResult:
    all_a_history_path: Path
    industry_history_paths: list[Path]
    size_history_paths: list[Path]


def _normalize_code(raw_code: str) -> str:
    return SymbolNormalizer("cn_a").normalize(raw_code)


def _industry_slug(industry_name: str) -> str:
    prefix_chars: list[str] = []
    for char in industry_name:
        if char.isascii() and char.isalnum():
            prefix_chars.append(char)
            continue
        break
    return "".join(prefix_chars).lower()


def _load_all_a_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def _active_codes_on_date(rows: list[dict[str, str]], as_of_date: str) -> set[str]:
    return {
        row["stock_code"]
        for row in rows
        if row["start_date"] <= as_of_date <= row["end_date"]
    }


def _load_industry_map(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return {
        _normalize_code(row["code"]): row.get("industry", "").strip()
        for row in rows
        if row.get("code")
    }


def _load_kline_close_map(path: Path, as_of_date: str) -> dict[str, float]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    close_map: dict[str, float] = {}
    for row in rows:
        if row["date"] != as_of_date:
            continue
        close_map[_normalize_code(row["code"])] = float(row["close"])
    return close_map


def _latest_share_map(path: Path, active_codes: set[str], as_of_date: str) -> dict[str, float]:
    latest_rows: dict[str, dict[str, str]] = {}
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            code = _normalize_code(row["code"])
            if code not in active_codes or row["pubDate"] > as_of_date:
                continue
            previous = latest_rows.get(code)
            if previous is None or row["pubDate"] > previous["pubDate"]:
                latest_rows[code] = row
    share_map: dict[str, float] = {}
    for code, row in latest_rows.items():
        share_value = row.get("liqaShare") or row.get("totalShare") or ""
        if not share_value:
            continue
        share = float(share_value)
        if share > 0:
            share_map[code] = share
    return share_map


def _write_universe_history(
    *,
    source_rows: list[dict[str, str]],
    selected_codes: set[str],
    universe_id: str,
    output_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["market_id", "universe_id", "stock_code", "start_date", "end_date"],
        )
        writer.writeheader()
        for row in source_rows:
            if row["stock_code"] not in selected_codes:
                continue
            writer.writerow(
                {
                    "market_id": row["market_id"],
                    "universe_id": universe_id,
                    "stock_code": row["stock_code"],
                    "start_date": row["start_date"],
                    "end_date": row["end_date"],
                }
            )


def build_segmented_formal_universes(
    *,
    all_a_history_path: Path,
    industry_path: Path,
    profit_data_path: Path,
    shared_kline_path: Path,
    output_dir: Path,
    as_of_date: str,
    top_industry_count: int = 3,
) -> SegmentedUniverseResult:
    all_a_rows = _load_all_a_rows(all_a_history_path)
    active_codes = _active_codes_on_date(all_a_rows, as_of_date)
    close_map = _load_kline_close_map(shared_kline_path, as_of_date)
    industry_map = _load_industry_map(industry_path)
    active_with_kline = active_codes & set(close_map)

    industry_counter = Counter(
        industry_map.get(code, "")
        for code in active_with_kline
        if industry_map.get(code, "")
    )
    top_industries = [industry for industry, _ in industry_counter.most_common(top_industry_count)]

    output_dir.mkdir(parents=True, exist_ok=True)
    all_a_active_path = output_dir / "all_a_active_history.csv"
    _write_universe_history(
        source_rows=all_a_rows,
        selected_codes=active_with_kline,
        universe_id="ALL_A_ACTIVE",
        output_path=all_a_active_path,
    )

    industry_history_paths: list[Path] = []
    for industry in top_industries:
        industry_code = _industry_slug(industry)
        selected_codes = {code for code in active_with_kline if industry_map.get(code) == industry}
        output_path = output_dir / f"industry_{industry_code}_history.csv"
        _write_universe_history(
            source_rows=all_a_rows,
            selected_codes=selected_codes,
            universe_id=f"INDUSTRY_{industry_code.upper()}",
            output_path=output_path,
        )
        industry_history_paths.append(output_path)

    share_map = _latest_share_map(profit_data_path, active_with_kline, as_of_date)
    market_caps = sorted(
        [
            (code, close_map[code] * share_map[code])
            for code in active_with_kline
            if code in share_map
        ],
        key=lambda item: item[1],
    )
    bucket_size = max(len(market_caps) // 3, 1)
    size_buckets = {
        "size_small_history.csv": {code for code, _ in market_caps[:bucket_size]},
        "size_mid_history.csv": {code for code, _ in market_caps[bucket_size : bucket_size * 2]},
        "size_large_history.csv": {code for code, _ in market_caps[bucket_size * 2 :]},
    }
    size_history_paths: list[Path] = []
    for filename, selected_codes in size_buckets.items():
        label = filename.replace("_history.csv", "").upper()
        output_path = output_dir / filename
        _write_universe_history(
            source_rows=all_a_rows,
            selected_codes=selected_codes,
            universe_id=label,
            output_path=output_path,
        )
        size_history_paths.append(output_path)

    return SegmentedUniverseResult(
        all_a_history_path=all_a_active_path,
        industry_history_paths=industry_history_paths,
        size_history_paths=size_history_paths,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build segmented formal universe histories for AC3 experiments.")
    parser.add_argument("--all-a-history-path", type=Path, required=True)
    parser.add_argument("--industry-path", type=Path, required=True)
    parser.add_argument("--profit-data-path", type=Path, required=True)
    parser.add_argument("--shared-kline-path", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--as-of-date", type=str, required=True)
    parser.add_argument("--top-industry-count", type=int, default=3)
    args = parser.parse_args()
    result = build_segmented_formal_universes(
        all_a_history_path=args.all_a_history_path,
        industry_path=args.industry_path,
        profit_data_path=args.profit_data_path,
        shared_kline_path=args.shared_kline_path,
        output_dir=args.output_dir,
        as_of_date=args.as_of_date,
        top_industry_count=args.top_industry_count,
    )
    print(result.all_a_history_path.as_posix())
    for path in result.industry_history_paths + result.size_history_paths:
        print(path.as_posix())


if __name__ == "__main__":
    main()
