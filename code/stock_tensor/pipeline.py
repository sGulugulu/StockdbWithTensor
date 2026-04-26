from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Callable

from .compute_backend import resolve_device
from .config import ExperimentConfig, load_config
from .dataset import TensorDataset, build_raw_tensor_dataset, slice_tensor_dataset
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
from .models import (
    ModelResult,
    fit_cp_model,
    fit_pca_model,
    fit_tucker_model,
    score_cp_model,
    score_pca_model,
    score_tucker_model,
)
from .output import write_outputs
from .path_utils import repo_relative_path
from .preprocess import apply_preprocess_state, fit_preprocess_state
from .splits import materialize_splits


def _fit_model_for_rank(
    config: ExperimentConfig,
    *,
    model_name: str,
    rank: int | tuple[int, int, int],
    tensor,
):
    device_context = resolve_device(config.runtime.device)
    if model_name == "cp":
        return fit_cp_model(
            tensor,
            rank=int(rank),
            max_iter=config.models.cp.max_iter,
            tol=config.models.cp.tol,
            seed=config.models.seed,
            device_context=device_context,
        )
    if model_name == "tucker":
        return fit_tucker_model(
            tensor,
            rank=tuple(int(part) for part in rank),
            max_iter=config.models.tucker.max_iter,
            tol=config.models.tucker.tol,
            device_context=device_context,
        )
    if model_name == "pca":
        return fit_pca_model(tensor, rank=int(rank), device_context=device_context)
    raise ValueError(f"Unsupported model target: {model_name}")


def _candidate_ranks(config: ExperimentConfig, model_name: str) -> list[int | tuple[int, int, int]]:
    if model_name == "cp":
        return list(config.models.cp.ranks)
    if model_name == "tucker":
        return list(config.models.tucker.ranks)
    if model_name == "pca":
        return list(config.models.pca.ranks)
    raise ValueError(f"Unsupported model target: {model_name}")


def _ordered_union(full_items: list[str], *parts: list[str]) -> list[str]:
    seen = {item for part in parts for item in part}
    return [item for item in full_items if item in seen]


def _build_refit_dataset(
    full_dataset: TensorDataset,
    *,
    train_dataset: TensorDataset,
    validation_dataset: TensorDataset,
) -> TensorDataset:
    refit_stock_codes = _ordered_union(
        full_dataset.stock_codes,
        train_dataset.stock_codes,
        validation_dataset.stock_codes,
    )
    refit_dates = _ordered_union(
        full_dataset.dates,
        train_dataset.dates,
        validation_dataset.dates,
    )
    return slice_tensor_dataset(
        full_dataset,
        stock_codes=refit_stock_codes,
        dates=refit_dates,
    )


def _score_partition(
    *,
    model_name: str,
    trained_model: ModelResult,
    fit_dataset: TensorDataset,
    evaluation_dataset: TensorDataset,
) -> ModelResult:
    infer_stock = fit_dataset.stock_codes != evaluation_dataset.stock_codes
    infer_time = fit_dataset.dates != evaluation_dataset.dates
    if model_name == "cp":
        return score_cp_model(
            evaluation_dataset.tensor,
            trained_model,
            infer_stock=infer_stock,
            infer_time=infer_time,
        )
    if model_name == "tucker":
        return score_tucker_model(
            evaluation_dataset.tensor,
            trained_model,
            infer_stock=infer_stock,
            infer_time=infer_time,
        )
    if model_name == "pca":
        return score_pca_model(
            evaluation_dataset.tensor,
            trained_model,
        )
    raise ValueError(f"Unsupported model target: {model_name}")


def _select_best_model(
    config: ExperimentConfig,
    *,
    train_dataset: TensorDataset,
    validation_dataset: TensorDataset,
    logs: list[str],
    model_name: str,
) -> int | tuple[int, int, int]:
    scored_candidates: list[ModelResult] = []
    for rank in _candidate_ranks(config, model_name):
        train_candidate = _fit_model_for_rank(
            config,
            model_name=model_name,
            rank=rank,
            tensor=train_dataset.tensor,
        )
        validation_candidate = _score_partition(
            model_name=model_name,
            trained_model=train_candidate,
            fit_dataset=train_dataset,
            evaluation_dataset=validation_dataset,
        )
        logs.append(
            f"{model_name} rank={rank} train_fit_mse={train_candidate.objective:.6f} "
            f"validation_score_mse={validation_candidate.objective:.6f}"
        )
        scored_candidates.append(validation_candidate)
    return min(scored_candidates, key=lambda item: item.objective).rank


def _fit_window_callable(config: ExperimentConfig, model: ModelResult):
    device_context = resolve_device(config.runtime.device)
    if model.name == "cp":
        return lambda tensor: fit_cp_model(
            tensor,
            rank=int(model.rank),
            max_iter=config.models.cp.max_iter,
            tol=config.models.cp.tol,
            seed=config.models.seed,
            device_context=device_context,
        )
    if model.name == "tucker":
        return lambda tensor: fit_tucker_model(
            tensor,
            rank=tuple(int(part) for part in model.rank),
            max_iter=config.models.tucker.max_iter,
            tol=config.models.tucker.tol,
            device_context=device_context,
        )
    return lambda tensor: fit_pca_model(tensor, rank=int(model.rank), device_context=device_context)


def run_experiment(
    config_path: str | Path,
    *,
    output_root: str | Path | None = None,
    experiment_name: str | None = None,
    status_callback: Callable[[str, dict[str, object]], None] | None = None,
) -> Path:
    config = load_config(config_path)
    device_context = resolve_device(config.runtime.device)
    if output_root is not None:
        config.output.root_dir = Path(output_root).resolve()
    if experiment_name is not None:
        config.output.experiment_name = experiment_name
    logs: list[str] = [
        f"Loaded config: {repo_relative_path(Path(config_path).resolve())}",
        f"Resolved device: requested={config.runtime.device}, actual={device_context.resolved_device}",
    ]
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
    raw_dataset = build_raw_tensor_dataset(filtered_records)
    logs.append(
        "Tensor shape: "
        f"{raw_dataset.tensor.shape[0]} stocks x {raw_dataset.tensor.shape[1]} factors x {raw_dataset.tensor.shape[2]} dates"
    )

    split_plan = materialize_splits(
        raw_dataset,
        config.split,
        label_column=config.data.return_column,
    )
    train_raw_dataset = split_plan.partitions["train"].dataset
    validation_raw_dataset = split_plan.partitions["validation"].dataset
    test_raw_dataset = split_plan.partitions["test"].dataset
    refit_dataset = _build_refit_dataset(
        raw_dataset,
        train_dataset=train_raw_dataset,
        validation_dataset=validation_raw_dataset,
    )
    preprocess_state, train_preprocessed = fit_preprocess_state(
        train_raw_dataset.tensor,
        train_raw_dataset.raw_tensor,
        train_raw_dataset.returns,
        train_raw_dataset.stock_codes,
        train_raw_dataset.factor_names,
        train_raw_dataset.dates,
        train_raw_dataset.industries,
        config.preprocess,
    )
    train_dataset = TensorDataset(
        tensor=train_preprocessed.tensor,
        raw_tensor=train_preprocessed.raw_tensor,
        returns=train_preprocessed.returns,
        stock_codes=train_preprocessed.stock_codes,
        factor_names=train_preprocessed.factor_names,
        dates=train_raw_dataset.dates,
        industries=train_preprocessed.industries,
        preprocess_summary=train_preprocessed.summary,
    )
    validation_preprocessed = apply_preprocess_state(
        validation_raw_dataset.tensor,
        validation_raw_dataset.raw_tensor,
        validation_raw_dataset.returns,
        validation_raw_dataset.stock_codes,
        validation_raw_dataset.factor_names,
        validation_raw_dataset.dates,
        preprocess_state,
        config.preprocess,
        partition_name="validation",
    )
    validation_dataset = TensorDataset(
        tensor=validation_preprocessed.tensor,
        raw_tensor=validation_preprocessed.raw_tensor,
        returns=validation_preprocessed.returns,
        stock_codes=validation_preprocessed.stock_codes,
        factor_names=validation_preprocessed.factor_names,
        dates=validation_raw_dataset.dates,
        industries=validation_preprocessed.industries,
        preprocess_summary=validation_preprocessed.summary,
    )
    test_preprocessed = apply_preprocess_state(
        test_raw_dataset.tensor,
        test_raw_dataset.raw_tensor,
        test_raw_dataset.returns,
        test_raw_dataset.stock_codes,
        test_raw_dataset.factor_names,
        test_raw_dataset.dates,
        preprocess_state,
        config.preprocess,
        partition_name="test",
    )
    test_dataset = TensorDataset(
        tensor=test_preprocessed.tensor,
        raw_tensor=test_preprocessed.raw_tensor,
        returns=test_preprocessed.returns,
        stock_codes=test_preprocessed.stock_codes,
        factor_names=test_preprocessed.factor_names,
        dates=test_raw_dataset.dates,
        industries=test_preprocessed.industries,
        preprocess_summary=test_preprocessed.summary,
    )
    refit_preprocessed = apply_preprocess_state(
        refit_dataset.tensor,
        refit_dataset.raw_tensor,
        refit_dataset.returns,
        refit_dataset.stock_codes,
        refit_dataset.factor_names,
        refit_dataset.dates,
        preprocess_state,
        config.preprocess,
        partition_name="refit",
    )
    refit_dataset = TensorDataset(
        tensor=refit_preprocessed.tensor,
        raw_tensor=refit_preprocessed.raw_tensor,
        returns=refit_preprocessed.returns,
        stock_codes=refit_preprocessed.stock_codes,
        factor_names=refit_preprocessed.factor_names,
        dates=refit_dataset.dates,
        industries=refit_preprocessed.industries,
        preprocess_summary=refit_preprocessed.summary,
    )
    logs.append(
        "Split materialization: "
        f"train={train_dataset.tensor.shape}, "
        f"validation={validation_dataset.tensor.shape}, "
        f"test={test_dataset.tensor.shape}"
    )
    logs.append("Preprocess fit scope: train_only")

    selected_models: list[ModelResult] = []
    refit_models: dict[str, ModelResult] = {}
    if config.models.cp.enabled:
        best_rank = _select_best_model(
            config,
            train_dataset=train_dataset,
            validation_dataset=validation_dataset,
            logs=logs,
            model_name="cp",
        )
        refit_models["cp"] = _fit_model_for_rank(
            config,
            model_name="cp",
            rank=best_rank,
            tensor=refit_dataset.tensor,
        )
        selected_models.append(
            _score_partition(
                model_name="cp",
                trained_model=refit_models["cp"],
                fit_dataset=refit_dataset,
                evaluation_dataset=test_dataset,
            )
        )
    if config.models.tucker.enabled:
        best_rank = _select_best_model(
            config,
            train_dataset=train_dataset,
            validation_dataset=validation_dataset,
            logs=logs,
            model_name="tucker",
        )
        refit_models["tucker"] = _fit_model_for_rank(
            config,
            model_name="tucker",
            rank=best_rank,
            tensor=refit_dataset.tensor,
        )
        selected_models.append(
            _score_partition(
                model_name="tucker",
                trained_model=refit_models["tucker"],
                fit_dataset=refit_dataset,
                evaluation_dataset=test_dataset,
            )
        )
    if config.models.pca.enabled:
        best_rank = _select_best_model(
            config,
            train_dataset=train_dataset,
            validation_dataset=validation_dataset,
            logs=logs,
            model_name="pca",
        )
        refit_models["pca"] = _fit_model_for_rank(
            config,
            model_name="pca",
            rank=best_rank,
            tensor=refit_dataset.tensor,
        )
        selected_models.append(
            _score_partition(
                model_name="pca",
                trained_model=refit_models["pca"],
                fit_dataset=refit_dataset,
                evaluation_dataset=test_dataset,
            )
        )

    metrics_rows: list[dict[str, object]] = []
    stock_pairs: dict[str, list] = {}
    factor_pairs: dict[str, list] = {}
    time_shifts: dict[str, list] = {}
    selection_rows: dict[str, list] = {}
    factor_summaries: dict[str, list] = {}
    for model in selected_models:
        metrics = compute_quality_metrics(test_dataset.tensor, model, test_dataset.returns)
        refit_model = refit_models[model.name]
        stability = compute_rolling_stability(
            refit_dataset,
            config.evaluation.rolling_window,
            _fit_window_callable(config, refit_model),
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
            test_dataset.stock_codes,
            model.stock_loadings,
            config.evaluation.top_k_pairs,
        )
        factor_pairs[model.name] = top_similarity_pairs(
            test_dataset.factor_names,
            model.factor_loadings,
            config.evaluation.top_k_pairs,
        )
        time_shifts[model.name] = time_regime_shifts(
            test_dataset.dates,
            model.time_loadings,
            config.evaluation.top_k_pairs,
        )
        selection_rows[model.name] = build_selection_records(
            test_dataset,
            model,
            market_id=config.market.market_id,
            universe_id=config.market.universe_id,
        )
        factor_summaries[model.name] = factor_importance_summary(
            test_dataset.factor_names,
            model.factor_loadings,
        )
        logs.append(
            f"Selected {model.name} rank={model.rank}; "
            f"refit_shape={refit_dataset.tensor.shape}; held_out_test_mse={metrics['mse']:.6f}"
        )

    candidate_rows = build_candidate_pool(selection_rows)
    split_metadata = split_plan.metadata

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
            "preprocess": train_dataset.preprocess_summary,
            "split": split_metadata,
            "status": "completed",
        },
    )
    if status_callback is not None:
        status_callback(
            "completed",
            {
                "output_dir": repo_relative_path(output_dir),
                "models": [row["model"] for row in metrics_rows],
            },
        )
    return output_dir
