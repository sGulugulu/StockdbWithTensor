from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np

from .config import DataConfig, PreprocessConfig


@dataclass(slots=True)
class NormalizedRecord:
    stock_code: str
    trade_date: str
    factor_name: str
    factor_value: float
    industry: str | None
    future_return: float | None


@dataclass(slots=True)
class TensorDataset:
    tensor: np.ndarray
    raw_tensor: np.ndarray
    returns: np.ndarray
    stock_codes: list[str]
    factor_names: list[str]
    dates: list[str]
    industries: dict[str, str | None]


def _parse_float(value: str | None) -> float | None:
    if value is None:
        return None
    stripped = value.strip()
    if not stripped:
        return None
    return float(stripped)


def _normalize_date(raw_value: str) -> str:
    return date.fromisoformat(raw_value.strip()).isoformat()


def load_factor_records(config: DataConfig) -> list[NormalizedRecord]:
    path = Path(config.path)
    if not path.exists():
        raise FileNotFoundError(f"Data file not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("Input CSV is missing a header row.")
        fieldnames = set(reader.fieldnames)

        required_columns = {config.stock_column, config.date_column}
        if config.industry_column:
            required_columns.add(config.industry_column)
        if config.return_column:
            required_columns.add(config.return_column)
        if config.format == "wide":
            required_columns.update(config.factor_columns)
        else:
            required_columns.update({config.factor_name_column or "", config.factor_value_column or ""})
        missing = [column for column in required_columns if column and column not in fieldnames]
        if missing:
            raise ValueError(f"Missing required columns: {', '.join(sorted(missing))}")

        records: list[NormalizedRecord] = []
        for row in reader:
            stock_code = row[config.stock_column].strip()
            trade_date = _normalize_date(row[config.date_column])
            industry = row[config.industry_column].strip() if config.industry_column and row[config.industry_column] else None
            future_return = _parse_float(row[config.return_column]) if config.return_column else None

            if config.format == "wide":
                for factor_column in config.factor_columns:
                    factor_value = _parse_float(row[factor_column])
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
                factor_name = row[config.factor_name_column or ""].strip()
                factor_value = _parse_float(row[config.factor_value_column or ""])
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


def _forward_backward_fill(values: np.ndarray) -> np.ndarray:
    filled = values.copy()
    last = np.nan
    for index, value in enumerate(filled):
        if np.isnan(value):
            if not np.isnan(last):
                filled[index] = last
        else:
            last = value

    last = np.nan
    for index in range(len(filled) - 1, -1, -1):
        value = filled[index]
        if np.isnan(value):
            if not np.isnan(last):
                filled[index] = last
        else:
            last = value
    return filled


def _winsorize(values: np.ndarray, lower: float, upper: float) -> np.ndarray:
    if values.size == 0:
        return values
    low = np.quantile(values, lower)
    high = np.quantile(values, upper)
    return np.clip(values, low, high)


def _zscore(values: np.ndarray) -> np.ndarray:
    if values.size == 0:
        return values
    mean = values.mean()
    std = values.std()
    if std == 0:
        return np.zeros_like(values)
    return (values - mean) / std


def build_tensor_dataset(records: list[NormalizedRecord], config: PreprocessConfig) -> TensorDataset:
    stock_codes = sorted({record.stock_code for record in records})
    factor_names = sorted({record.factor_name for record in records})
    dates = sorted({record.trade_date for record in records})

    stock_index = {stock_code: index for index, stock_code in enumerate(stock_codes)}
    factor_index = {factor_name: index for index, factor_name in enumerate(factor_names)}
    date_index = {trade_date: index for index, trade_date in enumerate(dates)}

    tensor = np.full((len(stock_codes), len(factor_names), len(dates)), np.nan, dtype=float)
    returns = np.full((len(stock_codes), len(dates)), np.nan, dtype=float)
    industry_votes: dict[str, list[str]] = defaultdict(list)
    seen_factor_keys: set[tuple[str, str, str]] = set()
    seen_return_keys: dict[tuple[str, str], float] = {}

    for record in records:
        s_idx = stock_index[record.stock_code]
        f_idx = factor_index[record.factor_name]
        d_idx = date_index[record.trade_date]
        factor_key = (record.stock_code, record.factor_name, record.trade_date)
        if factor_key in seen_factor_keys:
            raise ValueError(f"Duplicate factor observation detected for {factor_key}.")
        seen_factor_keys.add(factor_key)
        tensor[s_idx, f_idx, d_idx] = record.factor_value

        if record.industry:
            industry_votes[record.stock_code].append(record.industry)
        if record.future_return is not None:
            return_key = (record.stock_code, record.trade_date)
            prior = seen_return_keys.get(return_key)
            if prior is not None and not np.isclose(prior, record.future_return):
                raise ValueError(f"Conflicting future returns detected for {return_key}.")
            seen_return_keys[return_key] = record.future_return
            returns[s_idx, d_idx] = record.future_return

    raw_tensor = tensor.copy()

    stock_missing = np.isnan(tensor).mean(axis=(1, 2))
    factor_missing = np.isnan(tensor).mean(axis=(0, 2))
    stock_keep = stock_missing <= config.max_missing_ratio
    factor_keep = factor_missing <= config.max_missing_ratio
    if stock_keep.sum() < 2 or factor_keep.sum() < 2:
        raise ValueError("Missing-value filtering removed too many stocks or factors.")

    tensor = tensor[stock_keep][:, factor_keep, :]
    raw_tensor = raw_tensor[stock_keep][:, factor_keep, :]
    returns = returns[stock_keep]
    stock_codes = [stock_code for stock_code, keep in zip(stock_codes, stock_keep) if keep]
    factor_names = [factor_name for factor_name, keep in zip(factor_names, factor_keep) if keep]

    industries: dict[str, str | None] = {}
    for stock_code in stock_codes:
        votes = industry_votes.get(stock_code, [])
        industries[stock_code] = Counter(votes).most_common(1)[0][0] if votes else None

    stock_index = {stock_code: index for index, stock_code in enumerate(stock_codes)}
    industry_groups: dict[str, list[int]] = defaultdict(list)
    for stock_code, industry in industries.items():
        if industry:
            industry_groups[industry].append(stock_index[stock_code])

    for s_idx in range(tensor.shape[0]):
        for f_idx in range(tensor.shape[1]):
            tensor[s_idx, f_idx, :] = _forward_backward_fill(tensor[s_idx, f_idx, :])

    for f_idx in range(tensor.shape[1]):
        for d_idx in range(tensor.shape[2]):
            column = tensor[:, f_idx, d_idx]
            missing_positions = np.where(np.isnan(column))[0]
            for s_idx in missing_positions:
                stock_code = stock_codes[s_idx]
                industry = industries.get(stock_code)
                fill_value = np.nan
                if industry and industry_groups[industry]:
                    peer_values = column[industry_groups[industry]]
                    peer_values = peer_values[~np.isnan(peer_values)]
                    if peer_values.size:
                        fill_value = float(np.median(peer_values))
                if np.isnan(fill_value):
                    available = column[~np.isnan(column)]
                    if available.size:
                        fill_value = float(np.median(available))
                if np.isnan(fill_value):
                    factor_slice = tensor[:, f_idx, :]
                    available = factor_slice[~np.isnan(factor_slice)]
                    fill_value = float(np.median(available)) if available.size else 0.0
                tensor[s_idx, f_idx, d_idx] = fill_value

    lower, upper = config.winsor_limits
    for f_idx in range(tensor.shape[1]):
        for d_idx in range(tensor.shape[2]):
            column = tensor[:, f_idx, d_idx]
            tensor[:, f_idx, d_idx] = _zscore(_winsorize(column, lower, upper))

    return TensorDataset(
        tensor=tensor,
        raw_tensor=raw_tensor,
        returns=returns,
        stock_codes=stock_codes,
        factor_names=factor_names,
        dates=dates,
        industries=industries,
    )
