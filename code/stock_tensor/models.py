from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np


@dataclass(slots=True)
class ModelResult:
    name: str
    rank: int | tuple[int, int, int]
    reconstruction: np.ndarray
    stock_loadings: np.ndarray
    factor_loadings: np.ndarray
    time_loadings: np.ndarray
    signal_matrix: np.ndarray
    objective: float
    param_count: int
    diagnostics: dict[str, Any] = field(default_factory=dict)


def unfold(tensor: np.ndarray, mode: int) -> np.ndarray:
    if mode == 0:
        return tensor.reshape(tensor.shape[0], tensor.shape[1] * tensor.shape[2])
    if mode == 1:
        return np.transpose(tensor, (1, 0, 2)).reshape(tensor.shape[1], tensor.shape[0] * tensor.shape[2])
    if mode == 2:
        return np.transpose(tensor, (2, 0, 1)).reshape(tensor.shape[2], tensor.shape[0] * tensor.shape[1])
    raise ValueError(f"Unsupported mode: {mode}")


def khatri_rao(left: np.ndarray, right: np.ndarray) -> np.ndarray:
    if left.shape[1] != right.shape[1]:
        raise ValueError("Khatri-Rao inputs must have the same number of columns.")
    columns = []
    for col_idx in range(left.shape[1]):
        columns.append(np.kron(left[:, col_idx], right[:, col_idx]))
    return np.column_stack(columns)


def _reconstruct_cp(weights: np.ndarray, factors: tuple[np.ndarray, np.ndarray, np.ndarray]) -> np.ndarray:
    a_mat, b_mat, c_mat = factors
    reconstruction = np.zeros((a_mat.shape[0], b_mat.shape[0], c_mat.shape[0]), dtype=float)
    for col_idx in range(weights.shape[0]):
        reconstruction += weights[col_idx] * np.einsum(
            "i,j,k->ijk",
            a_mat[:, col_idx],
            b_mat[:, col_idx],
            c_mat[:, col_idx],
        )
    return reconstruction


def fit_cp_model(
    tensor: np.ndarray,
    rank: int,
    max_iter: int,
    tol: float,
    seed: int,
) -> ModelResult:
    stock_count, factor_count, time_count = tensor.shape
    rng = np.random.default_rng(seed)
    a_mat = rng.normal(scale=0.5, size=(stock_count, rank))
    b_mat = rng.normal(scale=0.5, size=(factor_count, rank))
    c_mat = rng.normal(scale=0.5, size=(time_count, rank))
    weights = np.ones(rank, dtype=float)
    identity = np.eye(rank) * 1e-8
    prev_error = np.inf
    diagnostics: dict[str, Any] = {"iterations": 0}

    for iteration in range(1, max_iter + 1):
        gram = (c_mat.T @ c_mat) * (b_mat.T @ b_mat) + identity
        a_mat = (unfold(tensor, 0) @ khatri_rao(c_mat, b_mat)) @ np.linalg.pinv(gram)

        gram = (c_mat.T @ c_mat) * (a_mat.T @ a_mat) + identity
        b_mat = (unfold(tensor, 1) @ khatri_rao(c_mat, a_mat)) @ np.linalg.pinv(gram)

        gram = (b_mat.T @ b_mat) * (a_mat.T @ a_mat) + identity
        c_mat = (unfold(tensor, 2) @ khatri_rao(b_mat, a_mat)) @ np.linalg.pinv(gram)

        weights = np.ones(rank, dtype=float)
        for factor_matrix in (a_mat, b_mat, c_mat):
            norms = np.linalg.norm(factor_matrix, axis=0)
            norms[norms == 0] = 1.0
            factor_matrix /= norms
            weights *= norms

        reconstruction = _reconstruct_cp(weights, (a_mat, b_mat, c_mat))
        error = float(np.linalg.norm(tensor - reconstruction) / max(np.linalg.norm(tensor), 1e-8))
        diagnostics["iterations"] = iteration
        diagnostics["relative_error"] = error
        if abs(prev_error - error) <= tol:
            break
        prev_error = error

    final_reconstruction = _reconstruct_cp(weights, (a_mat, b_mat, c_mat))
    mse = float(np.mean((tensor - final_reconstruction) ** 2))
    return ModelResult(
        name="cp",
        rank=rank,
        reconstruction=final_reconstruction,
        stock_loadings=a_mat,
        factor_loadings=b_mat,
        time_loadings=c_mat,
        signal_matrix=final_reconstruction.mean(axis=1),
        objective=mse,
        param_count=stock_count * rank + factor_count * rank + time_count * rank + rank,
        diagnostics=diagnostics,
    )


def _mode_product(tensor: np.ndarray, matrix: np.ndarray, mode: int) -> np.ndarray:
    moved = np.moveaxis(tensor, mode, 0)
    product = np.tensordot(matrix, moved, axes=(1, 0))
    return np.moveaxis(product, 0, mode)


def _top_singular_vectors(matrix: np.ndarray, rank: int) -> np.ndarray:
    left, _, _ = np.linalg.svd(matrix, full_matrices=False)
    return left[:, :rank]


def fit_tucker_model(
    tensor: np.ndarray,
    rank: tuple[int, int, int],
    max_iter: int,
    tol: float,
) -> ModelResult:
    stock_rank, factor_rank, time_rank = rank
    u_stock = _top_singular_vectors(unfold(tensor, 0), stock_rank)
    u_factor = _top_singular_vectors(unfold(tensor, 1), factor_rank)
    u_time = _top_singular_vectors(unfold(tensor, 2), time_rank)

    prev_error = np.inf
    diagnostics: dict[str, Any] = {"iterations": 0}
    for iteration in range(1, max_iter + 1):
        projected = _mode_product(_mode_product(tensor, u_factor.T, 1), u_time.T, 2)
        u_stock = _top_singular_vectors(unfold(projected, 0), stock_rank)

        projected = _mode_product(_mode_product(tensor, u_stock.T, 0), u_time.T, 2)
        u_factor = _top_singular_vectors(unfold(projected, 1), factor_rank)

        projected = _mode_product(_mode_product(tensor, u_stock.T, 0), u_factor.T, 1)
        u_time = _top_singular_vectors(unfold(projected, 2), time_rank)

        core = _mode_product(_mode_product(_mode_product(tensor, u_stock.T, 0), u_factor.T, 1), u_time.T, 2)
        reconstruction = _mode_product(_mode_product(_mode_product(core, u_stock, 0), u_factor, 1), u_time, 2)
        error = float(np.linalg.norm(tensor - reconstruction) / max(np.linalg.norm(tensor), 1e-8))
        diagnostics["iterations"] = iteration
        diagnostics["relative_error"] = error
        if abs(prev_error - error) <= tol:
            break
        prev_error = error

    core = _mode_product(_mode_product(_mode_product(tensor, u_stock.T, 0), u_factor.T, 1), u_time.T, 2)
    reconstruction = _mode_product(_mode_product(_mode_product(core, u_stock, 0), u_factor, 1), u_time, 2)
    mse = float(np.mean((tensor - reconstruction) ** 2))
    return ModelResult(
        name="tucker",
        rank=rank,
        reconstruction=reconstruction,
        stock_loadings=u_stock,
        factor_loadings=u_factor,
        time_loadings=u_time,
        signal_matrix=reconstruction.mean(axis=1),
        objective=mse,
        param_count=(
            tensor.shape[0] * stock_rank
            + tensor.shape[1] * factor_rank
            + tensor.shape[2] * time_rank
            + stock_rank * factor_rank * time_rank
        ),
        diagnostics=diagnostics,
    )


def fit_pca_model(tensor: np.ndarray, rank: int) -> ModelResult:
    stock_count, factor_count, time_count = tensor.shape
    observation_matrix = np.transpose(tensor, (0, 2, 1)).reshape(stock_count * time_count, factor_count)
    mean_vector = observation_matrix.mean(axis=0, keepdims=True)
    centered = observation_matrix - mean_vector
    left, singular_values, right_t = np.linalg.svd(centered, full_matrices=False)
    scores = left[:, :rank] * singular_values[:rank]
    components = right_t[:rank, :].T
    reconstruction_matrix = scores @ components.T + mean_vector
    reconstruction = np.transpose(
        reconstruction_matrix.reshape(stock_count, time_count, factor_count),
        (0, 2, 1),
    )
    scores_tensor = scores.reshape(stock_count, time_count, rank)
    mse = float(np.mean((tensor - reconstruction) ** 2))
    return ModelResult(
        name="pca",
        rank=rank,
        reconstruction=reconstruction,
        stock_loadings=scores_tensor.mean(axis=1),
        factor_loadings=components,
        time_loadings=scores_tensor.mean(axis=0),
        signal_matrix=reconstruction.mean(axis=1),
        objective=mse,
        param_count=stock_count * time_count * rank + factor_count * rank + factor_count,
        diagnostics={"explained_singular_values": singular_values[:rank].tolist()},
    )
