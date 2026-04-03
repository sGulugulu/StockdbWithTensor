from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

import yaml

from .evaluation import PairScore, SelectionRecord


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def _safe_value(value: float) -> float:
    return 0.0 if value != value else value


def _serialize_paths(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, dict):
        return {key: _serialize_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_paths(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_paths(item) for item in value]
    return value


def _write_simple_bar_svg(path: Path, title: str, values: dict[str, float]) -> None:
    width = 720
    height = 360
    margin = 60
    inner_width = width - margin * 2
    inner_height = height - margin * 2
    safe_values = {key: _safe_value(value) for key, value in values.items()}
    max_value = max(safe_values.values()) if safe_values else 1.0
    max_value = max(max_value, 1.0)
    bar_width = inner_width / max(len(safe_values), 1)

    bars: list[str] = []
    for index, (label, value) in enumerate(safe_values.items()):
        bar_height = inner_height * max(value, 0.0) / max_value
        x_pos = margin + index * bar_width + 10
        y_pos = height - margin - bar_height
        bars.append(
            f"<rect x='{x_pos:.1f}' y='{y_pos:.1f}' width='{bar_width - 20:.1f}' "
            f"height='{bar_height:.1f}' fill='#3a6ea5' />"
        )
        bars.append(
            f"<text x='{x_pos + (bar_width - 20) / 2:.1f}' y='{height - margin + 18}' "
            f"text-anchor='middle' font-size='12'>{label}</text>"
        )
        bars.append(
            f"<text x='{x_pos + (bar_width - 20) / 2:.1f}' y='{y_pos - 6:.1f}' "
            f"text-anchor='middle' font-size='12'>{value:.3f}</text>"
        )

    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>"
        f"<rect width='100%' height='100%' fill='#f7f8fb' />"
        f"<text x='{width / 2}' y='28' text-anchor='middle' font-size='20'>{title}</text>"
        f"<line x1='{margin}' y1='{height - margin}' x2='{width - margin}' y2='{height - margin}' stroke='#333' />"
        f"<line x1='{margin}' y1='{margin}' x2='{margin}' y2='{height - margin}' stroke='#333' />"
        f"{''.join(bars)}</svg>"
    )
    path.write_text(svg, encoding="utf-8")


def write_outputs(
    output_dir: Path,
    config_snapshot: dict[str, Any],
    logs: list[str],
    metrics_rows: list[dict[str, Any]],
    stock_pairs: dict[str, list[PairScore]],
    factor_pairs: dict[str, list[PairScore]],
    time_shifts: dict[str, list[PairScore]],
    selection_rows: dict[str, list[SelectionRecord]],
    candidate_rows: list[dict[str, Any]],
    factor_summaries: dict[str, list[dict[str, Any]]],
    run_manifest: dict[str, Any],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "config_snapshot.yaml").write_text(
        yaml.safe_dump(_serialize_paths(config_snapshot), sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    (output_dir / "run.log").write_text("\n".join(logs), encoding="utf-8")
    _write_csv(output_dir / "metrics.csv", metrics_rows)
    (output_dir / "metrics.json").write_text(
        json.dumps(metrics_rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    (output_dir / "run_manifest.json").write_text(
        json.dumps(_serialize_paths(run_manifest), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    for model_name, pairs in stock_pairs.items():
        _write_csv(
            output_dir / f"stock_similarity_{model_name}.csv",
            [{"left": pair.left, "right": pair.right, "score": pair.score} for pair in pairs],
        )
    for model_name, pairs in factor_pairs.items():
        _write_csv(
            output_dir / f"factor_association_{model_name}.csv",
            [{"left": pair.left, "right": pair.right, "score": pair.score} for pair in pairs],
        )
        (output_dir / f"factor_association_{model_name}.json").write_text(
            json.dumps(
                [{"left": pair.left, "right": pair.right, "score": pair.score} for pair in pairs],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    for model_name, pairs in time_shifts.items():
        _write_csv(
            output_dir / f"time_regimes_{model_name}.csv",
            [{"from": pair.left, "to": pair.right, "shift_score": pair.score} for pair in pairs],
        )
        (output_dir / f"time_regimes_{model_name}.json").write_text(
            json.dumps(
                [{"from": pair.left, "to": pair.right, "shift_score": pair.score} for pair in pairs],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    for model_name, rows in selection_rows.items():
        _write_csv(
            output_dir / f"selection_{model_name}.csv",
            [
                {
                    "trade_date": row.trade_date,
                    "stock_code": row.stock_code,
                    "model": row.model,
                    "rank": row.rank_label,
                    "market_id": row.market_id,
                    "universe_id": row.universe_id,
                    "total_score": row.total_score,
                    "stock_score": row.stock_score,
                    "selection_signal": row.selection_signal,
                    "time_regime_score": row.time_regime_score,
                    "cluster_label": row.cluster_label,
                    "top_factor_1": row.top_factor_1,
                    "top_factor_1_score": row.top_factor_1_score,
                    "top_factor_2": row.top_factor_2,
                    "top_factor_2_score": row.top_factor_2_score,
                    "top_factor_3": row.top_factor_3,
                    "top_factor_3_score": row.top_factor_3_score,
                }
                for row in rows
            ],
        )
        (output_dir / f"selection_{model_name}.json").write_text(
            json.dumps(
                [
                    {
                        "trade_date": row.trade_date,
                        "stock_code": row.stock_code,
                        "model": row.model,
                        "rank": row.rank_label,
                        "market_id": row.market_id,
                        "universe_id": row.universe_id,
                        "total_score": row.total_score,
                        "stock_score": row.stock_score,
                        "selection_signal": row.selection_signal,
                        "time_regime_score": row.time_regime_score,
                        "cluster_label": row.cluster_label,
                        "top_factor_1": row.top_factor_1,
                        "top_factor_1_score": row.top_factor_1_score,
                        "top_factor_2": row.top_factor_2,
                        "top_factor_2_score": row.top_factor_2_score,
                        "top_factor_3": row.top_factor_3,
                        "top_factor_3_score": row.top_factor_3_score,
                    }
                    for row in rows
                ],
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    for model_name, rows in factor_summaries.items():
        _write_csv(output_dir / f"factor_summary_{model_name}.csv", rows)
        (output_dir / f"factor_summary_{model_name}.json").write_text(
            json.dumps(rows, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    _write_csv(output_dir / "selection_candidates.csv", candidate_rows)
    (output_dir / "selection_candidates.json").write_text(
        json.dumps(candidate_rows, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    _write_simple_bar_svg(
        output_dir / "model_explained_variance.svg",
        "Model Explained Variance",
        {row["model"]: float(row["explained_variance"]) for row in metrics_rows},
    )
    _write_simple_bar_svg(
        output_dir / "model_rank_ic.svg",
        "Model RankIC",
        {row["model"]: float(row["rank_ic_mean"]) for row in metrics_rows},
    )

    summary_lines = [
        "# Experiment Summary",
        "",
        "## Models",
    ]
    for row in metrics_rows:
        summary_lines.append(
            f"- {row['model']}: rank={row['rank']}, mse={row['mse']:.6f}, "
            f"explained_variance={row['explained_variance']:.4f}, "
            f"rank_ic_mean={row['rank_ic_mean']:.4f}"
        )
    summary_lines.append("")
    summary_lines.append("## Output Files")
    summary_lines.append("- `metrics.csv` / `metrics.json`: model comparison table")
    summary_lines.append("- `stock_similarity_*.csv`: stock linkage candidates")
    summary_lines.append("- `factor_association_*.csv`: factor resonance candidates")
    summary_lines.append("- `time_regimes_*.csv`: largest adjacent time shifts")
    summary_lines.append("- `selection_*.csv` / `selection_*.json`: per-date stock selection signals")
    summary_lines.append("- `selection_candidates.csv` / `selection_candidates.json`: unified per-date candidate pool")
    summary_lines.append("- `factor_summary_*.csv` / `factor_summary_*.json`: factor importance summaries")
    summary_lines.append("- `run_manifest.json`: machine-readable run metadata for web services")
    summary_lines.append("- `model_explained_variance.svg` and `model_rank_ic.svg`: quick visual summaries")
    (output_dir / "summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
