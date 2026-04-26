from __future__ import annotations

import argparse
import csv
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from html import escape
from pathlib import Path
import sys
from typing import Any

import yaml

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))


@dataclass(frozen=True, slots=True)
class PatternAssetResult:
    stock_structure_svg: Path
    cluster_industry_svg: Path
    boundary_comparison_svg: Path
    summary_json: Path
    summary_md: Path


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_factor_industries(panel_path: Path) -> dict[str, str]:
    industry_by_stock: dict[str, Counter[str]] = defaultdict(Counter)
    with panel_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            stock_code = row.get("stock_code", "").strip()
            industry = row.get("industry", "").strip() or "UNKNOWN"
            if stock_code:
                industry_by_stock[stock_code][industry] += 1
    return {
        stock_code: counter.most_common(1)[0][0]
        for stock_code, counter in industry_by_stock.items()
        if counter
    }


def _resolve_project_path(raw_path: str, *, project_root: Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return project_root / raw_path


def _selection_rows(output_dir: Path, model_name: str) -> list[dict[str, Any]]:
    path = output_dir / f"selection_{model_name}.json"
    if not path.exists():
        return []
    return list(_load_json(path))


def _stock_summary_rows(
    *,
    output_dir: Path,
    model_name: str,
    project_root: Path,
    max_stocks: int,
) -> list[dict[str, Any]]:
    snapshot = yaml.safe_load((output_dir / "config_snapshot.yaml").read_text(encoding="utf-8"))
    panel_path = _resolve_project_path(snapshot["data"]["path"], project_root=project_root)
    industries = _load_factor_industries(panel_path)
    by_stock: dict[str, dict[str, Any]] = {}
    for row in _selection_rows(output_dir, model_name):
        stock_code = str(row["stock_code"])
        current = by_stock.setdefault(
            stock_code,
            {
                "stock_code": stock_code,
                "cluster_label": int(row.get("cluster_label", 0)),
                "industry": industries.get(stock_code, "UNKNOWN"),
                "appearances": 0,
                "score_sum": 0.0,
            },
        )
        current["appearances"] += 1
        current["score_sum"] += float(row.get("total_score", 0.0))
    rows = []
    for row in by_stock.values():
        row["avg_score"] = row["score_sum"] / max(row["appearances"], 1)
        del row["score_sum"]
        rows.append(row)
    rows.sort(key=lambda item: (int(item["cluster_label"]), -float(item["avg_score"]), item["stock_code"]))
    return rows[:max_stocks]


def _write_stock_structure_svg(path: Path, rows: list[dict[str, Any]], *, title: str) -> None:
    width = 980
    height = 560
    margin_x = 80
    margin_y = 92
    plot_width = width - margin_x * 2
    plot_height = height - margin_y - 80
    clusters = sorted({int(row["cluster_label"]) for row in rows})
    cluster_index = {cluster: index for index, cluster in enumerate(clusters)}
    industry_colors = {
        industry: color
        for industry, color in zip(
            sorted({str(row["industry"]) for row in rows}),
            ["#2f6db2", "#d06f2c", "#2f8f6b", "#8b5fbf", "#c44536", "#596579", "#b78b20"],
        )
    }
    cluster_counts: dict[int, int] = defaultdict(int)
    body: list[str] = [
        "<rect width='100%' height='100%' fill='#f7f8fb' />",
        f"<text x='{width / 2}' y='34' text-anchor='middle' font-size='22'>{escape(title)}</text>",
        "<text x='490' y='58' text-anchor='middle' font-size='12' fill='#666'>"
        "横向表示模型聚类标签，纵向按平均潜在得分排序；颜色表示股票所属行业</text>",
    ]
    for cluster, index in cluster_index.items():
        x_pos = margin_x + (index + 0.5) * plot_width / max(len(clusters), 1)
        body.append(
            f"<line x1='{x_pos:.1f}' y1='{margin_y - 16}' x2='{x_pos:.1f}' y2='{height - 72}' "
            "stroke='#d7dce5' stroke-dasharray='4 4' />"
        )
        body.append(
            f"<text x='{x_pos:.1f}' y='{height - 42}' text-anchor='middle' font-size='13'>Cluster {cluster}</text>"
        )
    for row in rows:
        cluster = int(row["cluster_label"])
        slot = cluster_counts[cluster]
        cluster_counts[cluster] += 1
        x_base = margin_x + (cluster_index[cluster] + 0.5) * plot_width / max(len(clusters), 1)
        x_pos = x_base + ((slot % 5) - 2) * 26
        y_pos = margin_y + (slot // 5) * 42
        if y_pos > margin_y + plot_height:
            continue
        radius = min(18, 8 + float(row["avg_score"]) * 8)
        fill = industry_colors.get(str(row["industry"]), "#596579")
        body.append(
            f"<circle cx='{x_pos:.1f}' cy='{y_pos:.1f}' r='{radius:.1f}' fill='{fill}' "
            "fill-opacity='0.86' stroke='#1f2937' stroke-width='0.8' />"
        )
        body.append(
            f"<text x='{x_pos:.1f}' y='{y_pos + 4:.1f}' text-anchor='middle' font-size='9' fill='#fff'>"
            f"{escape(str(row['stock_code']).split('.')[0][-3:])}</text>"
        )
    legend_y = height - 18
    for index, (industry, color) in enumerate(industry_colors.items()):
        x_pos = margin_x + index * 130
        body.append(f"<rect x='{x_pos}' y='{legend_y - 10}' width='12' height='12' fill='{color}' rx='2' />")
        body.append(f"<text x='{x_pos + 18}' y='{legend_y}' font-size='11'>{escape(industry[:14])}</text>")
    path.write_text(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>{''.join(body)}</svg>",
        encoding="utf-8",
    )


def _write_cluster_industry_svg(path: Path, rows: list[dict[str, Any]], *, title: str) -> None:
    clusters = sorted({int(row["cluster_label"]) for row in rows})
    industries = sorted({str(row["industry"]) for row in rows})
    counts = Counter((int(row["cluster_label"]), str(row["industry"])) for row in rows)
    max_count = max(counts.values(), default=1)
    cell_width = 118
    cell_height = 48
    width = max(760, 190 + len(industries) * cell_width)
    height = 150 + len(clusters) * cell_height
    body: list[str] = [
        "<rect width='100%' height='100%' fill='#f7f8fb' />",
        f"<text x='{width / 2}' y='32' text-anchor='middle' font-size='22'>{escape(title)}</text>",
        "<text x='110' y='78' text-anchor='end' font-size='12' fill='#666'>聚类</text>",
    ]
    for column, industry in enumerate(industries):
        x_pos = 150 + column * cell_width
        body.append(
            f"<text x='{x_pos + cell_width / 2:.1f}' y='78' text-anchor='middle' font-size='11'>"
            f"{escape(industry[:12])}</text>"
        )
    for row_index, cluster in enumerate(clusters):
        y_pos = 98 + row_index * cell_height
        body.append(f"<text x='110' y='{y_pos + 29}' text-anchor='end' font-size='12'>Cluster {cluster}</text>")
        for column, industry in enumerate(industries):
            x_pos = 150 + column * cell_width
            count = counts.get((cluster, industry), 0)
            ratio = count / max_count
            fill = f"#{int(239 - ratio * 136):02x}{int(246 - ratio * 78):02x}{int(255 - ratio * 31):02x}"
            body.append(
                f"<rect x='{x_pos}' y='{y_pos}' width='{cell_width - 8}' height='{cell_height - 8}' "
                f"fill='{fill}' stroke='#d7dce5' rx='6' />"
            )
            body.append(
                f"<text x='{x_pos + (cell_width - 8) / 2:.1f}' y='{y_pos + 25}' "
                f"text-anchor='middle' font-size='13'>{count}</text>"
            )
    path.write_text(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>{''.join(body)}</svg>",
        encoding="utf-8",
    )


def _final_nav(output_dir: Path, model_name: str) -> float:
    path = output_dir / f"group_returns_{model_name}.json"
    if not path.exists():
        return 1.0
    rows = _load_json(path)
    if not rows:
        return 1.0
    return float(rows[-1].get("cumulative_nav", 1.0))


def _boundary_rows(run_dirs: list[Path]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for output_dir in run_dirs:
        if not (output_dir / "metrics.json").exists():
            continue
        manifest = _load_json(output_dir / "run_manifest.json")
        universe_id = str(manifest.get("market", {}).get("universe_id", output_dir.name))
        for metric in _load_json(output_dir / "metrics.json"):
            model_name = str(metric["model"])
            rows.append(
                {
                    "run": output_dir.name,
                    "universe_id": universe_id,
                    "model": model_name,
                    "rank_ic_mean": float(metric.get("rank_ic_mean", 0.0)),
                    "rolling_stability": float(metric.get("rolling_stability", 0.0)),
                    "final_nav": _final_nav(output_dir, model_name),
                }
            )
    return rows


def _write_boundary_svg(path: Path, rows: list[dict[str, Any]]) -> None:
    tucker_rows = [row for row in rows if row["model"] == "tucker"]
    width = 1080
    height = 520
    left = 78
    top = 70
    plot_width = width - 130
    plot_height = 300
    labels = [str(row["universe_id"]) for row in tucker_rows]
    values = [float(row["rank_ic_mean"]) for row in tucker_rows]
    nav_values = [float(row["final_nav"]) - 1.0 for row in tucker_rows]
    all_values = values + nav_values + [0.0]
    min_value = min(all_values) if all_values else -0.1
    max_value = max(all_values) if all_values else 0.1
    if abs(max_value - min_value) < 1e-9:
        min_value, max_value = -0.1, 0.1

    def y_pos(value: float) -> float:
        return top + (max_value - value) / max(max_value - min_value, 1e-9) * plot_height

    body: list[str] = [
        "<rect width='100%' height='100%' fill='#f7f8fb' />",
        "<text x='540' y='34' text-anchor='middle' font-size='22'>跨样本边界 Tucker 指标对比</text>",
        "<text x='540' y='56' text-anchor='middle' font-size='12' fill='#666'>"
        "蓝色为 Rank IC，橙色为组合累计收益率</text>",
        f"<line x1='{left}' y1='{top}' x2='{left}' y2='{top + plot_height}' stroke='#333' />",
        f"<line x1='{left}' y1='{y_pos(0.0):.1f}' x2='{left + plot_width}' y2='{y_pos(0.0):.1f}' stroke='#64748b' />",
    ]
    bar_slot = plot_width / max(len(labels), 1)
    for index, label in enumerate(labels):
        x_base = left + index * bar_slot + 14
        for offset, value, color in ((0, values[index], "#2f6db2"), (24, nav_values[index], "#d06f2c")):
            y_value = y_pos(value)
            y_zero = y_pos(0.0)
            body.append(
                f"<rect x='{x_base + offset:.1f}' y='{min(y_value, y_zero):.1f}' width='20' "
                f"height='{max(abs(y_zero - y_value), 1.5):.1f}' fill='{color}' rx='3' />"
            )
        body.append(
            f"<text x='{x_base + 22:.1f}' y='{height - 54}' text-anchor='end' font-size='10' "
            f"transform='rotate(-38 {x_base + 22:.1f},{height - 54})'>{escape(label)}</text>"
        )
    body.append(f"<text x='{left - 8}' y='{y_pos(max_value) + 4:.1f}' text-anchor='end' font-size='11'>{max_value:.2f}</text>")
    body.append(f"<text x='{left - 8}' y='{y_pos(0.0) + 4:.1f}' text-anchor='end' font-size='11'>0.00</text>")
    body.append(f"<text x='{left - 8}' y='{y_pos(min_value) + 4:.1f}' text-anchor='end' font-size='11'>{min_value:.2f}</text>")
    path.write_text(
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>{''.join(body)}</svg>",
        encoding="utf-8",
    )


def build_pattern_discovery_assets(
    *,
    project_root: Path,
    anchor_output_dir: Path,
    comparison_output_dirs: list[Path],
    output_dir: Path,
    model_name: str = "tucker",
    max_stocks: int = 60,
) -> PatternAssetResult:
    output_dir.mkdir(parents=True, exist_ok=True)
    stock_rows = _stock_summary_rows(
        output_dir=anchor_output_dir,
        model_name=model_name,
        project_root=project_root,
        max_stocks=max_stocks,
    )
    boundary_rows = _boundary_rows(comparison_output_dirs)
    stock_svg = output_dir / f"stock_latent_structure_{anchor_output_dir.name}_{model_name}.svg"
    cluster_svg = output_dir / f"cluster_vs_industry_{anchor_output_dir.name}_{model_name}.svg"
    boundary_svg = output_dir / "boundary_comparison_tucker.svg"
    _write_stock_structure_svg(stock_svg, stock_rows, title=f"{anchor_output_dir.name} 股票潜在结构图")
    _write_cluster_industry_svg(cluster_svg, stock_rows, title=f"{anchor_output_dir.name} 聚类与行业交叉图")
    _write_boundary_svg(boundary_svg, boundary_rows)
    summary = {
        "anchor_run": anchor_output_dir.name,
        "model": model_name,
        "stock_count": len(stock_rows),
        "comparison_run_count": len(comparison_output_dirs),
        "stock_rows": stock_rows,
        "boundary_rows": boundary_rows,
        "assets": {
            "stock_structure_svg": stock_svg.as_posix(),
            "cluster_industry_svg": cluster_svg.as_posix(),
            "boundary_comparison_svg": boundary_svg.as_posix(),
        },
    }
    summary_json = output_dir / "pattern_discovery_summary.json"
    summary_json.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    summary_md = output_dir / "README.md"
    summary_md.write_text(
        "\n".join(
            [
                "# 模式发现扩展图组",
                "",
                f"- 锚定样本：`{anchor_output_dir.name}`",
                f"- 锚定模型：`{model_name}`",
                f"- 股票潜在结构图：`{stock_svg.name}`",
                f"- 聚类与行业交叉图：`{cluster_svg.name}`",
                f"- 跨样本边界对比图：`{boundary_svg.name}`",
                "",
                "这些图由 formal run 的 `selection_*.json`、`metrics.json`、`group_returns_*.json` 与因子面板行业字段生成，用于补足股票联动结构、行业聚类关系和样本边界差异的可视化证据。",
            ]
        ),
        encoding="utf-8",
    )
    return PatternAssetResult(
        stock_structure_svg=stock_svg,
        cluster_industry_svg=cluster_svg,
        boundary_comparison_svg=boundary_svg,
        summary_json=summary_json,
        summary_md=summary_md,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build AC4 pattern discovery visual assets.")
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--anchor-output-dir", type=Path, required=True)
    parser.add_argument("--comparison-output-dir", type=Path, action="append", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model-name", type=str, default="tucker")
    parser.add_argument("--max-stocks", type=int, default=60)
    args = parser.parse_args()
    result = build_pattern_discovery_assets(
        project_root=args.project_root.resolve(),
        anchor_output_dir=args.anchor_output_dir.resolve(),
        comparison_output_dirs=[path.resolve() for path in args.comparison_output_dir],
        output_dir=args.output_dir.resolve(),
        model_name=args.model_name,
        max_stocks=args.max_stocks,
    )
    for path in (
        result.stock_structure_svg,
        result.cluster_industry_svg,
        result.boundary_comparison_svg,
        result.summary_json,
        result.summary_md,
    ):
        print(path.as_posix())


if __name__ == "__main__":
    main()
