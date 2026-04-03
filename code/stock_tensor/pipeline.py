from __future__ import annotations

from dataclasses import asdict
from pathlib import Path

from .config import ExperimentConfig, load_config
from .dataset import TensorDataset, build_tensor_dataset, load_factor_records
from .evaluation import (
    compute_quality_metrics,
    compute_rolling_stability,
    time_regime_shifts,
    top_similarity_pairs,
)
from .models import ModelResult, fit_cp_model, fit_pca_model, fit_tucker_model
from .output import write_outputs


def _select_best_model(config: ExperimentConfig, dataset: TensorDataset, logs: list[str], model_name: str) -> ModelResult:
    candidates: list[ModelResult] = []
    if model_name == "cp":
        for rank in config.models.cp.ranks:
            candidate = fit_cp_model(
                dataset.tensor,
                rank=rank,
                max_iter=config.models.cp.max_iter,
                tol=config.models.cp.tol,
                seed=config.models.seed,
            )
            logs.append(f"cp rank={rank} mse={candidate.objective:.6f}")
            candidates.append(candidate)
    elif model_name == "tucker":
        for rank in config.models.tucker.ranks:
            candidate = fit_tucker_model(
                dataset.tensor,
                rank=rank,
                max_iter=config.models.tucker.max_iter,
                tol=config.models.tucker.tol,
            )
            logs.append(f"tucker rank={rank} mse={candidate.objective:.6f}")
            candidates.append(candidate)
    elif model_name == "pca":
        for rank in config.models.pca.ranks:
            candidate = fit_pca_model(dataset.tensor, rank=rank)
            logs.append(f"pca rank={rank} mse={candidate.objective:.6f}")
            candidates.append(candidate)
    else:
        raise ValueError(f"Unsupported model selection target: {model_name}")
    return min(candidates, key=lambda item: item.objective)


def _fit_window_callable(config: ExperimentConfig, model: ModelResult):
    if model.name == "cp":
        return lambda tensor: fit_cp_model(
            tensor,
            rank=int(model.rank),
            max_iter=config.models.cp.max_iter,
            tol=config.models.cp.tol,
            seed=config.models.seed,
        )
    if model.name == "tucker":
        return lambda tensor: fit_tucker_model(
            tensor,
            rank=tuple(int(part) for part in model.rank),
            max_iter=config.models.tucker.max_iter,
            tol=config.models.tucker.tol,
        )
    return lambda tensor: fit_pca_model(tensor, rank=int(model.rank))


def run_experiment(config_path: str | Path) -> Path:
    config = load_config(config_path)
    logs: list[str] = [f"Loaded config: {Path(config_path).resolve()}"]

    records = load_factor_records(config.data)
    logs.append(f"Loaded normalized records: {len(records)}")
    dataset = build_tensor_dataset(records, config.preprocess)
    logs.append(
        "Tensor shape: "
        f"{dataset.tensor.shape[0]} stocks x {dataset.tensor.shape[1]} factors x {dataset.tensor.shape[2]} dates"
    )

    selected_models: list[ModelResult] = []
    if config.models.cp.enabled:
        selected_models.append(_select_best_model(config, dataset, logs, "cp"))
    if config.models.tucker.enabled:
        selected_models.append(_select_best_model(config, dataset, logs, "tucker"))
    if config.models.pca.enabled:
        selected_models.append(_select_best_model(config, dataset, logs, "pca"))

    metrics_rows: list[dict[str, object]] = []
    stock_pairs: dict[str, list] = {}
    factor_pairs: dict[str, list] = {}
    time_shifts: dict[str, list] = {}
    for model in selected_models:
        metrics = compute_quality_metrics(dataset.tensor, model, dataset.returns)
        stability = compute_rolling_stability(
            dataset,
            config.evaluation.rolling_window,
            _fit_window_callable(config, model),
        )
        metrics["rolling_stability"] = stability
        metrics_rows.append(
            {
                "model": model.name,
                "rank": str(model.rank),
                **metrics,
            }
        )
        stock_pairs[model.name] = top_similarity_pairs(
            dataset.stock_codes,
            model.stock_loadings,
            config.evaluation.top_k_pairs,
        )
        factor_pairs[model.name] = top_similarity_pairs(
            dataset.factor_names,
            model.factor_loadings,
            config.evaluation.top_k_pairs,
        )
        time_shifts[model.name] = time_regime_shifts(
            dataset.dates,
            model.time_loadings,
            config.evaluation.top_k_pairs,
        )
        logs.append(f"Selected {model.name} rank={model.rank} with mse={metrics['mse']:.6f}")

    output_dir = config.output.root_dir / config.output.experiment_name
    write_outputs(
        output_dir=output_dir,
        config_snapshot=asdict(config),
        logs=logs,
        metrics_rows=metrics_rows,
        stock_pairs=stock_pairs,
        factor_pairs=factor_pairs,
        time_shifts=time_shifts,
    )
    return output_dir
