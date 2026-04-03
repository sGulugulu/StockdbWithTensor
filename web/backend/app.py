from __future__ import annotations

import json
import os
import threading
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


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _status_path(run_dir: Path) -> Path:
    return run_dir / "run_status.json"


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
    run_dir = output_root / run_id
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
        "run_id": run_id,
        "status": _load_status(run_dir),
        "manifest": _read_json(run_dir / "run_manifest.json") if (run_dir / "run_manifest.json").exists() else None,
        "metrics": _read_json(run_dir / "metrics.json") if (run_dir / "metrics.json").exists() else [],
        "factor_summaries": factor_summaries,
        "factor_associations": factor_associations,
        "time_regimes": time_regimes,
    }


def get_run_metrics(output_root: Path, run_id: str) -> list[dict[str, Any]]:
    return _read_json(output_root / run_id / "metrics.json")


def get_selection_for_date(output_root: Path, run_id: str, trade_date: str, top_n: int) -> list[dict[str, Any]]:
    run_dir = output_root / run_id
    selection_file = run_dir / "selection_candidates.json"
    selection_rows = [
        row
        for row in _read_json(selection_file)
        if row["trade_date"] == trade_date
    ]
    selection_rows.sort(key=lambda item: float(item["total_score"]), reverse=True)
    return selection_rows[:top_n]


def get_markets() -> list[dict[str, str]]:
    return [
        {"market_id": "cn_a", "market_name": "A股", "default_universe_id": "CSI_A500"},
        {"market_id": "us_equity", "market_name": "美股", "default_universe_id": "EXTERNAL_LIST"},
    ]


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
    actual_run_id = run_id or uuid.uuid4().hex[:12]
    run_dir = output_root / actual_run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    _update_status(
        run_dir,
        "queued",
        {
            "run_id": actual_run_id,
            "config_path": str(config_path),
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
    return _load_status(run_dir)


def _build_run_config(
    *,
    base_config_path: Path,
    run_dir: Path,
    payload: dict[str, Any],
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
        data["path"] = str((base_dir / data["path"]).resolve())
    if market.get("universe_path"):
        market["universe_path"] = str((base_dir / market["universe_path"]).resolve())
    if output.get("root_dir"):
        output["root_dir"] = str(run_dir.parent.resolve())

    for key in ["market_id", "universe_id", "start_date", "end_date"]:
        if key in payload and payload[key] is not None:
            market[key] = payload[key]
    if "top_k_pairs" in payload and payload["top_k_pairs"] is not None:
        evaluation["top_k_pairs"] = int(payload["top_k_pairs"])
    if "selection_top_n" in payload and payload["selection_top_n"] is not None:
        runtime["selection_top_n"] = int(payload["selection_top_n"])
    if "models_enabled" in payload and isinstance(payload["models_enabled"], dict):
        for model_name, enabled in payload["models_enabled"].items():
            if model_name in models and isinstance(models[model_name], dict):
                models[model_name]["enabled"] = bool(enabled)
    if "model_ranks" in payload and isinstance(payload["model_ranks"], dict):
        for model_name, ranks in payload["model_ranks"].items():
            if model_name in models and isinstance(models[model_name], dict):
                models[model_name]["ranks"] = ranks

    config_override_path = run_dir / "submitted_config.yaml"
    config_override_path.write_text(
        yaml.safe_dump(config_data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return config_override_path


def create_app(output_root: Path | None = None, default_config_path: Path | None = None):
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("FastAPI is required to run the web backend.") from exc

    app = FastAPI(title="Stock Tensor Experiment API")
    resolved_output_root = output_root or Path(os.environ.get("OUTPUT_ROOT", ROOT / "code" / "outputs"))
    config_path = default_config_path or Path(os.environ.get("DEFAULT_CONFIG_PATH", ROOT / "code" / "configs" / "default.yaml"))
    config_templates = {
        "cn_a": ROOT / "code" / "configs" / "default.yaml",
        "us_equity": ROOT / "code" / "configs" / "sample_us_equity.yaml",
    }

    @app.get("/api/markets")
    def api_markets() -> list[dict[str, str]]:
        return get_markets()

    @app.get("/api/runs")
    def api_runs() -> list[dict[str, Any]]:
        return list_runs(resolved_output_root)

    @app.post("/api/runs")
    def api_create_run(payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = payload or {}
        requested_run_id = body.get("run_id")
        run_sync = bool(body.get("run_sync", False))
        actual_run_id = requested_run_id or uuid.uuid4().hex[:12]
        run_dir = resolved_output_root / actual_run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        if body.get("config_path"):
            requested_config = Path(body["config_path"]).resolve()
        elif body.get("config_profile") == "sample_cn_smoke":
            requested_config = (ROOT / "code" / "configs" / "sample_cn_smoke.yaml").resolve()
        elif body.get("config_profile") == "sample_us_equity":
            requested_config = (ROOT / "code" / "configs" / "sample_us_equity.yaml").resolve()
        elif body.get("market_id") in config_templates:
            requested_config = config_templates[body["market_id"]].resolve()
        else:
            requested_config = Path(config_path).resolve()
        built_config_path = _build_run_config(
            base_config_path=requested_config,
            run_dir=run_dir,
            payload=body,
        )
        return submit_run(
            config_path=built_config_path,
            output_root=resolved_output_root,
            run_id=actual_run_id,
            run_sync=run_sync,
        )

    @app.get("/api/runs/{run_id}")
    def api_run_detail(run_id: str) -> dict[str, Any]:
        run_dir = resolved_output_root / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        return get_run_detail(resolved_output_root, run_id)

    @app.get("/api/runs/{run_id}/metrics")
    def api_run_metrics(run_id: str) -> list[dict[str, Any]]:
        run_dir = resolved_output_root / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        status = _load_status(run_dir)
        if status["status"] != "completed" or not (run_dir / "metrics.json").exists():
            raise HTTPException(status_code=409, detail="Run metrics are not available yet")
        return get_run_metrics(resolved_output_root, run_id)

    @app.get("/api/runs/{run_id}/selection")
    def api_run_selection(run_id: str, trade_date: str, top_n: int = 50) -> list[dict[str, Any]]:
        run_dir = resolved_output_root / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        status = _load_status(run_dir)
        if status["status"] != "completed" or not (run_dir / "selection_candidates.json").exists():
            raise HTTPException(status_code=409, detail="Selection results are not available yet")
        return get_selection_for_date(resolved_output_root, run_id, trade_date, top_n)

    return app
