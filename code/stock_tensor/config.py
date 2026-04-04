from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class DataConfig:
    path: Path
    format: str
    stock_column: str
    date_column: str
    industry_column: str | None
    return_column: str | None
    factor_columns: list[str]
    factor_name_column: str | None
    factor_value_column: str | None


@dataclass(slots=True)
class MarketConfig:
    market_id: str
    universe_id: str
    start_date: str
    end_date: str
    timezone: str
    currency: str
    universe_path: Path | None
    universe_symbol_column: str
    universe_start_column: str
    universe_end_column: str
    universe_market_column: str | None
    universe_id_column: str | None


@dataclass(slots=True)
class PreprocessConfig:
    max_missing_ratio: float
    winsor_limits: tuple[float, float]


@dataclass(slots=True)
class CPConfig:
    enabled: bool
    ranks: list[int]
    max_iter: int
    tol: float


@dataclass(slots=True)
class TuckerConfig:
    enabled: bool
    ranks: list[tuple[int, int, int]]
    max_iter: int
    tol: float


@dataclass(slots=True)
class PCAConfig:
    enabled: bool
    ranks: list[int]


@dataclass(slots=True)
class ModelConfig:
    seed: int
    cp: CPConfig
    tucker: TuckerConfig
    pca: PCAConfig


@dataclass(slots=True)
class EvaluationConfig:
    top_k_pairs: int
    rolling_window: int


@dataclass(slots=True)
class RuntimeConfig:
    selection_top_n: int
    device: str


@dataclass(slots=True)
class OutputConfig:
    root_dir: Path
    experiment_name: str


@dataclass(slots=True)
class ExperimentConfig:
    market: MarketConfig
    data: DataConfig
    preprocess: PreprocessConfig
    models: ModelConfig
    evaluation: EvaluationConfig
    runtime: RuntimeConfig
    output: OutputConfig


def _require_keys(section: dict[str, Any], keys: list[str], prefix: str) -> None:
    missing = [key for key in keys if key not in section]
    if missing:
        raise ValueError(f"Missing required config keys in {prefix}: {', '.join(missing)}")


def load_config(path: str | Path) -> ExperimentConfig:
    config_path = Path(path).resolve()
    raw = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("Config file must be a mapping.")

    _require_keys(raw, ["market", "data", "preprocess", "models", "evaluation", "output"], "root")
    market = raw["market"]
    data = raw["data"]
    preprocess = raw["preprocess"]
    models = raw["models"]
    evaluation = raw["evaluation"]
    runtime = raw.get("runtime", {})
    output = raw["output"]

    _require_keys(
        market,
        ["market_id", "universe_id", "start_date", "end_date", "timezone", "currency"],
        "market",
    )

    _require_keys(data, ["path", "format", "stock_column", "date_column"], "data")
    data_format = data["format"]
    if data_format not in {"wide", "long"}:
        raise ValueError("data.format must be either 'wide' or 'long'.")

    factor_columns = list(data.get("factor_columns", []))
    factor_name_column = data.get("factor_name_column")
    factor_value_column = data.get("factor_value_column")
    if data_format == "wide" and not factor_columns:
        raise ValueError("Wide format requires data.factor_columns.")
    if data_format == "long" and (not factor_name_column or not factor_value_column):
        raise ValueError("Long format requires data.factor_name_column and data.factor_value_column.")

    _require_keys(preprocess, ["max_missing_ratio", "winsor_limits"], "preprocess")
    winsor_limits = tuple(preprocess["winsor_limits"])
    if len(winsor_limits) != 2:
        raise ValueError("preprocess.winsor_limits must contain [lower, upper].")

    _require_keys(models, ["seed", "cp", "tucker", "pca"], "models")
    cp = models["cp"]
    tucker = models["tucker"]
    pca = models["pca"]
    _require_keys(cp, ["enabled", "ranks", "max_iter", "tol"], "models.cp")
    _require_keys(tucker, ["enabled", "ranks", "max_iter", "tol"], "models.tucker")
    _require_keys(pca, ["enabled", "ranks"], "models.pca")

    _require_keys(evaluation, ["top_k_pairs", "rolling_window"], "evaluation")
    _require_keys(output, ["root_dir", "experiment_name"], "output")

    base_dir = config_path.parent
    universe_path = market.get("universe_path")
    data_path = (base_dir / data["path"]).resolve()
    output_root = (base_dir / output["root_dir"]).resolve()

    return ExperimentConfig(
        market=MarketConfig(
            market_id=str(market["market_id"]),
            universe_id=str(market["universe_id"]),
            start_date=str(market["start_date"]),
            end_date=str(market["end_date"]),
            timezone=str(market["timezone"]),
            currency=str(market["currency"]),
            universe_path=((base_dir / universe_path).resolve() if universe_path else None),
            universe_symbol_column=str(market.get("universe_symbol_column", "stock_code")),
            universe_start_column=str(market.get("universe_start_column", "start_date")),
            universe_end_column=str(market.get("universe_end_column", "end_date")),
            universe_market_column=market.get("universe_market_column"),
            universe_id_column=market.get("universe_id_column"),
        ),
        data=DataConfig(
            path=data_path,
            format=data_format,
            stock_column=data["stock_column"],
            date_column=data["date_column"],
            industry_column=data.get("industry_column"),
            return_column=data.get("return_column"),
            factor_columns=factor_columns,
            factor_name_column=factor_name_column,
            factor_value_column=factor_value_column,
        ),
        preprocess=PreprocessConfig(
            max_missing_ratio=float(preprocess["max_missing_ratio"]),
            winsor_limits=(float(winsor_limits[0]), float(winsor_limits[1])),
        ),
        models=ModelConfig(
            seed=int(models["seed"]),
            cp=CPConfig(
                enabled=bool(cp["enabled"]),
                ranks=[int(rank) for rank in cp["ranks"]],
                max_iter=int(cp["max_iter"]),
                tol=float(cp["tol"]),
            ),
            tucker=TuckerConfig(
                enabled=bool(tucker["enabled"]),
                ranks=[tuple(int(part) for part in rank) for rank in tucker["ranks"]],
                max_iter=int(tucker["max_iter"]),
                tol=float(tucker["tol"]),
            ),
            pca=PCAConfig(
                enabled=bool(pca["enabled"]),
                ranks=[int(rank) for rank in pca["ranks"]],
            ),
        ),
        evaluation=EvaluationConfig(
            top_k_pairs=int(evaluation["top_k_pairs"]),
            rolling_window=int(evaluation["rolling_window"]),
        ),
        runtime=RuntimeConfig(
            selection_top_n=int(runtime.get("selection_top_n", 20)),
            device=str(runtime.get("device", "auto")),
        ),
        output=OutputConfig(
            root_dir=output_root,
            experiment_name=str(output["experiment_name"]),
        ),
    )
