from __future__ import annotations

import csv
import json
from collections import defaultdict
from html import escape
from pathlib import Path
from typing import Any

import yaml

from .evaluation import PairScore, SelectionRecord
from .path_utils import repo_relative_path


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
        return repo_relative_path(value)
    if isinstance(value, dict):
        return {key: _serialize_paths(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_serialize_paths(item) for item in value]
    if isinstance(value, tuple):
        return [_serialize_paths(item) for item in value]
    return value


def _format_metric_value(value: float) -> str:
    return f"{value:.3f}"


def _build_chart_scale(values: list[float]) -> tuple[float, float]:
    if not values:
        return -1.0, 1.0
    min_value = min(min(values), 0.0)
    max_value = max(max(values), 0.0)
    if abs(max_value - min_value) < 1e-9:
        span = max(abs(max_value), 1.0)
        return -span, span
    return min_value, max_value


def _map_value_to_y(value: float, *, min_value: float, max_value: float, top: float, height: float) -> float:
    value_range = max(max_value - min_value, 1e-9)
    return top + (max_value - value) / value_range * height


def _color_for_value(value: float) -> str:
    return "#2f6db2" if value >= 0 else "#c44536"


def _write_empty_svg(path: Path, title: str, message: str) -> None:
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='720' height='360'>"
        "<rect width='100%' height='100%' fill='#f7f8fb' />"
        f"<text x='360' y='36' text-anchor='middle' font-size='20'>{escape(title)}</text>"
        f"<text x='360' y='190' text-anchor='middle' font-size='16' fill='#666'>{escape(message)}</text>"
        "</svg>"
    )
    path.write_text(svg, encoding="utf-8")


def _write_simple_bar_svg(path: Path, title: str, values: dict[str, float]) -> None:
    if not values:
        _write_empty_svg(path, title, "暂无可视化数据")
        return

    width = 720
    height = 360
    margin = 60
    inner_width = width - margin * 2
    inner_height = height - margin * 2
    safe_values = {key: _safe_value(value) for key, value in values.items()}
    min_value, max_value = _build_chart_scale(list(safe_values.values()))
    zero_y = _map_value_to_y(0.0, min_value=min_value, max_value=max_value, top=margin, height=inner_height)
    bar_width = inner_width / max(len(safe_values), 1)

    axis_lines = []
    for tick in [max_value, 0.0, min_value]:
        tick_y = _map_value_to_y(tick, min_value=min_value, max_value=max_value, top=margin, height=inner_height)
        axis_lines.append(
            f"<line x1='{margin}' y1='{tick_y:.1f}' x2='{width - margin}' y2='{tick_y:.1f}' "
            "stroke='#d7dce5' stroke-dasharray='4 4' />"
        )
        axis_lines.append(
            f"<text x='{margin - 8}' y='{tick_y + 4:.1f}' text-anchor='end' font-size='11' fill='#555'>"
            f"{_format_metric_value(tick)}</text>"
        )

    bars: list[str] = []
    for index, (label, value) in enumerate(safe_values.items()):
        x_pos = margin + index * bar_width + 10
        value_y = _map_value_to_y(value, min_value=min_value, max_value=max_value, top=margin, height=inner_height)
        rect_y = min(value_y, zero_y)
        rect_height = max(abs(zero_y - value_y), 1.5)
        bars.append(
            f"<rect x='{x_pos:.1f}' y='{rect_y:.1f}' width='{bar_width - 20:.1f}' "
            f"height='{rect_height:.1f}' fill='{_color_for_value(value)}' rx='4' />"
        )
        bars.append(
            f"<text x='{x_pos + (bar_width - 20) / 2:.1f}' y='{height - margin + 18}' "
            f"text-anchor='middle' font-size='12'>{escape(label)}</text>"
        )
        label_y = value_y - 8 if value >= 0 else value_y + 18
        bars.append(
            f"<text x='{x_pos + (bar_width - 20) / 2:.1f}' y='{label_y:.1f}' "
            f"text-anchor='middle' font-size='12'>{_format_metric_value(value)}</text>"
        )

    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>"
        f"<rect width='100%' height='100%' fill='#f7f8fb' />"
        f"<text x='{width / 2}' y='28' text-anchor='middle' font-size='20'>{escape(title)}</text>"
        f"{''.join(axis_lines)}"
        f"<line x1='{margin}' y1='{zero_y:.1f}' x2='{width - margin}' y2='{zero_y:.1f}' stroke='#333' />"
        f"<line x1='{margin}' y1='{margin}' x2='{margin}' y2='{height - margin}' stroke='#333' />"
        f"{''.join(bars)}</svg>"
    )
    path.write_text(svg, encoding="utf-8")


def _normalize_metric(values: list[float], *, higher_is_better: bool) -> list[float]:
    if not values:
        return []
    min_value = min(values)
    max_value = max(values)
    if abs(max_value - min_value) < 1e-9:
        return [1.0 for _ in values]
    if higher_is_better:
        return [(value - min_value) / (max_value - min_value) for value in values]
    return [(max_value - value) / (max_value - min_value) for value in values]


def _write_model_metrics_overview_svg(path: Path, metrics_rows: list[dict[str, Any]]) -> None:
    if not metrics_rows:
        _write_empty_svg(path, "模型指标分组对比", "暂无指标数据")
        return

    panel_specs = [
        ("mse", "MSE", False),
        ("explained_variance", "解释方差", True),
        ("rank_ic_mean", "Rank IC", True),
        ("rolling_stability", "稳定性", True),
    ]
    model_colors = {
        "cp": "#3b82f6",
        "tucker": "#f59e0b",
        "pca": "#10b981",
    }
    width = 980
    height = 620
    outer_margin = 40
    title_height = 56
    panel_gap = 28
    panel_width = (width - outer_margin * 2 - panel_gap) / 2
    panel_height = (height - outer_margin * 2 - title_height - panel_gap) / 2

    body: list[str] = [
        f"<rect width='100%' height='100%' fill='#f7f8fb' />",
        "<text x='490' y='30' text-anchor='middle' font-size='24'>模型指标分组对比</text>",
    ]

    for index, (metric_key, metric_label, higher_is_better) in enumerate(panel_specs):
        panel_x = outer_margin + (index % 2) * (panel_width + panel_gap)
        panel_y = outer_margin + title_height + (index // 2) * (panel_height + panel_gap)
        panel_values = [_safe_value(float(row[metric_key])) for row in metrics_rows]
        min_value, max_value = _build_chart_scale(panel_values)
        zero_y = _map_value_to_y(
            0.0,
            min_value=min_value,
            max_value=max_value,
            top=panel_y + 30,
            height=panel_height - 70,
        )
        normalized = _normalize_metric(panel_values, higher_is_better=higher_is_better)

        body.append(
            f"<rect x='{panel_x:.1f}' y='{panel_y:.1f}' width='{panel_width:.1f}' height='{panel_height:.1f}' "
            "fill='#ffffff' stroke='#d7dce5' rx='10' />"
        )
        body.append(
            f"<text x='{panel_x + 18:.1f}' y='{panel_y + 24:.1f}' font-size='16'>{escape(metric_label)}</text>"
        )
        body.append(
            f"<text x='{panel_x + panel_width - 18:.1f}' y='{panel_y + 24:.1f}' text-anchor='end' "
            f"font-size='12' fill='#666'>{'越大越好' if higher_is_better else '越小越好'}</text>"
        )

        plot_x = panel_x + 48
        plot_y = panel_y + 30
        plot_width = panel_width - 66
        plot_height = panel_height - 70
        body.append(
            f"<line x1='{plot_x:.1f}' y1='{zero_y:.1f}' x2='{plot_x + plot_width:.1f}' y2='{zero_y:.1f}' "
            "stroke='#9aa4b2' />"
        )
        body.append(
            f"<line x1='{plot_x:.1f}' y1='{plot_y:.1f}' x2='{plot_x:.1f}' y2='{plot_y + plot_height:.1f}' "
            "stroke='#9aa4b2' />"
        )

        bar_width = plot_width / max(len(metrics_rows), 1)
        for row_index, row in enumerate(metrics_rows):
            value = panel_values[row_index]
            value_y = _map_value_to_y(
                value,
                min_value=min_value,
                max_value=max_value,
                top=plot_y,
                height=plot_height,
            )
            rect_y = min(value_y, zero_y)
            rect_height = max(abs(zero_y - value_y), 1.5)
            bar_x = plot_x + row_index * bar_width + 12
            label_x = bar_x + (bar_width - 24) / 2
            model_name = str(row["model"])
            body.append(
                f"<rect x='{bar_x:.1f}' y='{rect_y:.1f}' width='{bar_width - 24:.1f}' "
                f"height='{rect_height:.1f}' rx='4' fill='{model_colors.get(model_name, '#64748b')}' />"
            )
            body.append(
                f"<text x='{label_x:.1f}' y='{plot_y + plot_height + 18:.1f}' text-anchor='middle' "
                f"font-size='12'>{escape(model_name.upper())}</text>"
            )
            value_label_y = value_y - 8 if value >= 0 else value_y + 18
            body.append(
                f"<text x='{label_x:.1f}' y='{value_label_y:.1f}' text-anchor='middle' font-size='12'>"
                f"{_format_metric_value(value)}</text>"
            )
            score_x = bar_x
            score_y = panel_y + panel_height - 24
            score_width = bar_width - 24
            body.append(
                f"<rect x='{score_x:.1f}' y='{score_y:.1f}' width='{score_width:.1f}' height='6' "
                "fill='#e5e7eb' rx='3' />"
            )
            body.append(
                f"<rect x='{score_x:.1f}' y='{score_y:.1f}' width='{score_width * normalized[row_index]:.1f}' "
                f"height='6' fill='{model_colors.get(model_name, '#64748b')}' rx='3' />"
            )

    path.write_text(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>{''.join(body)}</svg>",
        encoding="utf-8",
    )


def _build_time_regime_series(candidate_rows: list[dict[str, Any]]) -> list[tuple[str, float]]:
    aggregated: dict[str, list[float]] = defaultdict(list)
    for row in candidate_rows:
        trade_date = str(row.get("trade_date", "")).strip()
        if not trade_date:
            continue
        score = row.get("time_regime_score")
        if score is None:
            continue
        aggregated[trade_date].append(_safe_value(float(score)))
    return [
        (trade_date, sum(values) / len(values))
        for trade_date, values in sorted(aggregated.items())
        if values
    ]


def _extract_shift_entry(entry: Any) -> tuple[str, str, float]:
    if isinstance(entry, dict):
        return str(entry["from"]), str(entry["to"]), _safe_value(float(entry["shift_score"]))
    return str(entry.left), str(entry.right), _safe_value(float(entry.score))


def _write_time_regime_timeline_svg(
    path: Path,
    time_regime_series: list[tuple[str, float]],
    time_shifts: dict[str, list[Any]],
) -> None:
    if not time_regime_series:
        _write_empty_svg(path, "时间状态变化图", "暂无时间状态数据")
        return

    width = 980
    height = 420
    margin_left = 84
    margin_right = 40
    margin_top = 54
    margin_bottom = 74
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    values = [value for _, value in time_regime_series]
    min_value, max_value = _build_chart_scale(values)
    if max_value <= 0:
        max_value = max(max(values), 0.1)
        min_value = min(min(values), 0.0)
    points: list[str] = []
    circles: list[str] = []
    for index, (trade_date, value) in enumerate(time_regime_series):
        x_pos = margin_left + (plot_width * index / max(len(time_regime_series) - 1, 1))
        y_pos = _map_value_to_y(value, min_value=min_value, max_value=max_value, top=margin_top, height=plot_height)
        points.append(f"{x_pos:.1f},{y_pos:.1f}")
        if index in {0, len(time_regime_series) // 2, len(time_regime_series) - 1}:
            circles.append(
                f"<text x='{x_pos:.1f}' y='{height - 28:.1f}' text-anchor='middle' font-size='11' fill='#555'>"
                f"{escape(trade_date)}</text>"
            )

    marker_candidates: list[tuple[str, str, str, float]] = []
    for model_name, entries in time_shifts.items():
        for entry in entries:
            shift_from, shift_to, shift_score = _extract_shift_entry(entry)
            marker_candidates.append((model_name, shift_from, shift_to, shift_score))
    marker_candidates.sort(key=lambda item: item[3], reverse=True)

    markers: list[str] = []
    marker_dates = {trade_date: value for trade_date, value in time_regime_series}
    for marker_index, (model_name, _, shift_to, shift_score) in enumerate(marker_candidates[:4]):
        if shift_to not in marker_dates:
            continue
        date_index = next(index for index, (trade_date, _) in enumerate(time_regime_series) if trade_date == shift_to)
        x_pos = margin_left + (plot_width * date_index / max(len(time_regime_series) - 1, 1))
        y_pos = _map_value_to_y(
            marker_dates[shift_to],
            min_value=min_value,
            max_value=max_value,
            top=margin_top,
            height=plot_height,
        )
        label_y = margin_top + 24 + marker_index * 16
        markers.append(f"<circle cx='{x_pos:.1f}' cy='{y_pos:.1f}' r='4' fill='#c44536' />")
        markers.append(
            f"<line x1='{x_pos:.1f}' y1='{y_pos:.1f}' x2='{x_pos:.1f}' y2='{label_y + 4:.1f}' "
            "stroke='#c44536' stroke-dasharray='3 3' />"
        )
        markers.append(
            f"<text x='{x_pos + 6:.1f}' y='{label_y:.1f}' font-size='11' fill='#7a1f16'>"
            f"{escape(model_name.upper())} {escape(shift_to)} ({_format_metric_value(shift_score)})</text>"
        )

    axis = []
    for tick in [max_value, (max_value + min_value) / 2, min_value]:
        tick_y = _map_value_to_y(tick, min_value=min_value, max_value=max_value, top=margin_top, height=plot_height)
        axis.append(
            f"<line x1='{margin_left:.1f}' y1='{tick_y:.1f}' x2='{width - margin_right:.1f}' y2='{tick_y:.1f}' "
            "stroke='#d7dce5' stroke-dasharray='4 4' />"
        )
        axis.append(
            f"<text x='{margin_left - 10:.1f}' y='{tick_y + 4:.1f}' text-anchor='end' font-size='11' fill='#555'>"
            f"{_format_metric_value(tick)}</text>"
        )

    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>"
        "<rect width='100%' height='100%' fill='#f7f8fb' />"
        "<text x='490' y='30' text-anchor='middle' font-size='24'>时间状态变化图</text>"
        "<text x='490' y='50' text-anchor='middle' font-size='12' fill='#666'>"
        "基于 unified selection candidate 的日均 time regime score</text>"
        f"{''.join(axis)}"
        f"<line x1='{margin_left:.1f}' y1='{margin_top:.1f}' x2='{margin_left:.1f}' y2='{height - margin_bottom:.1f}' stroke='#9aa4b2' />"
        f"<line x1='{margin_left:.1f}' y1='{height - margin_bottom:.1f}' x2='{width - margin_right:.1f}' y2='{height - margin_bottom:.1f}' stroke='#9aa4b2' />"
        f"<polyline fill='none' stroke='#2f6db2' stroke-width='3' points='{' '.join(points)}' />"
        f"{''.join(markers)}"
        f"{''.join(circles)}"
        "</svg>"
    )
    path.write_text(svg, encoding="utf-8")


def _heatmap_color(value: float, max_value: float) -> str:
    ratio = 0.0 if max_value <= 0 else max(0.0, min(value / max_value, 1.0))
    red = int(241 - ratio * 150)
    green = int(245 - ratio * 92)
    blue = int(249 - ratio * 106)
    return f"#{red:02x}{green:02x}{blue:02x}"


def _write_factor_importance_heatmap_svg(path: Path, factor_summaries: dict[str, list[dict[str, Any]]]) -> None:
    if not factor_summaries:
        _write_empty_svg(path, "因子载荷热力图", "暂无因子摘要数据")
        return

    factor_names = sorted(
        {
            str(row["factor_name"])
            for rows in factor_summaries.values()
            for row in rows
            if row.get("factor_name")
        },
        key=lambda factor_name: -sum(
            _safe_value(float(row["importance"]))
            for rows in factor_summaries.values()
            for row in rows
            if row.get("factor_name") == factor_name
        ),
    )
    if not factor_names:
        _write_empty_svg(path, "因子载荷热力图", "暂无因子摘要数据")
        return

    row_labels = list(factor_summaries.keys())
    max_value = max(
        _safe_value(float(row["importance"]))
        for rows in factor_summaries.values()
        for row in rows
        if row.get("importance") is not None
    )
    width = max(860, 180 + len(factor_names) * 132)
    height = 180 + len(row_labels) * 70
    cell_width = 120
    cell_height = 52
    start_x = 160
    start_y = 78
    lookup = {
        (model_name, str(row["factor_name"])): _safe_value(float(row["importance"]))
        for model_name, rows in factor_summaries.items()
        for row in rows
        if row.get("factor_name")
    }

    body: list[str] = [
        "<rect width='100%' height='100%' fill='#f7f8fb' />",
        f"<text x='{width / 2:.1f}' y='30' text-anchor='middle' font-size='24'>因子载荷热力图</text>",
        f"<text x='{width / 2:.1f}' y='50' text-anchor='middle' font-size='12' fill='#666'>"
        "颜色越深表示模型对该因子的相对重要性越高</text>",
    ]

    for column_index, factor_name in enumerate(factor_names):
        x_pos = start_x + column_index * cell_width
        body.append(
            f"<text x='{x_pos + cell_width / 2:.1f}' y='{start_y - 12:.1f}' text-anchor='middle' font-size='12'>"
            f"{escape(factor_name)}</text>"
        )

    for row_index, model_name in enumerate(row_labels):
        y_pos = start_y + row_index * cell_height
        body.append(
            f"<text x='{start_x - 14:.1f}' y='{y_pos + cell_height / 2 + 4:.1f}' text-anchor='end' font-size='13'>"
            f"{escape(model_name.upper())}</text>"
        )
        for column_index, factor_name in enumerate(factor_names):
            x_pos = start_x + column_index * cell_width
            importance = lookup.get((model_name, factor_name), 0.0)
            fill = _heatmap_color(importance, max_value)
            body.append(
                f"<rect x='{x_pos:.1f}' y='{y_pos:.1f}' width='{cell_width - 8:.1f}' height='{cell_height - 8:.1f}' "
                f"rx='8' fill='{fill}' stroke='#d7dce5' />"
            )
            body.append(
                f"<text x='{x_pos + (cell_width - 8) / 2:.1f}' y='{y_pos + 22:.1f}' text-anchor='middle' "
                f"font-size='11'>{escape(factor_name)}</text>"
            )
            body.append(
                f"<text x='{x_pos + (cell_width - 8) / 2:.1f}' y='{y_pos + 38:.1f}' text-anchor='middle' "
                f"font-size='12' fill='#111'>{_format_metric_value(importance)}</text>"
            )

    path.write_text(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>{''.join(body)}</svg>",
        encoding="utf-8",
    )


def write_visual_assets(
    output_dir: Path,
    metrics_rows: list[dict[str, Any]],
    factor_summaries: dict[str, list[dict[str, Any]]],
    time_shifts: dict[str, list[Any]],
    candidate_rows: list[dict[str, Any]],
    *,
    time_regime_series: list[tuple[str, float]] | None = None,
) -> None:
    _write_simple_bar_svg(
        output_dir / "model_explained_variance.svg",
        "模型解释方差对比",
        {row["model"]: float(row["explained_variance"]) for row in metrics_rows},
    )
    _write_simple_bar_svg(
        output_dir / "model_rank_ic.svg",
        "模型 Rank IC 对比",
        {row["model"]: float(row["rank_ic_mean"]) for row in metrics_rows},
    )
    _write_model_metrics_overview_svg(output_dir / "model_metrics_overview.svg", metrics_rows)
    _write_time_regime_timeline_svg(
        output_dir / "time_regime_timeline.svg",
        time_regime_series if time_regime_series is not None else _build_time_regime_series(candidate_rows),
        time_shifts,
    )
    _write_factor_importance_heatmap_svg(output_dir / "factor_importance_heatmap.svg", factor_summaries)


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

    write_visual_assets(
        output_dir,
        metrics_rows=metrics_rows,
        factor_summaries=factor_summaries,
        time_shifts=time_shifts,
        candidate_rows=candidate_rows,
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
    summary_lines.append("- `model_explained_variance.svg` and `model_rank_ic.svg`: signed metric bar charts")
    summary_lines.append("- `model_metrics_overview.svg`: grouped comparison of core metrics")
    summary_lines.append("- `time_regime_timeline.svg`: timeline of daily regime shifts")
    summary_lines.append("- `factor_importance_heatmap.svg`: factor importance heatmap across models")
    (output_dir / "summary.md").write_text("\n".join(summary_lines), encoding="utf-8")
