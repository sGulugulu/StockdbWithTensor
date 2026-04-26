from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

import numpy as np

from .config import PreprocessConfig
from .preprocess import preprocess_tensor


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
    preprocess_summary: dict[str, object]


def slice_tensor_dataset(
    dataset: TensorDataset,
    *,
    stock_codes: list[str],
    dates: list[str],
) -> TensorDataset:
    stock_index = {stock_code: index for index, stock_code in enumerate(dataset.stock_codes)}
    date_index = {trade_date: index for index, trade_date in enumerate(dataset.dates)}

    stock_positions = [stock_index[stock_code] for stock_code in stock_codes]
    date_positions = [date_index[trade_date] for trade_date in dates]
    sliced_tensor = dataset.tensor[np.ix_(stock_positions, np.arange(len(dataset.factor_names)), date_positions)]
    sliced_raw_tensor = dataset.raw_tensor[np.ix_(stock_positions, np.arange(len(dataset.factor_names)), date_positions)]
    sliced_returns = dataset.returns[np.ix_(stock_positions, date_positions)]

    return TensorDataset(
        tensor=sliced_tensor.copy(),
        raw_tensor=sliced_raw_tensor.copy(),
        returns=sliced_returns.copy(),
        stock_codes=list(stock_codes),
        factor_names=list(dataset.factor_names),
        dates=list(dates),
        industries={stock_code: dataset.industries.get(stock_code) for stock_code in stock_codes},
        preprocess_summary={**dataset.preprocess_summary},
    )


def build_raw_tensor_dataset(records: list[NormalizedRecord]) -> TensorDataset:
    stock_codes = sorted({record.stock_code for record in records})
    factor_names = sorted({record.factor_name for record in records})
    dates = sorted({record.trade_date for record in records})

    stock_index = {stock_code: index for index, stock_code in enumerate(stock_codes)}
    factor_index = {factor_name: index for index, factor_name in enumerate(factor_names)}
    date_index = {trade_date: index for index, trade_date in enumerate(dates)}

    tensor = np.full((len(stock_codes), len(factor_names), len(dates)), np.nan, dtype=float)
    returns = np.full((len(stock_codes), len(dates)), np.nan, dtype=float)
    industry_votes: dict[str, list[str]] = {}
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
            industry_votes.setdefault(record.stock_code, []).append(record.industry)
        if record.future_return is not None:
            return_key = (record.stock_code, record.trade_date)
            prior = seen_return_keys.get(return_key)
            if prior is not None and not np.isclose(prior, record.future_return):
                raise ValueError(f"Conflicting future returns detected for {return_key}.")
            seen_return_keys[return_key] = record.future_return
            returns[s_idx, d_idx] = record.future_return

    industries = {
        stock_code: Counter(industry_votes.get(stock_code, [])).most_common(1)[0][0]
        if industry_votes.get(stock_code)
        else None
        for stock_code in stock_codes
    }
    return TensorDataset(
        tensor=tensor.copy(),
        raw_tensor=tensor.copy(),
        returns=returns,
        stock_codes=stock_codes,
        factor_names=factor_names,
        dates=dates,
        industries=industries,
        preprocess_summary={},
    )


def build_tensor_dataset(records: list[NormalizedRecord], config: PreprocessConfig) -> TensorDataset:
    raw_dataset = build_raw_tensor_dataset(records)
    preprocessed = preprocess_tensor(
        tensor=raw_dataset.tensor,
        raw_tensor=raw_dataset.raw_tensor,
        returns=raw_dataset.returns,
        stock_codes=raw_dataset.stock_codes,
        factor_names=raw_dataset.factor_names,
        dates=raw_dataset.dates,
        industries=raw_dataset.industries,
        config=config,
    )
    return TensorDataset(
        tensor=preprocessed.tensor,
        raw_tensor=preprocessed.raw_tensor,
        returns=preprocessed.returns,
        stock_codes=preprocessed.stock_codes,
        factor_names=preprocessed.factor_names,
        dates=raw_dataset.dates,
        industries=preprocessed.industries,
        preprocess_summary=preprocessed.summary,
    )
