from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import PreprocessConfig


@dataclass(slots=True)
class PreprocessState:
    train_stock_codes: list[str]
    kept_factor_names: list[str]
    factor_low: np.ndarray
    factor_high: np.ndarray
    factor_mean: np.ndarray
    factor_std: np.ndarray
    factor_global_median: np.ndarray
    factor_date_medians: dict[str, np.ndarray]
    last_train_values: dict[tuple[str, str], float]
    industries: dict[str, str | None]


@dataclass(slots=True)
class PreprocessedTensor:
    tensor: np.ndarray
    raw_tensor: np.ndarray
    returns: np.ndarray
    stock_codes: list[str]
    factor_names: list[str]
    industries: dict[str, str | None]
    summary: dict[str, object]


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


def _forward_fill_with_anchor(values: np.ndarray, anchor: float | None) -> np.ndarray:
    filled = values.copy()
    last = anchor if anchor is not None else np.nan
    for index, value in enumerate(filled):
        if np.isnan(value):
            if not np.isnan(last):
                filled[index] = last
        else:
            last = value
    return filled


def _filter_train_axes(
    tensor: np.ndarray,
    raw_tensor: np.ndarray,
    returns: np.ndarray,
    stock_codes: list[str],
    factor_names: list[str],
    max_missing_ratio: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[str], list[str]]:
    stock_missing = np.isnan(tensor).mean(axis=(1, 2))
    factor_missing = np.isnan(tensor).mean(axis=(0, 2))
    stock_keep = stock_missing <= max_missing_ratio
    factor_keep = factor_missing <= max_missing_ratio
    if stock_keep.sum() < 1 or factor_keep.sum() < 1:
        raise ValueError("Missing-value filtering removed too many stocks or factors.")

    filtered_tensor = tensor[stock_keep][:, factor_keep, :]
    filtered_raw_tensor = raw_tensor[stock_keep][:, factor_keep, :]
    filtered_returns = returns[stock_keep]
    filtered_stocks = [stock_code for stock_code, keep in zip(stock_codes, stock_keep) if keep]
    filtered_factors = [factor_name for factor_name, keep in zip(factor_names, factor_keep) if keep]
    return filtered_tensor, filtered_raw_tensor, filtered_returns, filtered_stocks, filtered_factors


def _compute_train_fill_stats(tensor: np.ndarray, dates: list[str]) -> tuple[dict[str, np.ndarray], np.ndarray]:
    factor_date_medians: dict[str, np.ndarray] = {}
    factor_global_median = np.zeros(tensor.shape[1], dtype=float)
    for factor_index in range(tensor.shape[1]):
        factor_values = tensor[:, factor_index, :]
        finite = factor_values[~np.isnan(factor_values)]
        factor_global_median[factor_index] = float(np.median(finite)) if finite.size else 0.0
    for date_index, trade_date in enumerate(dates):
        medians = np.zeros(tensor.shape[1], dtype=float)
        for factor_index in range(tensor.shape[1]):
            column = tensor[:, factor_index, date_index]
            finite = column[~np.isnan(column)]
            medians[factor_index] = float(np.median(finite)) if finite.size else factor_global_median[factor_index]
        factor_date_medians[trade_date] = medians
    return factor_date_medians, factor_global_median


def _fill_train_tensor(
    tensor: np.ndarray,
    stock_codes: list[str],
    factor_names: list[str],
    dates: list[str],
) -> tuple[np.ndarray, dict[str, np.ndarray], np.ndarray, dict[tuple[str, str], float]]:
    filled = tensor.copy()
    for stock_index in range(filled.shape[0]):
        for factor_index in range(filled.shape[1]):
            filled[stock_index, factor_index, :] = _forward_backward_fill(filled[stock_index, factor_index, :])

    factor_date_medians, factor_global_median = _compute_train_fill_stats(filled, dates)
    for factor_index in range(filled.shape[1]):
        for date_index, trade_date in enumerate(dates):
            column = filled[:, factor_index, date_index]
            missing_positions = np.where(np.isnan(column))[0]
            if missing_positions.size:
                column[missing_positions] = factor_date_medians[trade_date][factor_index]
                filled[:, factor_index, date_index] = column

    last_train_values: dict[tuple[str, str], float] = {}
    for stock_index, stock_code in enumerate(stock_codes):
        for factor_index, factor_name in enumerate(factor_names):
            values = filled[stock_index, factor_index, :]
            finite_positions = np.where(~np.isnan(values))[0]
            if finite_positions.size:
                last_train_values[(stock_code, factor_name)] = float(values[finite_positions[-1]])
    return filled, factor_date_medians, factor_global_median, last_train_values


def _fit_normalization_stats(
    filled_train_tensor: np.ndarray,
    winsor_limits: tuple[float, float],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    factor_low = np.zeros(filled_train_tensor.shape[1], dtype=float)
    factor_high = np.zeros(filled_train_tensor.shape[1], dtype=float)
    factor_mean = np.zeros(filled_train_tensor.shape[1], dtype=float)
    factor_std = np.zeros(filled_train_tensor.shape[1], dtype=float)
    for factor_index in range(filled_train_tensor.shape[1]):
        values = filled_train_tensor[:, factor_index, :].reshape(-1)
        factor_low[factor_index] = float(np.quantile(values, winsor_limits[0]))
        factor_high[factor_index] = float(np.quantile(values, winsor_limits[1]))
        clipped = np.clip(values, factor_low[factor_index], factor_high[factor_index])
        factor_mean[factor_index] = float(clipped.mean())
        std = float(clipped.std())
        factor_std[factor_index] = std if std > 0 else 1.0
    return factor_low, factor_high, factor_mean, factor_std


def fit_preprocess_state(
    tensor: np.ndarray,
    raw_tensor: np.ndarray,
    returns: np.ndarray,
    stock_codes: list[str],
    factor_names: list[str],
    dates: list[str],
    industries: dict[str, str | None],
    config: PreprocessConfig,
) -> tuple[PreprocessState, PreprocessedTensor]:
    filtered_tensor, filtered_raw_tensor, filtered_returns, filtered_stocks, filtered_factors = _filter_train_axes(
        tensor,
        raw_tensor,
        returns,
        stock_codes,
        factor_names,
        config.max_missing_ratio,
    )
    filled_train, factor_date_medians, factor_global_median, last_train_values = _fill_train_tensor(
        filtered_tensor,
        filtered_stocks,
        filtered_factors,
        dates,
    )
    factor_low, factor_high, factor_mean, factor_std = _fit_normalization_stats(
        filled_train,
        config.winsor_limits,
    )

    normalized_train = np.zeros_like(filled_train)
    for factor_index in range(filled_train.shape[1]):
        clipped = np.clip(filled_train[:, factor_index, :], factor_low[factor_index], factor_high[factor_index])
        normalized_train[:, factor_index, :] = (clipped - factor_mean[factor_index]) / factor_std[factor_index]

    state = PreprocessState(
        train_stock_codes=filtered_stocks,
        kept_factor_names=filtered_factors,
        factor_low=factor_low,
        factor_high=factor_high,
        factor_mean=factor_mean,
        factor_std=factor_std,
        factor_global_median=factor_global_median,
        factor_date_medians=factor_date_medians,
        last_train_values=last_train_values,
        industries={stock_code: industries.get(stock_code) for stock_code in stock_codes},
    )
    summary = {
        "max_missing_ratio": config.max_missing_ratio,
        "winsor_limits": [config.winsor_limits[0], config.winsor_limits[1]],
        "fill_strategy": config.fill_strategy,
        "standardize_method": config.standardize_method,
        "initial_stock_count": len(stock_codes),
        "initial_factor_count": len(factor_names),
        "filtered_stock_count": len(filtered_stocks),
        "filtered_factor_count": len(filtered_factors),
        "date_count": len(dates),
        "fit_scope": "train_only",
        "applied_partition": "train",
    }
    return state, PreprocessedTensor(
        tensor=normalized_train,
        raw_tensor=filtered_raw_tensor,
        returns=filtered_returns,
        stock_codes=filtered_stocks,
        factor_names=filtered_factors,
        industries=state.industries,
        summary=summary,
    )


def apply_preprocess_state(
    tensor: np.ndarray,
    raw_tensor: np.ndarray,
    returns: np.ndarray,
    stock_codes: list[str],
    factor_names: list[str],
    dates: list[str],
    industries: dict[str, str | None],
    state: PreprocessState,
    config: PreprocessConfig,
    *,
    partition_name: str,
) -> PreprocessedTensor:
    factor_positions = [factor_names.index(factor_name) for factor_name in state.kept_factor_names]
    kept_tensor = tensor[:, factor_positions, :].copy()
    kept_raw_tensor = raw_tensor[:, factor_positions, :].copy()
    kept_factor_names = [factor_names[index] for index in factor_positions]

    if all(stock_code in state.train_stock_codes for stock_code in stock_codes):
        keep_stock_positions = [index for index, stock_code in enumerate(stock_codes) if stock_code in state.train_stock_codes]
        kept_tensor = kept_tensor[keep_stock_positions]
        kept_raw_tensor = kept_raw_tensor[keep_stock_positions]
        kept_returns = returns[keep_stock_positions]
        kept_stock_codes = [stock_codes[index] for index in keep_stock_positions]
    else:
        kept_returns = returns.copy()
        kept_stock_codes = list(stock_codes)

    filled = kept_tensor.copy()
    for stock_index, stock_code in enumerate(kept_stock_codes):
        for factor_index, factor_name in enumerate(kept_factor_names):
            if partition_name == "train":
                filled[stock_index, factor_index, :] = _forward_backward_fill(filled[stock_index, factor_index, :])
            else:
                filled[stock_index, factor_index, :] = _forward_fill_with_anchor(
                    filled[stock_index, factor_index, :],
                    state.last_train_values.get((stock_code, factor_name)),
                )

    for factor_index in range(filled.shape[1]):
        for date_index, trade_date in enumerate(dates):
            column = filled[:, factor_index, date_index]
            missing_positions = np.where(np.isnan(column))[0]
            if missing_positions.size:
                fill_value = state.factor_date_medians.get(trade_date, state.factor_global_median)[factor_index]
                column[missing_positions] = fill_value
                filled[:, factor_index, date_index] = column

    normalized = np.zeros_like(filled)
    for factor_index in range(filled.shape[1]):
        clipped = np.clip(filled[:, factor_index, :], state.factor_low[factor_index], state.factor_high[factor_index])
        normalized[:, factor_index, :] = (clipped - state.factor_mean[factor_index]) / state.factor_std[factor_index]

    summary = {
        "max_missing_ratio": config.max_missing_ratio,
        "winsor_limits": [config.winsor_limits[0], config.winsor_limits[1]],
        "fill_strategy": config.fill_strategy,
        "standardize_method": config.standardize_method,
        "initial_stock_count": len(stock_codes),
        "initial_factor_count": len(factor_names),
        "filtered_stock_count": len(kept_stock_codes),
        "filtered_factor_count": len(kept_factor_names),
        "date_count": len(dates),
        "fit_scope": "train_only",
        "applied_partition": partition_name,
    }
    return PreprocessedTensor(
        tensor=normalized,
        raw_tensor=kept_raw_tensor,
        returns=kept_returns,
        stock_codes=kept_stock_codes,
        factor_names=kept_factor_names,
        industries={stock_code: industries.get(stock_code) for stock_code in kept_stock_codes},
        summary=summary,
    )


def preprocess_tensor(
    tensor: np.ndarray,
    raw_tensor: np.ndarray,
    returns: np.ndarray,
    stock_codes: list[str],
    factor_names: list[str],
    dates: list[str],
    industries: dict[str, str | None],
    config: PreprocessConfig,
) -> PreprocessedTensor:
    state, _ = fit_preprocess_state(
        tensor,
        raw_tensor,
        returns,
        stock_codes,
        factor_names,
        dates,
        industries,
        config,
    )
    return apply_preprocess_state(
        tensor,
        raw_tensor,
        returns,
        stock_codes,
        factor_names,
        dates,
        industries,
        state,
        config,
        partition_name="train",
    )
