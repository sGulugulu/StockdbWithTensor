from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[2]
CODE_ROOT = ROOT / "code"
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from stock_tensor.pipeline import run_experiment
from stock_tensor.path_utils import path_relative_to, repo_relative_path
from web.backend.formal_catalog import get_formal_coverage, get_universe_members_for_date


_RUN_STATUS_LOCKS: dict[str, threading.Lock] = {}
_RUN_STATUS_LOCKS_GUARD = threading.Lock()
_RUN_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")
_CONFIG_FILE_SUFFIXES = {".yaml", ".yml"}
_PROFILE_CONFIGS: dict[str, Path] = {
    "formal_hs300": ROOT / "code" / "configs" / "formal_hs300.yaml",
    "formal_sz50": ROOT / "code" / "configs" / "formal_sz50.yaml",
    "formal_zz500": ROOT / "code" / "configs" / "formal_zz500.yaml",
    "sample_cn_smoke": ROOT / "code" / "configs" / "sample_cn_smoke.yaml",
    "sample_us_equity": ROOT / "code" / "configs" / "sample_us_equity.yaml",
}
_MARKET_OPTIONS: list[dict[str, str | bool]] = [
    {
        "option_id": "formal_hs300",
        "config_profile": "formal_hs300",
        "market_id": "cn_a",
        "market_name": "A股 / 沪深300",
        "universe_id": "HS300",
        "is_formal": True,
    },
    {
        "option_id": "formal_sz50",
        "config_profile": "formal_sz50",
        "market_id": "cn_a",
        "market_name": "A股 / 上证50",
        "universe_id": "SZ50",
        "is_formal": True,
    },
    {
        "option_id": "formal_zz500",
        "config_profile": "formal_zz500",
        "market_id": "cn_a",
        "market_name": "A股 / 中证500",
        "universe_id": "ZZ500",
        "is_formal": True,
    },
    {
        "option_id": "sample_cn_smoke",
        "config_profile": "sample_cn_smoke",
        "market_id": "cn_a",
        "market_name": "A股样例",
        "universe_id": "CSI_A500",
        "is_formal": False,
    },
    {
        "option_id": "sample_us_equity",
        "config_profile": "sample_us_equity",
        "market_id": "us_equity",
        "market_name": "美股样例",
        "universe_id": "EXTERNAL_LIST",
        "is_formal": False,
    },
]


def _get_status_lock(run_dir: Path) -> threading.Lock:
    key = str(run_dir.resolve())
    with _RUN_STATUS_LOCKS_GUARD:
        lock = _RUN_STATUS_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _RUN_STATUS_LOCKS[key] = lock
        return lock


def _read_json(path: Path) -> Any:
    last_error: json.JSONDecodeError | None = None
    for _ in range(3):
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            last_error = exc
            time.sleep(0.05)
    if last_error is not None:
        raise last_error
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(f"{path.name}.{uuid.uuid4().hex}.tmp")
    temp_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    temp_path.replace(path)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_path(run_dir: Path) -> Path:
    return run_dir / "run_status.json"


def _is_path_within_root(candidate: Path, root: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _validate_run_id(run_id: Any) -> str:
    if not isinstance(run_id, str):
        raise ValueError("run_id 必须是字符串。")
    candidate = run_id.strip()
    if not _RUN_ID_PATTERN.fullmatch(candidate):
        raise ValueError("run_id 只能包含字母、数字、下划线和中划线，且长度不能超过 64。")
    return candidate


def _resolve_run_dir(output_root: Path, run_id: str, *, validate_pattern: bool = True) -> Path:
    candidate = str(run_id).strip()
    if validate_pattern:
        safe_run_id = _validate_run_id(candidate)
    else:
        if not candidate:
            raise ValueError("run_id 不能为空。")
        safe_run_id = candidate
    run_dir = (output_root / safe_run_id).resolve()
    if not _is_path_within_root(run_dir, output_root):
        raise ValueError("run_id 超出输出目录边界。")
    return run_dir


def _validate_positive_int(value: int, field_name: str) -> int:
    if value <= 0:
        raise ValueError(f"{field_name} 必须是大于 0 的整数。")
    return value


def _coerce_positive_int(value: Any, field_name: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{field_name} 必须是整数。")
    if isinstance(value, int):
        return _validate_positive_int(value, field_name)
    if isinstance(value, float):
        if not value.is_integer():
            raise ValueError(f"{field_name} 必须是整数。")
        return _validate_positive_int(int(value), field_name)
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate or not re.fullmatch(r"[+-]?\d+", candidate):
            raise ValueError(f"{field_name} 必须是整数。")
        return _validate_positive_int(int(candidate), field_name)
    raise ValueError(f"{field_name} 必须是整数。")


def _resolve_requested_config_path(
    raw_config_path: str,
    default_config_path: Path,
    output_root: Path | None = None,
) -> Path:
    candidate = Path(raw_config_path).expanduser()
    default_config_dir = default_config_path.resolve().parent
    if candidate.is_absolute():
        resolved_path = candidate.resolve()
    else:
        candidate_paths = [
            (default_config_dir / candidate).resolve(),
            (ROOT / candidate).resolve(),
        ]
        resolved_path = next((path for path in candidate_paths if path.is_file()), candidate_paths[0])
    if resolved_path.suffix.lower() not in _CONFIG_FILE_SUFFIXES:
        raise ValueError("config_path 只能指向 YAML 配置文件。")
    if not resolved_path.is_file():
        raise ValueError("config_path 指向的配置文件不存在。")
    if output_root is not None:
        resolved_output_root = output_root.resolve()
        if resolved_path.name == "submitted_config.yaml" and _is_path_within_root(resolved_path, resolved_output_root):
            return resolved_path

    # 这里只允许仓库配置目录或当前默认配置同目录，避免把任意文件伪装成实验配置注入执行链路。
    allowed_roots = {
        (ROOT / "code" / "configs").resolve(),
        default_config_path.resolve().parent,
    }
    if not any(_is_path_within_root(resolved_path, root) for root in allowed_roots):
        raise ValueError("config_path 不在允许的配置目录内。")
    return resolved_path


def _load_status(run_dir: Path) -> dict[str, Any]:
    path = _status_path(run_dir)
    if path.exists():
        return _read_json(path)
    return {
        "run_id": run_dir.name,
        "status": "unknown",
        "created_at": None,
        "updated_at": None,
    }


def _update_status(run_dir: Path, status: str, extra: dict[str, Any] | None = None) -> dict[str, Any]:
    with _get_status_lock(run_dir):
        payload = _load_status(run_dir)
        payload["status"] = status
        payload["updated_at"] = _utc_now_iso()
        if payload.get("created_at") is None:
            payload["created_at"] = payload["updated_at"]
        if extra:
            payload.update(extra)
        _write_json(_status_path(run_dir), payload)
        return payload


def list_runs(output_root: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if not output_root.exists():
        return runs
    for child in sorted(output_root.iterdir()):
        if not child.is_dir():
            continue
        status = _load_status(child)
        manifest_path = child / "run_manifest.json"
        metrics_path = child / "metrics.json"
        runs.append(
            {
                "run_id": child.name,
                "status": status,
                "manifest": _read_json(manifest_path) if manifest_path.exists() else None,
                "metrics_exists": metrics_path.exists(),
            }
        )
    return runs


def get_run_detail(output_root: Path, run_id: str) -> dict[str, Any]:
    run_dir = _resolve_run_dir(output_root, run_id, validate_pattern=False)
    factor_summaries = {
        path.stem.replace("factor_summary_", ""): _read_json(path)
        for path in run_dir.glob("factor_summary_*.json")
    }
    factor_associations = {
        path.stem.replace("factor_association_", ""): _read_json(path)
        for path in run_dir.glob("factor_association_*.json")
    }
    time_regimes = {
        path.stem.replace("time_regimes_", ""): _read_json(path)
        for path in run_dir.glob("time_regimes_*.json")
    }
    return {
        "run_id": run_dir.name,
        "status": _load_status(run_dir),
        "manifest": _read_json(run_dir / "run_manifest.json") if (run_dir / "run_manifest.json").exists() else None,
        "metrics": _read_json(run_dir / "metrics.json") if (run_dir / "metrics.json").exists() else [],
        "factor_summaries": factor_summaries,
        "factor_associations": factor_associations,
        "time_regimes": time_regimes,
    }


def get_run_metrics(output_root: Path, run_id: str) -> list[dict[str, Any]]:
    run_dir = _resolve_run_dir(output_root, run_id, validate_pattern=False)
    return _read_json(run_dir / "metrics.json")


def get_selection_for_date(output_root: Path, run_id: str, trade_date: str, top_n: int) -> list[dict[str, Any]]:
    run_dir = _resolve_run_dir(output_root, run_id, validate_pattern=False)
    selection_file = run_dir / "selection_candidates.json"
    selection_rows = [
        row
        for row in _read_json(selection_file)
        if row["trade_date"] == trade_date
    ]
    selection_rows.sort(key=lambda item: float(item["total_score"]), reverse=True)
    return selection_rows[:top_n]


def get_markets() -> list[dict[str, Any]]:
    return list(_MARKET_OPTIONS)


def _run_job(
    *,
    config_path: Path,
    output_root: Path,
    run_id: str,
) -> None:
    run_dir = output_root / run_id
    _update_status(run_dir, "running")
    try:
        run_experiment(
            config_path,
            output_root=output_root,
            experiment_name=run_id,
            status_callback=lambda status, extra: _update_status(run_dir, status, extra),
        )
    except Exception as exc:
        _update_status(run_dir, "failed", {"error": str(exc)})


def submit_run(
    *,
    config_path: Path,
    output_root: Path,
    run_id: str | None = None,
    run_sync: bool = False,
) -> dict[str, Any]:
    actual_run_id = _validate_run_id(run_id) if run_id else uuid.uuid4().hex[:12]
    run_dir = _resolve_run_dir(output_root, actual_run_id)
    run_dir.mkdir(parents=True, exist_ok=True)
    status_payload = _update_status(
        run_dir,
        "queued",
        {
            "run_id": actual_run_id,
            "config_path": repo_relative_path(config_path),
        },
    )
    if run_sync:
        _run_job(config_path=config_path, output_root=output_root, run_id=actual_run_id)
    else:
        thread = threading.Thread(
            target=_run_job,
            kwargs={"config_path": config_path, "output_root": output_root, "run_id": actual_run_id},
            daemon=True,
        )
        thread.start()
    return status_payload


def _build_run_config(
    *,
    base_config_path: Path,
    run_dir: Path,
    payload: dict[str, Any],
    config_profile: str,
) -> Path:
    config_data = yaml.safe_load(base_config_path.read_text(encoding="utf-8"))
    market = config_data.setdefault("market", {})
    data = config_data.setdefault("data", {})
    evaluation = config_data.setdefault("evaluation", {})
    runtime = config_data.setdefault("runtime", {})
    models = config_data.setdefault("models", {})
    output = config_data.setdefault("output", {})
    base_dir = base_config_path.parent

    if "path" in data:
        data["path"] = path_relative_to(run_dir, base_dir / data["path"])
    if market.get("universe_path"):
        market["universe_path"] = path_relative_to(run_dir, base_dir / market["universe_path"])
    if output.get("root_dir"):
        output["root_dir"] = path_relative_to(run_dir, run_dir.parent)

    if not config_profile.startswith("formal_"):
        for key in ["market_id", "universe_id", "start_date", "end_date"]:
            if key in payload and payload[key] is not None:
                market[key] = payload[key]
    if "top_k_pairs" in payload and payload["top_k_pairs"] is not None:
        evaluation["top_k_pairs"] = int(payload["top_k_pairs"])
    if "selection_top_n" in payload and payload["selection_top_n"] is not None:
        runtime["selection_top_n"] = _coerce_positive_int(payload["selection_top_n"], "selection_top_n")
    if "models_enabled" in payload and isinstance(payload["models_enabled"], dict):
        for model_name, enabled in payload["models_enabled"].items():
            if model_name in models and isinstance(models[model_name], dict):
                models[model_name]["enabled"] = bool(enabled)
    if "model_ranks" in payload and isinstance(payload["model_ranks"], dict):
        for model_name, ranks in payload["model_ranks"].items():
            if model_name in models and isinstance(models[model_name], dict):
                models[model_name]["ranks"] = ranks

    config_override_path = run_dir / "submitted_config.yaml"
    run_dir.mkdir(parents=True, exist_ok=True)
    config_override_path.write_text(
        yaml.safe_dump(config_data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return config_override_path


def create_app(
    output_root: Path | None = None,
    default_config_path: Path | None = None,
    formal_root: Path | None = None,
    catalog_path: Path | None = None,
):
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("FastAPI is required to run the web backend.") from exc

    app = FastAPI(title="Stock Tensor Experiment API")
    resolved_output_root = output_root or Path(os.environ.get("OUTPUT_ROOT", ROOT / "code" / "outputs"))
    config_path = default_config_path or Path(os.environ.get("DEFAULT_CONFIG_PATH", ROOT / "code" / "configs" / "default.yaml"))
    resolved_formal_root = formal_root or Path(os.environ.get("FORMAL_ROOT", ROOT / "code" / "data" / "formal"))
    resolved_catalog_path = catalog_path or Path(
        os.environ.get("FORMAL_CATALOG_PATH", resolved_formal_root / "catalog.duckdb")
    )
    config_templates = {
        "cn_a": ROOT / "code" / "configs" / "default.yaml",
        "us_equity": ROOT / "code" / "configs" / "sample_us_equity.yaml",
    }

    @app.get("/api/markets")
    async def api_markets() -> list[dict[str, Any]]:
        return get_markets()

    @app.get("/api/formal/coverage")
    async def api_formal_coverage() -> dict[str, Any]:
        try:
            return get_formal_coverage(
                formal_root=resolved_formal_root,
                catalog_path=resolved_catalog_path,
            )
        except ModuleNotFoundError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    @app.get("/api/formal/universes/{universe_id}")
    async def api_formal_universe_members(universe_id: str, trade_date: str) -> list[dict[str, Any]]:
        try:
            rows = get_universe_members_for_date(
                formal_root=resolved_formal_root,
                catalog_path=resolved_catalog_path,
                universe_id=universe_id,
                trade_date=trade_date,
            )
        except KeyError as exc:
            raise HTTPException(status_code=404, detail="Universe not found") from exc
        except ModuleNotFoundError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return rows

    @app.get("/api/runs")
    async def api_runs() -> list[dict[str, Any]]:
        return list_runs(resolved_output_root)

    @app.post("/api/runs")
    async def api_create_run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = payload or {}
        requested_run_id = body.get("run_id")
        run_sync = bool(body.get("run_sync", False))
        try:
            actual_run_id = _validate_run_id(requested_run_id) if requested_run_id else uuid.uuid4().hex[:12]
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        config_profile = str(body.get("config_profile", ""))
        try:
            if body.get("config_path"):
                requested_config = _resolve_requested_config_path(
                    str(body["config_path"]),
                    Path(config_path),
                    resolved_output_root,
                )
            elif config_profile in _PROFILE_CONFIGS:
                requested_config = _PROFILE_CONFIGS[config_profile].resolve()
            elif body.get("market_id") == "cn_a" and body.get("universe_id") == "HS300":
                requested_config = (ROOT / "code" / "configs" / "formal_hs300.yaml").resolve()
            elif body.get("market_id") == "cn_a" and body.get("universe_id") == "SZ50":
                requested_config = (ROOT / "code" / "configs" / "formal_sz50.yaml").resolve()
            elif body.get("market_id") == "cn_a" and body.get("universe_id") == "ZZ500":
                requested_config = (ROOT / "code" / "configs" / "formal_zz500.yaml").resolve()
            elif body.get("market_id") in config_templates:
                requested_config = config_templates[body["market_id"]].resolve()
            else:
                requested_config = Path(config_path).resolve()
            if "selection_top_n" in body and body["selection_top_n"] is not None:
                _coerce_positive_int(body["selection_top_n"], "selection_top_n")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        run_dir = _resolve_run_dir(resolved_output_root, actual_run_id)
        built_config_path = _build_run_config(
            base_config_path=requested_config,
            run_dir=run_dir,
            payload=body,
            config_profile=config_profile,
        )
        return submit_run(
            config_path=built_config_path,
            output_root=resolved_output_root,
            run_id=actual_run_id,
            run_sync=run_sync,
        )

    @app.get("/api/runs/{run_id}")
    async def api_run_detail(run_id: str) -> dict[str, Any]:
        try:
            run_dir = _resolve_run_dir(resolved_output_root, run_id, validate_pattern=False)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        return get_run_detail(resolved_output_root, run_id)

    @app.get("/api/runs/{run_id}/metrics")
    async def api_run_metrics(run_id: str) -> list[dict[str, Any]]:
        try:
            run_dir = _resolve_run_dir(resolved_output_root, run_id, validate_pattern=False)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        status = _load_status(run_dir)
        if status["status"] != "completed" or not (run_dir / "metrics.json").exists():
            raise HTTPException(status_code=409, detail="Run metrics are not available yet")
        return get_run_metrics(resolved_output_root, run_id)

    @app.get("/api/runs/{run_id}/selection")
    async def api_run_selection(run_id: str, trade_date: str, top_n: int = 50) -> list[dict[str, Any]]:
        try:
            run_dir = _resolve_run_dir(resolved_output_root, run_id, validate_pattern=False)
            validated_top_n = _validate_positive_int(top_n, "top_n")
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        status = _load_status(run_dir)
        if status["status"] != "completed" or not (run_dir / "selection_candidates.json").exists():
            raise HTTPException(status_code=409, detail="Selection results are not available yet")
        return get_selection_for_date(resolved_output_root, run_id, trade_date, validated_top_n)

    return app
