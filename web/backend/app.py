from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def list_runs(output_root: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    if not output_root.exists():
        return runs
    for child in sorted(output_root.iterdir()):
        if not child.is_dir():
            continue
        manifest_path = child / "run_manifest.json"
        summary_path = child / "summary.md"
        metrics_path = child / "metrics.json"
        if not manifest_path.exists():
            continue
        runs.append(
            {
                "run_id": child.name,
                "manifest": _read_json(manifest_path),
                "summary_exists": summary_path.exists(),
                "metrics_exists": metrics_path.exists(),
            }
        )
    return runs


def get_run_detail(output_root: Path, run_id: str) -> dict[str, Any]:
    run_dir = output_root / run_id
    return {
        "run_id": run_id,
        "manifest": _read_json(run_dir / "run_manifest.json"),
        "metrics": _read_json(run_dir / "metrics.json"),
    }


def get_run_metrics(output_root: Path, run_id: str) -> list[dict[str, Any]]:
    return _read_json(output_root / run_id / "metrics.json")


def get_selection_for_date(output_root: Path, run_id: str, trade_date: str, top_n: int) -> list[dict[str, Any]]:
    run_dir = output_root / run_id
    selection_rows: list[dict[str, Any]] = []
    for selection_file in sorted(run_dir.glob("selection_*.json")):
        rows = _read_json(selection_file)
        selection_rows.extend(
            row
            for row in rows
            if row["trade_date"] == trade_date
        )
    selection_rows.sort(key=lambda item: float(item["score"]), reverse=True)
    return selection_rows[:top_n]


def get_markets() -> list[dict[str, str]]:
    return [
        {"market_id": "cn_a", "market_name": "A股", "default_universe_id": "CSI_A500"},
        {"market_id": "us_equity", "market_name": "美股", "default_universe_id": "EXTERNAL_LIST"},
    ]


def create_app(output_root: Path):
    try:
        from fastapi import FastAPI, HTTPException
    except ImportError as exc:
        raise RuntimeError("FastAPI is required to run the web backend.") from exc

    app = FastAPI(title="Stock Tensor Experiment API")

    @app.get("/api/markets")
    def api_markets() -> list[dict[str, str]]:
        return get_markets()

    @app.get("/api/runs")
    def api_runs() -> list[dict[str, Any]]:
        return list_runs(output_root)

    @app.get("/api/runs/{run_id}")
    def api_run_detail(run_id: str) -> dict[str, Any]:
        run_dir = output_root / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        return get_run_detail(output_root, run_id)

    @app.get("/api/runs/{run_id}/metrics")
    def api_run_metrics(run_id: str) -> list[dict[str, Any]]:
        run_dir = output_root / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        return get_run_metrics(output_root, run_id)

    @app.get("/api/runs/{run_id}/selection")
    def api_run_selection(run_id: str, trade_date: str, top_n: int = 50) -> list[dict[str, Any]]:
        run_dir = output_root / run_id
        if not run_dir.exists():
            raise HTTPException(status_code=404, detail="Run not found")
        return get_selection_for_date(output_root, run_id, trade_date, top_n)

    return app
