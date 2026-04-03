from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Callable

from .config import ExperimentConfig, load_config
from .dataset import TensorDataset, build_tensor_dataset
from .evaluation import (
    build_candidate_pool,
    build_selection_records,
    compute_quality_metrics,
    compute_rolling_stability,
    factor_importance_summary,
    time_regime_shifts,
    top_similarity_pairs,
)
from .market import create_market_adapter
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


def run_experiment(
    config_path: str | Path,
    *,
    output_root: str | Path | None = None,
    experiment_name: str | None = None,
    status_callback: Callable[[str, dict[str, object]], None] | None = None,
) -> Path:
    config = load_config(config_path)
    if output_root is not None:
        config.output.root_dir = Path(output_root).resolve()
    if experiment_name is not None:
        config.output.experiment_name = experiment_name
    logs: list[str] = [f"Loaded config: {Path(config_path).resolve()}"]
    market_adapter = create_market_adapter(config.market)

    records = market_adapter.load_records(config.data)
    logs.append(f"Loaded normalized records before market filtering: {len(records)}")
    filtered_records, actual_start, actual_end = market_adapter.filter_records(records)
    logs.append(
        f"Filtered records for {config.market.market_id}/{config.market.universe_id}: "
        f"{len(filtered_records)} rows from {actual_start} to {actual_end}"
    )
    if status_callback is not None:
        status_callback(
            "running",
            {
                "actual_start_date": actual_start,
                "actual_end_date": actual_end,
                "loaded_records": len(filtered_records),
            },
        )
    dataset = build_tensor_dataset(filtered_records, config.preprocess)
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
    selection_rows: dict[str, list] = {}
    factor_summaries: dict[str, list] = {}
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
        selection_rows[model.name] = build_selection_records(
            dataset,
            model,
            market_id=config.market.market_id,
            universe_id=config.market.universe_id,
        )
        factor_summaries[model.name] = factor_importance_summary(
            dataset.factor_names,
            model.factor_loadings,
        )
        logs.append(f"Selected {model.name} rank={model.rank} with mse={metrics['mse']:.6f}")

    candidate_rows = build_candidate_pool(selection_rows)

    output_dir = config.output.root_dir / config.output.experiment_name
    write_outputs(
        output_dir=output_dir,
        config_snapshot=asdict(config),
        logs=logs,
        metrics_rows=metrics_rows,
        stock_pairs=stock_pairs,
        factor_pairs=factor_pairs,
        time_shifts=time_shifts,
        selection_rows=selection_rows,
        candidate_rows=candidate_rows,
        factor_summaries=factor_summaries,
        run_manifest={
            "market_id": config.market.market_id,
            "universe_id": config.market.universe_id,
            "requested_start_date": config.market.start_date,
            "requested_end_date": config.market.end_date,
            "actual_start_date": actual_start,
            "actual_end_date": actual_end,
            "models": [row["model"] for row in metrics_rows],
            "candidate_pool_size": len(candidate_rows),
            "selection_top_n": config.runtime.selection_top_n,
            "output_dir": output_dir,
            "status": "completed",
        },
    )
    if status_callback is not None:
        status_callback("completed", {"output_dir": str(output_dir), "models": [row["model"] for row in metrics_rows]})
    return output_dir
