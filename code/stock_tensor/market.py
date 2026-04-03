from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .config import MarketConfig


def normalize_symbol(symbol: str, market_id: str) -> str:
    cleaned = symbol.strip().upper()
    if market_id == "us_equity":
        return cleaned
    if market_id == "cn_a":
        if "." in cleaned:
            return cleaned
        if cleaned.startswith(("6", "9")):
            return f"{cleaned}.SH"
        return f"{cleaned}.SZ"
    return cleaned


def normalize_trade_date(value: str) -> str:
    return date.fromisoformat(value.strip()).isoformat()


@dataclass(slots=True)
class UniverseMembership:
    symbol: str
    start_date: str
    end_date: str


class UniverseProvider:
    def __init__(self, memberships: list[UniverseMembership]) -> None:
        self.memberships = memberships

    @classmethod
    def from_config(cls, config: MarketConfig) -> "UniverseProvider | None":
        if not config.universe_path:
            return None
        path = Path(config.universe_path)
        if not path.exists():
            raise FileNotFoundError(f"Universe file not found: {path}")

        memberships: list[UniverseMembership] = []
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("Universe CSV is missing a header row.")
            for row in reader:
                if config.universe_market_column and row.get(config.universe_market_column, "").strip():
                    if row[config.universe_market_column].strip() != config.market_id:
                        continue
                if config.universe_id_column and row.get(config.universe_id_column, "").strip():
                    if row[config.universe_id_column].strip() != config.universe_id:
                        continue
                memberships.append(
                    UniverseMembership(
                        symbol=normalize_symbol(row[config.universe_symbol_column], config.market_id),
                        start_date=normalize_trade_date(row[config.universe_start_column]),
                        end_date=normalize_trade_date(row[config.universe_end_column]),
                    )
                )
        return cls(memberships)

    def is_member(self, symbol: str, trade_date: str) -> bool:
        for membership in self.memberships:
            if membership.symbol != symbol:
                continue
            if membership.start_date <= trade_date <= membership.end_date:
                return True
        return False

    def members_on(self, trade_date: str) -> set[str]:
        return {
            membership.symbol
            for membership in self.memberships
            if membership.start_date <= trade_date <= membership.end_date
        }
