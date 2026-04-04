from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable

from .config import DataConfig, MarketConfig
from .dataset import NormalizedRecord


def normalize_trade_date(value: str) -> str:
    return date.fromisoformat(value.strip()).isoformat()


def _normalize_cn_a_symbol(cleaned: str) -> str:
    if "." in cleaned:
        left, right = cleaned.split(".", 1)
        if left in {"SH", "SZ", "BJ"} and right.isdigit():
            return f"{right}.{left}"
        if right in {"SH", "SZ", "BJ"} and left.isdigit():
            return f"{left}.{right}"
        return cleaned
    if cleaned.startswith(("6", "9")):
        return f"{cleaned}.SH"
    return f"{cleaned}.SZ"


class SymbolNormalizer:
    def __init__(self, market_id: str) -> None:
        self.market_id = market_id

    def normalize(self, symbol: str) -> str:
        cleaned = symbol.strip().upper()
        if self.market_id == "us_equity":
            return cleaned
        if self.market_id == "cn_a":
            return _normalize_cn_a_symbol(cleaned)
        return cleaned


@dataclass(slots=True)
class UniverseMembership:
    symbol: str
    start_date: str
    end_date: str


class UniverseProvider:
    def __init__(self, memberships: list[UniverseMembership]) -> None:
        self.memberships = memberships

    @classmethod
    def from_config(
        cls,
        config: MarketConfig,
        symbol_normalizer: SymbolNormalizer,
    ) -> "UniverseProvider | None":
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
                        symbol=symbol_normalizer.normalize(row[config.universe_symbol_column]),
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


class TradingCalendar:
    def clamp_range(self, dates: Iterable[str], requested_start: str, requested_end: str) -> tuple[str, str]:
        available_dates = sorted(set(dates))
        if not available_dates:
            raise ValueError("No available trade dates were loaded from the factor data source.")
        actual_dates = [
            trade_date
            for trade_date in available_dates
            if requested_start <= trade_date <= requested_end
        ]
        if not actual_dates:
            raise ValueError(
                f"No trade dates remain after applying requested range {requested_start} to {requested_end}."
            )
        return actual_dates[0], actual_dates[-1]


class FactorDataSource:
    def load_records(self, data_config: DataConfig, market_config: MarketConfig) -> list[NormalizedRecord]:
        raise NotImplementedError


class CsvFactorDataSource(FactorDataSource):
    def __init__(self, symbol_normalizer: SymbolNormalizer) -> None:
        self.symbol_normalizer = symbol_normalizer

    @staticmethod
    def _parse_float(value: str | None) -> float | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            return None
        return float(stripped)

    def load_records(self, data_config: DataConfig, market_config: MarketConfig) -> list[NormalizedRecord]:
        path = Path(data_config.path)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {path}")

        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if reader.fieldnames is None:
                raise ValueError("Input CSV is missing a header row.")
            fieldnames = set(reader.fieldnames)

            required_columns = {data_config.stock_column, data_config.date_column}
            if data_config.industry_column:
                required_columns.add(data_config.industry_column)
            if data_config.return_column:
                required_columns.add(data_config.return_column)
            if data_config.format == "wide":
                required_columns.update(data_config.factor_columns)
            else:
                required_columns.update(
                    {data_config.factor_name_column or "", data_config.factor_value_column or ""}
                )
            missing = [column for column in required_columns if column and column not in fieldnames]
            if missing:
                raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

            records: list[NormalizedRecord] = []
            for row in reader:
                stock_code = self.symbol_normalizer.normalize(row[data_config.stock_column])
                trade_date = normalize_trade_date(row[data_config.date_column])
                industry = (
                    row[data_config.industry_column].strip()
                    if data_config.industry_column and row[data_config.industry_column]
                    else None
                )
                future_return = (
                    self._parse_float(row[data_config.return_column])
                    if data_config.return_column
                    else None
                )

                if data_config.format == "wide":
                    for factor_column in data_config.factor_columns:
                        factor_value = self._parse_float(row[factor_column])
                        records.append(
                            NormalizedRecord(
                                stock_code=stock_code,
                                trade_date=trade_date,
                                factor_name=factor_column,
                                factor_value=float("nan") if factor_value is None else float(factor_value),
                                industry=industry,
                                future_return=future_return,
                            )
                        )
                else:
                    factor_name = row[data_config.factor_name_column or ""].strip()
                    factor_value = self._parse_float(row[data_config.factor_value_column or ""])
                    records.append(
                        NormalizedRecord(
                            stock_code=stock_code,
                            trade_date=trade_date,
                            factor_name=factor_name,
                            factor_value=float("nan") if factor_value is None else float(factor_value),
                            industry=industry,
                            future_return=future_return,
                        )
                    )

        if not records:
            raise ValueError("No usable records were loaded from the CSV.")
        return records


@dataclass(slots=True)
class MarketAdapter:
    market_config: MarketConfig
    symbol_normalizer: SymbolNormalizer
    trading_calendar: TradingCalendar
    factor_data_source: FactorDataSource
    universe_provider: UniverseProvider | None

    def load_records(self, data_config: DataConfig) -> list[NormalizedRecord]:
        return self.factor_data_source.load_records(data_config, self.market_config)

    def filter_records(self, records: list[NormalizedRecord]) -> tuple[list[NormalizedRecord], str, str]:
        actual_start, actual_end = self.trading_calendar.clamp_range(
            (record.trade_date for record in records),
            self.market_config.start_date,
            self.market_config.end_date,
        )
        filtered = [
            record
            for record in records
            if actual_start <= record.trade_date <= actual_end
        ]
        if self.universe_provider is not None:
            filtered = [
                record
                for record in filtered
                if self.universe_provider.is_member(record.stock_code, record.trade_date)
            ]
        if not filtered:
            raise ValueError(
                "No records remain after applying market date range and universe membership filters."
            )
        available_dates = sorted({record.trade_date for record in filtered})
        return filtered, available_dates[0], available_dates[-1]


def create_market_adapter(config: MarketConfig) -> MarketAdapter:
    symbol_normalizer = SymbolNormalizer(config.market_id)
    return MarketAdapter(
        market_config=config,
        symbol_normalizer=symbol_normalizer,
        trading_calendar=TradingCalendar(),
        factor_data_source=CsvFactorDataSource(symbol_normalizer),
        universe_provider=UniverseProvider.from_config(config, symbol_normalizer),
    )
