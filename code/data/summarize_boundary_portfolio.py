from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class BoundaryPortfolioSummaryResult:
    summary_json: Path
    summary_md: Path


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _row_by_model(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(row["model"]): row for row in rows}


def _top_exposures(output_dir: Path, model_name: str, exposure_type: str, limit: int) -> list[dict[str, Any]]:
    path = output_dir / f"exposure_{model_name}.json"
    if not path.exists():
        return []
    rows = [
        row
        for row in _load_json(path)
        if str(row.get("exposure_type", "")) == exposure_type
    ]
    rows.sort(key=lambda row: float(row.get("weight", 0.0)), reverse=True)
    return rows[:limit]


def _best_model(rows: list[dict[str, Any]], metric_key: str, *, higher_is_better: bool = True) -> str:
    if not rows:
        return ""
    if higher_is_better:
        key = lambda row: float(row.get(metric_key, 0.0))
    else:
        key = lambda row: -float(row.get(metric_key, 0.0))
    return str(max(rows, key=key).get("model", ""))


def _series_final_value(output_dir: Path, model_name: str, prefix: str, key: str) -> float:
    path = output_dir / f"{prefix}_{model_name}.json"
    if not path.exists():
        return 0.0
    rows = _load_json(path)
    if not rows:
        return 0.0
    return float(rows[-1].get(key, 0.0))


def _series_mean_value(output_dir: Path, model_name: str, prefix: str, key: str) -> float:
    path = output_dir / f"{prefix}_{model_name}.json"
    if not path.exists():
        return 0.0
    rows = _load_json(path)
    values = [float(row.get(key, 0.0)) for row in rows]
    return sum(values) / len(values) if values else 0.0


def _series_min_value(output_dir: Path, model_name: str, prefix: str, key: str) -> float:
    path = output_dir / f"{prefix}_{model_name}.json"
    if not path.exists():
        return 0.0
    rows = _load_json(path)
    values = [float(row.get(key, 0.0)) for row in rows]
    return min(values) if values else 0.0


def _quantile_spread(output_dir: Path, model_name: str) -> float:
    path = output_dir / f"quantile_returns_{model_name}.json"
    if not path.exists():
        return 0.0
    rows = _load_json(path)
    if not rows:
        return 0.0
    final_nav_by_quantile: dict[int, float] = {}
    for row in rows:
        final_nav_by_quantile[int(row.get("quantile", 0))] = float(row.get("cumulative_nav", 1.0))
    if not final_nav_by_quantile:
        return 0.0
    low_quantile = min(final_nav_by_quantile)
    high_quantile = max(final_nav_by_quantile)
    return final_nav_by_quantile[low_quantile] - final_nav_by_quantile[high_quantile]


def _summarize_run(output_dir: Path, *, exposure_limit: int) -> dict[str, Any]:
    manifest = _load_json(output_dir / "run_manifest.json")
    metrics_rows = _load_json(output_dir / "metrics.json")
    portfolio_rows = _load_json(output_dir / "portfolio_metrics.json")
    metrics_by_model = _row_by_model(metrics_rows)
    portfolio_by_model = _row_by_model(portfolio_rows)
    universe_id = str(manifest.get("universe_id") or manifest.get("market", {}).get("universe_id") or output_dir.name)

    model_rows: list[dict[str, Any]] = []
    for model_name in sorted(metrics_by_model):
        metric = metrics_by_model[model_name]
        portfolio = portfolio_by_model.get(model_name, {})
        model_rows.append(
            {
                "model": model_name,
                "rank_ic_mean": float(metric.get("rank_ic_mean", 0.0)),
                "rolling_stability": float(metric.get("rolling_stability", 0.0)),
                "cumulative_return": float(portfolio.get("cumulative_return", 0.0)),
                "annualized_volatility": float(portfolio.get("annualized_volatility", 0.0)),
                "sharpe_ratio": float(portfolio.get("sharpe_ratio", 0.0)),
                "max_drawdown": float(portfolio.get("max_drawdown", 0.0)),
                "average_turnover": float(portfolio.get("average_turnover", 0.0)),
                "quantile_top_bottom_nav_spread": _quantile_spread(output_dir, model_name),
                "long_short_cumulative_nav": _series_final_value(
                    output_dir, model_name, "long_short", "cumulative_nav"
                ),
                "long_short_max_drawdown": _series_min_value(output_dir, model_name, "long_short", "drawdown"),
                "cost_adjusted_cumulative_nav": _series_final_value(
                    output_dir, model_name, "cost_adjusted", "cumulative_nav"
                ),
                "average_transaction_cost": _series_mean_value(
                    output_dir, model_name, "cost_adjusted", "transaction_cost"
                ),
                "excess_cumulative_nav": _series_final_value(
                    output_dir, model_name, "excess_returns", "cumulative_nav"
                ),
                "excess_max_drawdown": _series_min_value(output_dir, model_name, "excess_returns", "drawdown"),
                "top_industry_exposures": _top_exposures(output_dir, model_name, "industry", exposure_limit),
                "top_style_exposures": _top_exposures(output_dir, model_name, "style", exposure_limit),
            }
        )

    return {
        "run_name": output_dir.name,
        "universe_id": universe_id,
        "actual_start_date": manifest.get("actual_start_date"),
        "actual_end_date": manifest.get("actual_end_date"),
        "candidate_pool_size": manifest.get("candidate_pool_size"),
        "selection_top_n": manifest.get("selection_top_n"),
        "best_rank_ic_model": _best_model(model_rows, "rank_ic_mean"),
        "best_return_model": _best_model(model_rows, "cumulative_return"),
        "best_sharpe_model": _best_model(model_rows, "sharpe_ratio"),
        "models": model_rows,
    }


def _format_percent(value: float) -> str:
    return f"{value * 100:.2f}%"


def _format_float(value: float) -> str:
    return f"{value:.4f}"


def _exposure_label(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "-"
    return "；".join(
        f"{row.get('name', '')} {_format_percent(float(row.get('weight', 0.0)))}"
        for row in rows
    )


def _write_markdown(path: Path, summaries: list[dict[str, Any]]) -> None:
    lines = [
        "# 跨样本边界组合与暴露汇总",
        "",
        "本文档由 `code/data/summarize_boundary_portfolio.py` 生成，用于把不同 formal run 的排序指标、组合表现和行业/风格暴露放到同一张可复核表中。",
        "",
        "## 样本池概览",
        "",
        "| 运行名 | 样本池 | 起止日期 | 候选池 | Top-N | Rank IC 最优 | 收益最优 | Sharpe 最优 |",
        "|---|---|---:|---:|---:|---|---|---|",
    ]
    for summary in summaries:
        lines.append(
            (
                "| {run_name} | {universe} | {start} 至 {end} | {pool} | {top_n} | "
                "{rank_model} | {return_model} | {sharpe_model} |"
            ).format(
                run_name=summary["run_name"],
                universe=summary["universe_id"],
                start=summary.get("actual_start_date") or "-",
                end=summary.get("actual_end_date") or "-",
                pool=summary.get("candidate_pool_size") or "-",
                top_n=summary.get("selection_top_n") or "-",
                rank_model=summary["best_rank_ic_model"],
                return_model=summary["best_return_model"],
                sharpe_model=summary["best_sharpe_model"],
            )
        )

    lines.extend(
        [
            "",
            "## 模型明细",
            "",
            (
                "| 运行名 | 样本池 | 模型 | Rank IC | 稳定性 | Top-N收益 | 分组价差 | 多空NAV | "
                "成本后NAV | 平均成本 | 超额NAV | 年化波动 | Sharpe | 最大回撤 | 平均换手 | 主要行业暴露 | 主要风格暴露 |"
            ),
            "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
        ]
    )
    for summary in summaries:
        for row in summary["models"]:
            lines.append(
                (
                    "| {run_name} | {universe} | {model} | {rank_ic} | {stability} | {ret} | {spread} | "
                    "{long_short} | {cost_nav} | {avg_cost} | {excess_nav} | {vol} | {sharpe} | "
                    "{drawdown} | {turnover} | {industry} | {style} |"
                ).format(
                    run_name=summary["run_name"],
                    universe=summary["universe_id"],
                    model=str(row["model"]).upper(),
                    rank_ic=_format_float(float(row["rank_ic_mean"])),
                    stability=_format_float(float(row["rolling_stability"])),
                    ret=_format_percent(float(row["cumulative_return"])),
                    spread=_format_float(float(row["quantile_top_bottom_nav_spread"])),
                    long_short=_format_float(float(row["long_short_cumulative_nav"])),
                    cost_nav=_format_float(float(row["cost_adjusted_cumulative_nav"])),
                    avg_cost=_format_percent(float(row["average_transaction_cost"])),
                    excess_nav=_format_float(float(row["excess_cumulative_nav"])),
                    vol=_format_percent(float(row["annualized_volatility"])),
                    sharpe=_format_float(float(row["sharpe_ratio"])),
                    drawdown=_format_percent(float(row["max_drawdown"])),
                    turnover=_format_percent(float(row["average_turnover"])),
                    industry=_exposure_label(row["top_industry_exposures"]),
                    style=_exposure_label(row["top_style_exposures"]),
                )
            )
    path.write_text("\n".join(lines), encoding="utf-8")


def summarize_boundary_portfolio(
    *,
    output_dirs: list[Path],
    report_dir: Path,
    exposure_limit: int = 3,
) -> BoundaryPortfolioSummaryResult:
    report_dir.mkdir(parents=True, exist_ok=True)
    summaries = [
        _summarize_run(output_dir, exposure_limit=exposure_limit)
        for output_dir in output_dirs
        if (output_dir / "metrics.json").exists()
        and (output_dir / "portfolio_metrics.json").exists()
        and (output_dir / "run_manifest.json").exists()
    ]
    summaries.sort(key=lambda row: str(row["universe_id"]))
    summary_json = report_dir / "boundary_portfolio_summary.json"
    summary_md = report_dir / "README.md"
    summary_json.write_text(json.dumps(summaries, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(summary_md, summaries)
    return BoundaryPortfolioSummaryResult(summary_json=summary_json, summary_md=summary_md)


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize portfolio and exposure results across formal boundaries.")
    parser.add_argument("--output-dir", type=Path, action="append", required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    parser.add_argument("--exposure-limit", type=int, default=3)
    args = parser.parse_args()
    result = summarize_boundary_portfolio(
        output_dirs=[path.resolve() for path in args.output_dir],
        report_dir=args.report_dir.resolve(),
        exposure_limit=args.exposure_limit,
    )
    print(result.summary_json.as_posix())
    print(result.summary_md.as_posix())


if __name__ == "__main__":
    main()
