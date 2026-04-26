from __future__ import annotations

from dataclasses import dataclass
from collections import defaultdict
from itertools import combinations
from typing import Callable

import numpy as np

from .dataset import TensorDataset
from .models import ModelResult


@dataclass(slots=True)
class PairScore:
    left: str
    right: str
    score: float


@dataclass(slots=True)
class SelectionRecord:
    trade_date: str
    stock_code: str
    model: str
    rank_label: str
    market_id: str
    universe_id: str
    total_score: float
    stock_score: float
    selection_signal: float
    time_regime_score: float
    cluster_label: int
    top_factor_1: str
    top_factor_1_score: float
    top_factor_2: str
    top_factor_2_score: float
    top_factor_3: str
    top_factor_3_score: float
    industry: str | None
    future_return: float


@dataclass(slots=True)
class PortfolioDailyRecord:
    trade_date: str
    model: str
    top_n: int
    daily_return: float
    cumulative_nav: float
    turnover: float
    drawdown: float


@dataclass(slots=True)
class PortfolioSummary:
    model: str
    top_n: int
    observation_count: int
    mean_daily_return: float
    cumulative_return: float
    annualized_volatility: float
    sharpe_ratio: float
    max_drawdown: float
    average_turnover: float


def _pearson_corr(left: np.ndarray, right: np.ndarray) -> float:
    if left.size < 2 or right.size < 2:
        return float("nan")
    left_centered = left - left.mean()
    right_centered = right - right.mean()
    denominator = np.linalg.norm(left_centered) * np.linalg.norm(right_centered)
    if denominator == 0:
        return float("nan")
    return float(np.dot(left_centered, right_centered) / denominator)


def _rank(values: np.ndarray) -> np.ndarray:
    order = np.argsort(values, kind="mergesort")
    ranks = np.empty(values.size, dtype=float)
    ranks[order] = np.arange(values.size, dtype=float)
    return ranks


def _spearman_corr(left: np.ndarray, right: np.ndarray) -> float:
    return _pearson_corr(_rank(left), _rank(right))


def compute_quality_metrics(tensor: np.ndarray, result: ModelResult, returns: np.ndarray) -> dict[str, float]:
    error = tensor - result.reconstruction
    mse = float(np.mean(error ** 2))
    rmse = float(np.sqrt(mse))
    total = tensor - tensor.mean()
    explained = 1.0 - (np.sum(error ** 2) / max(np.sum(total ** 2), 1e-8))
    original_params = int(np.prod(tensor.shape))
    compression_ratio = float(original_params / max(result.param_count, 1))
    n_obs = original_params
    bic = float(n_obs * np.log(max(mse, 1e-12)) + result.param_count * np.log(max(n_obs, 2)))

    ic_values: list[float] = []
    rank_ic_values: list[float] = []
    for date_idx in range(returns.shape[1]):
        mask = ~np.isnan(returns[:, date_idx])
        if mask.sum() < 2:
            continue
        signal_slice = result.selection_signal[:, date_idx][mask]
        return_slice = returns[:, date_idx][mask]
        ic = _pearson_corr(signal_slice, return_slice)
        rank_ic = _spearman_corr(signal_slice, return_slice)
        if not np.isnan(ic):
            ic_values.append(ic)
        if not np.isnan(rank_ic):
            rank_ic_values.append(rank_ic)

    ic_mean = float(np.mean(ic_values)) if ic_values else float("nan")
    rank_ic_mean = float(np.mean(rank_ic_values)) if rank_ic_values else float("nan")
    ir = float(np.mean(ic_values) / np.std(ic_values)) if len(ic_values) > 1 and np.std(ic_values) != 0 else float("nan")

    return {
        "mse": mse,
        "rmse": rmse,
        "explained_variance": float(explained),
        "compression_ratio": compression_ratio,
        "bic": bic,
        "ic_mean": ic_mean,
        "rank_ic_mean": rank_ic_mean,
        "ir": ir,
    }


def _normalize_columns(matrix: np.ndarray) -> np.ndarray:
    norms = np.linalg.norm(matrix, axis=0, keepdims=True)
    norms[norms == 0] = 1.0
    return matrix / norms


def factor_alignment_score(left: np.ndarray, right: np.ndarray) -> float:
    left_normalized = _normalize_columns(left)
    right_normalized = _normalize_columns(right)
    similarity = np.abs(left_normalized.T @ right_normalized)
    used_left: set[int] = set()
    used_right: set[int] = set()
    scores: list[float] = []
    for _ in range(min(similarity.shape[0], similarity.shape[1])):
        best_value = -1.0
        best_pair: tuple[int, int] | None = None
        for i_idx in range(similarity.shape[0]):
            if i_idx in used_left:
                continue
            for j_idx in range(similarity.shape[1]):
                if j_idx in used_right:
                    continue
                value = float(similarity[i_idx, j_idx])
                if value > best_value:
                    best_value = value
                    best_pair = (i_idx, j_idx)
        if best_pair is None:
            break
        used_left.add(best_pair[0])
        used_right.add(best_pair[1])
        scores.append(best_value)
    return float(np.mean(scores)) if scores else float("nan")


def compute_rolling_stability(
    dataset: TensorDataset,
    window_size: int,
    fit_window_model: Callable[[np.ndarray], ModelResult],
) -> float:
    if window_size < 2 or dataset.tensor.shape[2] < window_size + 1:
        return float("nan")

    factor_windows: list[np.ndarray] = []
    for start in range(0, dataset.tensor.shape[2] - window_size + 1):
        subtensor = dataset.tensor[:, :, start : start + window_size]
        window_result = fit_window_model(subtensor)
        factor_windows.append(window_result.factor_loadings)
    if len(factor_windows) < 2:
        return float("nan")

    scores = [
        factor_alignment_score(left, right)
        for left, right in zip(factor_windows, factor_windows[1:])
    ]
    scores = [score for score in scores if not np.isnan(score)]
    return float(np.mean(scores)) if scores else float("nan")


def top_similarity_pairs(labels: list[str], loadings: np.ndarray, top_k: int) -> list[PairScore]:
    if loadings.shape[0] < 2:
        return []
    pairs: list[PairScore] = []
    for left_idx, right_idx in combinations(range(loadings.shape[0]), 2):
        left = loadings[left_idx]
        right = loadings[right_idx]
        denominator = np.linalg.norm(left) * np.linalg.norm(right)
        score = 0.0 if denominator == 0 else float(np.dot(left, right) / denominator)
        pairs.append(PairScore(labels[left_idx], labels[right_idx], score))
    pairs.sort(key=lambda item: item.score, reverse=True)
    return pairs[:top_k]


def time_regime_shifts(dates: list[str], time_loadings: np.ndarray, top_k: int) -> list[PairScore]:
    if time_loadings.shape[0] < 2:
        return []
    shifts: list[PairScore] = []
    for idx in range(1, time_loadings.shape[0]):
        score = float(np.linalg.norm(time_loadings[idx] - time_loadings[idx - 1]))
        shifts.append(PairScore(dates[idx - 1], dates[idx], score))
    shifts.sort(key=lambda item: item.score, reverse=True)
    return shifts[:top_k]


def factor_importance_summary(factor_names: list[str], factor_loadings: np.ndarray) -> list[dict[str, float | str]]:
    importance = np.mean(np.abs(factor_loadings), axis=1)
    rows = [
        {"factor_name": name, "importance": float(score)}
        for name, score in zip(factor_names, importance)
    ]
    rows.sort(key=lambda item: float(item["importance"]), reverse=True)
    return rows


def build_selection_records(
    dataset: TensorDataset,
    result: ModelResult,
    market_id: str,
    universe_id: str,
    top_k_factors: int = 3,
) -> list[SelectionRecord]:
    selection_rows: list[SelectionRecord] = []
    for stock_idx, stock_code in enumerate(dataset.stock_codes):
        for date_idx, trade_date in enumerate(dataset.dates):
            factor_scores = result.factor_contribution[stock_idx, :, date_idx]
            top_indices = np.argsort(np.abs(factor_scores))[::-1][:top_k_factors]
            top_factors = [dataset.factor_names[index] for index in top_indices]
            top_scores = [float(factor_scores[index]) for index in top_indices]
            while len(top_factors) < 3:
                top_factors.append("")
            while len(top_scores) < 3:
                top_scores.append(0.0)
            selection_rows.append(
                SelectionRecord(
                    trade_date=trade_date,
                    stock_code=stock_code,
                    model=result.name,
                    rank_label=str(result.rank),
                    market_id=market_id,
                    universe_id=universe_id,
                    total_score=float(result.selection_signal[stock_idx, date_idx]),
                    stock_score=float(result.stock_score[stock_idx, date_idx]),
                    selection_signal=float(result.selection_signal[stock_idx, date_idx]),
                    time_regime_score=float(result.time_regime_score[date_idx]),
                    cluster_label=int(result.stock_cluster[stock_idx]),
                    top_factor_1=top_factors[0],
                    top_factor_1_score=top_scores[0],
                    top_factor_2=top_factors[1],
                    top_factor_2_score=top_scores[1],
                    top_factor_3=top_factors[2],
                    top_factor_3_score=top_scores[2],
                    industry=dataset.industries.get(stock_code),
                    future_return=float(dataset.returns[stock_idx, date_idx])
                    if not np.isnan(dataset.returns[stock_idx, date_idx])
                    else 0.0,
                )
            )
    selection_rows.sort(key=lambda item: (item.trade_date, -item.total_score, item.stock_code))
    return selection_rows


def build_candidate_pool(
    selection_rows_by_model: dict[str, list[SelectionRecord]],
    *,
    selection_top_n: int | None = None,
) -> list[dict[str, float | int | str]]:
    grouped: dict[tuple[str, str], list[SelectionRecord]] = defaultdict(list)
    for rows in selection_rows_by_model.values():
        for row in rows:
            grouped[(row.trade_date, row.stock_code)].append(row)

    candidate_rows: list[dict[str, float | int | str]] = []
    for (trade_date, stock_code), rows in grouped.items():
        rows.sort(key=lambda item: item.total_score, reverse=True)
        representative = rows[0]
        candidate_rows.append(
            {
                "trade_date": trade_date,
                "stock_code": stock_code,
                "market_id": representative.market_id,
                "universe_id": representative.universe_id,
                "model_count": len(rows),
                "models": ",".join(sorted({row.model for row in rows})),
                "total_score": float(np.mean([row.total_score for row in rows])),
                "stock_score": float(np.mean([row.stock_score for row in rows])),
                "selection_signal": float(np.mean([row.selection_signal for row in rows])),
                "time_regime_score": float(np.mean([row.time_regime_score for row in rows])),
                "cluster_label": representative.cluster_label,
                "top_factor_1": representative.top_factor_1,
                "top_factor_1_score": representative.top_factor_1_score,
                "top_factor_2": representative.top_factor_2,
                "top_factor_2_score": representative.top_factor_2_score,
                "top_factor_3": representative.top_factor_3,
                "top_factor_3_score": representative.top_factor_3_score,
            }
        )
    candidate_rows.sort(key=lambda item: (str(item["trade_date"]), -float(item["total_score"]), str(item["stock_code"])))
    if selection_top_n is not None and selection_top_n > 0:
        filtered_rows: list[dict[str, float | int | str]] = []
        current_date = None
        current_rows: list[dict[str, float | int | str]] = []
        for row in candidate_rows:
            trade_date = str(row["trade_date"])
            if current_date is None:
                current_date = trade_date
            if trade_date != current_date:
                filtered_rows.extend(current_rows[:selection_top_n])
                current_rows = []
                current_date = trade_date
            current_rows.append(row)
        if current_rows:
            filtered_rows.extend(current_rows[:selection_top_n])
        candidate_rows = filtered_rows
    return candidate_rows


def build_portfolio_backtest(
    selection_rows_by_model: dict[str, list[SelectionRecord]],
    *,
    selection_top_n: int,
    quantile_count: int = 5,
    transaction_cost_bps: float = 0.0,
    benchmark_returns: dict[str, float] | None = None,
) -> tuple[
    list[dict[str, float | int | str]],
    dict[str, list[dict[str, float | int | str]]],
    dict[str, list[dict[str, float | int | str]]],
    dict[str, list[dict[str, float | int | str]]],
    dict[str, list[dict[str, float | int | str]]],
    dict[str, list[dict[str, float | int | str]]],
    dict[str, list[dict[str, float | int | str]]],
]:
    portfolio_metrics: list[dict[str, float | int | str]] = []
    group_returns: dict[str, list[dict[str, float | int | str]]] = {}
    drawdowns: dict[str, list[dict[str, float | int | str]]] = {}
    exposures: dict[str, list[dict[str, float | int | str]]] = {}
    quantile_returns: dict[str, list[dict[str, float | int | str]]] = {}
    long_short_returns: dict[str, list[dict[str, float | int | str]]] = {}
    cost_adjusted_returns: dict[str, list[dict[str, float | int | str]]] = {}
    excess_returns_output: dict[str, list[dict[str, float | int | str]]] = {}

    for model_name, rows in selection_rows_by_model.items():
        by_date: dict[str, list[SelectionRecord]] = defaultdict(list)
        for row in rows:
            by_date[row.trade_date].append(row)
        ordered_dates = sorted(by_date)
        cumulative_nav = 1.0
        peak_nav = 1.0
        previous_holdings: set[str] = set()
        daily_records: list[dict[str, float | int | str]] = []
        drawdown_records: list[dict[str, float | int | str]] = []
        industry_counts: defaultdict[str, int] = defaultdict(int)
        style_counts: defaultdict[str, int] = defaultdict(int)
        turnover_values: list[float] = []
        daily_returns: list[float] = []
        quantile_navs = [1.0 for _ in range(max(quantile_count, 1))]
        long_short_nav = 1.0
        long_short_peak = 1.0
        cost_adjusted_nav = 1.0
        cost_adjusted_peak = 1.0
        excess_nav = 1.0
        excess_peak = 1.0
        quantile_records: list[dict[str, float | int | str]] = []
        long_short_records: list[dict[str, float | int | str]] = []
        cost_adjusted_records: list[dict[str, float | int | str]] = []
        excess_records: list[dict[str, float | int | str]] = []

        for trade_date in ordered_dates:
            full_ranked_rows = sorted(by_date[trade_date], key=lambda item: item.total_score, reverse=True)
            ranked_rows = full_ranked_rows[:selection_top_n]
            holdings = {row.stock_code for row in ranked_rows}
            daily_return = float(np.mean([row.future_return for row in ranked_rows])) if ranked_rows else 0.0
            daily_returns.append(daily_return)
            cumulative_nav *= 1.0 + daily_return
            peak_nav = max(peak_nav, cumulative_nav)
            drawdown = 0.0 if peak_nav == 0 else (cumulative_nav / peak_nav) - 1.0
            if not previous_holdings:
                turnover = 1.0 if holdings else 0.0
            else:
                overlap = len(previous_holdings & holdings)
                turnover = 1.0 - (overlap / max(len(holdings), 1))
            turnover_values.append(turnover)
            previous_holdings = holdings
            transaction_cost = turnover * transaction_cost_bps / 10000.0
            cost_adjusted_daily_return = daily_return - transaction_cost
            cost_adjusted_nav *= 1.0 + cost_adjusted_daily_return
            cost_adjusted_peak = max(cost_adjusted_peak, cost_adjusted_nav)
            cost_adjusted_drawdown = 0.0 if cost_adjusted_peak == 0 else (cost_adjusted_nav / cost_adjusted_peak) - 1.0

            benchmark_return = 0.0 if benchmark_returns is None else float(benchmark_returns.get(trade_date, 0.0))
            excess_return = daily_return - benchmark_return
            excess_nav *= 1.0 + excess_return
            excess_peak = max(excess_peak, excess_nav)
            excess_drawdown = 0.0 if excess_peak == 0 else (excess_nav / excess_peak) - 1.0

            for row in ranked_rows:
                industry_counts[row.industry or "UNKNOWN"] += 1
                style_counts[row.top_factor_1 or "UNKNOWN"] += 1

            daily_records.append(
                {
                    "trade_date": trade_date,
                    "model": model_name,
                    "top_n": selection_top_n,
                    "daily_return": daily_return,
                    "cumulative_nav": cumulative_nav,
                    "turnover": turnover,
                    "drawdown": drawdown,
                }
            )
            cost_adjusted_records.append(
                {
                    "trade_date": trade_date,
                    "model": model_name,
                    "top_n": selection_top_n,
                    "gross_return": daily_return,
                    "transaction_cost": transaction_cost,
                    "net_return": cost_adjusted_daily_return,
                    "cumulative_nav": cost_adjusted_nav,
                    "drawdown": cost_adjusted_drawdown,
                }
            )
            drawdown_records.append(
                {
                    "trade_date": trade_date,
                    "model": model_name,
                    "cumulative_nav": cumulative_nav,
                    "drawdown": drawdown,
                }
            )
            excess_records.append(
                {
                    "trade_date": trade_date,
                    "model": model_name,
                    "portfolio_return": daily_return,
                    "benchmark_return": benchmark_return,
                    "excess_return": excess_return,
                    "cumulative_nav": excess_nav,
                    "drawdown": excess_drawdown,
                }
            )

            bucket_count = max(min(quantile_count, len(full_ranked_rows)), 1)
            bucket_size = max(len(full_ranked_rows) // bucket_count, 1)
            quantile_slices: list[list[SelectionRecord]] = []
            start_index = 0
            for bucket_index in range(bucket_count):
                end_index = len(full_ranked_rows) if bucket_index == bucket_count - 1 else min(start_index + bucket_size, len(full_ranked_rows))
                quantile_slices.append(full_ranked_rows[start_index:end_index])
                start_index = end_index
            for bucket_index, bucket_rows in enumerate(quantile_slices):
                bucket_return = float(np.mean([row.future_return for row in bucket_rows])) if bucket_rows else 0.0
                quantile_navs[bucket_index] *= 1.0 + bucket_return
                quantile_records.append(
                    {
                        "trade_date": trade_date,
                        "model": model_name,
                        "quantile": bucket_index + 1,
                        "daily_return": bucket_return,
                        "cumulative_nav": quantile_navs[bucket_index],
                    }
                )

            if bucket_count > 0:
                top_bucket_return = float(quantile_records[-bucket_count]["daily_return"])
                bottom_bucket_return = float(quantile_records[-1]["daily_return"])
            else:
                top_bucket_return = 0.0
                bottom_bucket_return = 0.0
            long_short_return = float(top_bucket_return) - float(bottom_bucket_return)
            long_short_nav *= 1.0 + long_short_return
            long_short_peak = max(long_short_peak, long_short_nav)
            long_short_drawdown = 0.0 if long_short_peak == 0 else (long_short_nav / long_short_peak) - 1.0
            long_short_records.append(
                {
                    "trade_date": trade_date,
                    "model": model_name,
                    "long_quantile": 1,
                    "short_quantile": bucket_count,
                    "long_return": float(top_bucket_return),
                    "short_return": float(bottom_bucket_return),
                    "long_short_return": long_short_return,
                    "cumulative_nav": long_short_nav,
                    "drawdown": long_short_drawdown,
                }
            )

        mean_daily_return = float(np.mean(daily_returns)) if daily_returns else 0.0
        volatility = float(np.std(daily_returns)) if len(daily_returns) > 1 else 0.0
        annualized_volatility = volatility * np.sqrt(252.0)
        sharpe_ratio = 0.0 if volatility == 0 else float(mean_daily_return / volatility * np.sqrt(252.0))
        max_drawdown = float(min((record["drawdown"] for record in drawdown_records), default=0.0))
        average_turnover = float(np.mean(turnover_values)) if turnover_values else 0.0

        portfolio_metrics.append(
            {
                "model": model_name,
                "top_n": selection_top_n,
                "observation_count": len(daily_records),
                "mean_daily_return": mean_daily_return,
                "cumulative_return": cumulative_nav - 1.0,
                "annualized_volatility": annualized_volatility,
                "sharpe_ratio": sharpe_ratio,
                "max_drawdown": max_drawdown,
                "average_turnover": average_turnover,
            }
        )
        group_returns[model_name] = daily_records
        drawdowns[model_name] = drawdown_records
        quantile_returns[model_name] = quantile_records
        long_short_returns[model_name] = long_short_records
        cost_adjusted_returns[model_name] = cost_adjusted_records
        excess_returns_output[model_name] = excess_records

        total_slots = max(sum(industry_counts.values()), 1)
        industry_rows = [
            {
                "model": model_name,
                "exposure_type": "industry",
                "name": name,
                "weight": count / total_slots,
            }
            for name, count in sorted(industry_counts.items(), key=lambda item: item[1], reverse=True)
        ]
        style_rows = [
            {
                "model": model_name,
                "exposure_type": "style",
                "name": name,
                "weight": count / total_slots,
            }
            for name, count in sorted(style_counts.items(), key=lambda item: item[1], reverse=True)
        ]
        exposures[model_name] = industry_rows + style_rows

    portfolio_metrics.sort(key=lambda item: str(item["model"]))
    return (
        portfolio_metrics,
        group_returns,
        drawdowns,
        exposures,
        quantile_returns,
        long_short_returns,
        cost_adjusted_returns,
        excess_returns_output,
    )
