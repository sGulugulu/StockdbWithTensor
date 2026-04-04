from __future__ import annotations

from dataclasses import dataclass

import numpy as np

try:
    import torch
except ImportError:  # pragma: no cover
    torch = None


@dataclass(slots=True)
class DeviceContext:
    requested_device: str
    resolved_device: str
    torch_available: bool


def resolve_device(requested_device: str) -> DeviceContext:
    normalized = requested_device.strip().lower()
    if normalized not in {"auto", "cpu", "cuda"}:
        raise ValueError("runtime.device must be one of: auto, cpu, cuda")

    if torch is None:
        if normalized == "cuda":
            raise RuntimeError("runtime.device='cuda' was requested, but torch is not installed.")
        return DeviceContext(normalized, "cpu", False)
    if normalized == "cpu":
        return DeviceContext(normalized, "cpu", True)
    if normalized == "cuda":
        if not torch.cuda.is_available():
            raise RuntimeError("runtime.device='cuda' was requested, but CUDA is not available.")
        return DeviceContext(normalized, "cuda", True)
    if torch.cuda.is_available():
        return DeviceContext(normalized, "cuda", True)
    return DeviceContext(normalized, "cpu", True)


def _to_numpy(value) -> np.ndarray:
    if torch is not None and isinstance(value, torch.Tensor):
        return value.detach().cpu().numpy()
    return np.asarray(value)


def compute_abs_contribution(array: np.ndarray, context: DeviceContext) -> np.ndarray:
    if torch is not None and context.torch_available:
        tensor = torch.as_tensor(array, dtype=torch.float32, device=context.resolved_device)
        contribution = torch.abs(tensor)
        denominator = contribution.sum(dim=1, keepdim=True)
        denominator = torch.where(denominator == 0, torch.ones_like(denominator), denominator)
        return _to_numpy(contribution / denominator)
    contribution = np.abs(array)
    denominator = contribution.sum(axis=1, keepdims=True)
    denominator[denominator == 0] = 1.0
    return contribution / denominator


def compute_time_shift_scores(array: np.ndarray, context: DeviceContext) -> np.ndarray:
    if array.shape[0] == 0:
        return np.zeros(0, dtype=float)
    if torch is not None and context.torch_available:
        tensor = torch.as_tensor(array, dtype=torch.float32, device=context.resolved_device)
        shifts = torch.zeros(tensor.shape[0], dtype=torch.float32, device=context.resolved_device)
        if tensor.shape[0] > 1:
            diffs = tensor[1:] - tensor[:-1]
            shifts[1:] = torch.linalg.norm(diffs, dim=1)
        max_shift = torch.max(shifts)
        if float(max_shift) > 0:
            shifts = shifts / max_shift
        return _to_numpy(shifts)
    shifts = np.zeros(array.shape[0], dtype=float)
    for idx in range(1, array.shape[0]):
        shifts[idx] = float(np.linalg.norm(array[idx] - array[idx - 1]))
    max_shift = shifts.max() if shifts.size else 0.0
    if max_shift > 0:
        shifts = shifts / max_shift
    return shifts


def compute_stock_clusters(array: np.ndarray) -> np.ndarray:
    if array.ndim != 2 or array.shape[1] == 0:
        return np.zeros(array.shape[0], dtype=int)
    return np.argmax(np.abs(array), axis=1)
