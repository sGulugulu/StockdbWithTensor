from __future__ import annotations

from dataclasses import dataclass
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
        signal_slice = result.signal_matrix[:, date_idx][mask]
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
