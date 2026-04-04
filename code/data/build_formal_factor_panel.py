from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

from stock_tensor.market import SymbolNormalizer


def _to_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _load_industry_map(path: Path) -> dict[str, str]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        normalizer = SymbolNormalizer("cn_a")
        return {
            normalizer.normalize(row["code"]): row.get("industry", "")
            for row in reader
            if row.get("code")
        }


def _load_membership_map(path: Path) -> dict[str, list[tuple[str, str]]]:
    memberships: dict[str, list[tuple[str, str]]] = defaultdict(list)
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        normalizer = SymbolNormalizer("cn_a")
        for row in reader:
            memberships[normalizer.normalize(row["stock_code"])].append((row["start_date"], row["end_date"]))
    return memberships


def _rolling_return(prices: list[float], window: int) -> list[float]:
    result: list[float] = []
    for index, price in enumerate(prices):
        if index < window or prices[index - window] == 0:
            result.append(0.0)
            continue
        result.append(price / prices[index - window] - 1.0)
    return result


def _future_return(prices: list[float], horizon: int) -> list[float]:
    result: list[float] = []
    for index, price in enumerate(prices):
        target_index = index + horizon
        if target_index >= len(prices) or price == 0:
            result.append(0.0)
            continue
        result.append(prices[target_index] / price - 1.0)
    return result


def build_formal_factor_panel(
    *,
    kline_path: Path,
    industry_path: Path,
    membership_path: Path,
    output_path: Path,
    symbol_column: str = "code",
    date_column: str = "date",
) -> None:
    industry_map = _load_industry_map(industry_path)
    membership_map = _load_membership_map(membership_path)
    normalizer = SymbolNormalizer("cn_a")
    grouped_rows: dict[str, list[dict[str, str]]] = defaultdict(list)
    with kline_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            normalized_code = normalizer.normalize(row[symbol_column])
            trade_date = row[date_column]
            if not any(start_date <= trade_date <= end_date for start_date, end_date in membership_map.get(normalized_code, [])):
                continue
            grouped_rows[normalized_code].append({**row, symbol_column: normalized_code})

    output_rows: list[dict[str, object]] = []
    for code, rows in grouped_rows.items():
        rows.sort(key=lambda row: row[date_column])
        closes = [_to_float(row.get("close")) or 0.0 for row in rows]
        pe_ttm = [_to_float(row.get("peTTM")) or 0.0 for row in rows]
        pb_mrq = [_to_float(row.get("pbMRQ")) or 0.0 for row in rows]
        ps_ttm = [_to_float(row.get("psTTM")) or 0.0 for row in rows]
        turn = [_to_float(row.get("turn")) or 0.0 for row in rows]
        momentum_5 = _rolling_return(closes, 5)
        momentum_20 = _rolling_return(closes, 20)
        future_5 = _future_return(closes, 5)

        for index, row in enumerate(rows):
            value_factor = 0.0 if pb_mrq[index] == 0 else 1.0 / max(pb_mrq[index], 1e-8)
            quality_factor = 0.0 if pe_ttm[index] == 0 else 1.0 / max(pe_ttm[index], 1e-8)
            volatility_factor = abs(momentum_5[index] - momentum_20[index])
            output_rows.append(
                {
                    "stock_code": code,
                    "trade_date": row[date_column],
                    "industry": industry_map.get(code, ""),
                    "value_factor": value_factor,
                    "momentum_factor": momentum_20[index],
                    "quality_factor": quality_factor,
                    "volatility_factor": volatility_factor,
                    "turn_factor": turn[index],
                    "ps_ttm": ps_ttm[index],
                    "future_return": future_5[index],
                }
            )

    output_rows.sort(key=lambda item: (str(item["trade_date"]), str(item["stock_code"])))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(output_rows[0].keys()) if output_rows else [])
        if output_rows:
            writer.writeheader()
            writer.writerows(output_rows)
        else:
            handle.write("")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a formal factor panel from baostock kline and metadata.")
    parser.add_argument("--kline-path", type=Path, required=True)
    parser.add_argument("--industry-path", type=Path, required=True)
    parser.add_argument("--membership-path", type=Path, required=True)
    parser.add_argument("--output-path", type=Path, required=True)
    args = parser.parse_args()

    build_formal_factor_panel(
        kline_path=args.kline_path,
        industry_path=args.industry_path,
        membership_path=args.membership_path,
        output_path=args.output_path,
    )


if __name__ == "__main__":
    main()
