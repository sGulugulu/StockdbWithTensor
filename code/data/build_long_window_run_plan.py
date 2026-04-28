from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))

from data.year_windows import iter_year_date_ranges


@dataclass(frozen=True, slots=True)
class LongWindowRunPlanResult:
    plan_json: Path
    plan_md: Path


def _default_output_name(config_path: Path, year: int) -> str:
    stem = config_path.stem
    return f"{stem}_{year}_long_window_run"


def _replace_yaml_scalar(lines: list[str], key: str, value: str) -> list[str]:
    replaced = False
    result: list[str] = []
    for line in lines:
        stripped = line.lstrip()
        indent = line[: len(line) - len(stripped)]
        if stripped.startswith(f"{key}:") and not replaced:
            result.append(f"{indent}{key}: {value}\n")
            replaced = True
            continue
        result.append(line)
    if not replaced:
        raise ValueError(f"missing YAML key: {key}")
    return result


def _quote_yaml_scalar(value: str) -> str:
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def _display_cli_path(path: Path, *, cwd: Path) -> str:
    resolved = path.resolve()
    try:
        return Path(os.path.relpath(resolved, start=cwd)).as_posix()
    except ValueError:
        return resolved.as_posix()


def _relocate_config_path(source_config: Path, output_config: Path, value: str) -> str:
    raw = value.strip().strip('"').strip("'")
    if not raw:
        return raw
    candidate = Path(raw)
    if candidate.is_absolute():
        target = candidate
    else:
        target = (source_config.parent / candidate).resolve()
    try:
        return Path(os.path.relpath(target, start=output_config.parent)).as_posix()
    except ValueError:
        return target.as_posix()


def _long_window_factor_panel_path(source_config: Path, current_value: str) -> str | None:
    raw = current_value.strip().strip('"').strip("'")
    if not raw:
        return None
    target = (source_config.parent / Path(raw)).resolve()
    if target.suffix.lower() != ".csv":
        return None
    if target.parent.name != "factors":
        return None
    if not (target.stem.endswith("_factor_panel") or target.stem.endswith("_factor_panel_extended")):
        return None
    long_window_target = target.parent / "long_window" / f"{target.stem}_long_window.csv"
    # 计划文件必须只引用已生成的数据，避免把缺失面板延迟到实验运行阶段才失败。
    if not long_window_target.exists():
        raise FileNotFoundError(f"missing long-window factor panel: {long_window_target}")
    return long_window_target.as_posix()


def _write_config_variant(
    *,
    source_config: Path,
    output_config: Path,
    output_name: str,
    start_date: str,
    end_date: str,
) -> None:
    lines = source_config.read_text(encoding="utf-8").splitlines(keepends=True)
    lines = _replace_yaml_scalar(lines, "start_date", start_date)
    lines = _replace_yaml_scalar(lines, "end_date", end_date)
    lines = _replace_yaml_scalar(lines, "experiment_name", output_name)
    for key in ("universe_path", "path", "benchmark_path", "root_dir"):
        for line in lines:
            stripped = line.lstrip()
            if stripped.startswith(f"{key}:"):
                current_value = stripped.split(":", 1)[1]
                override_value = None
                if key == "path":
                    override_value = _long_window_factor_panel_path(source_config, current_value)
                relocated_source = override_value if override_value is not None else current_value
                resolved_value = _quote_yaml_scalar(_relocate_config_path(source_config, output_config, relocated_source))
                lines = _replace_yaml_scalar(lines, key, resolved_value)
                break
    output_config.parent.mkdir(parents=True, exist_ok=True)
    output_config.write_text("".join(lines), encoding="utf-8")


def _build_command(config_path: Path | str) -> str:
    path_text = config_path.as_posix() if isinstance(config_path, Path) else str(config_path)
    escaped = path_text.replace('"', '\\"')
    return f'python3 code/main.py --config "{escaped}"'


def build_long_window_run_plan(
    *,
    config_paths: list[Path],
    start_date: str,
    end_date: str,
    report_dir: Path,
) -> LongWindowRunPlanResult:
    report_dir.mkdir(parents=True, exist_ok=True)
    cwd = Path.cwd().resolve()
    windows = iter_year_date_ranges(start_date, end_date)
    rows: list[dict[str, str | int]] = []
    config_dir = report_dir / "configs"
    for config_path in config_paths:
        for window_start, window_end, year in windows:
            output_name = _default_output_name(config_path, year)
            output_config = config_dir / f"{output_name}.yaml"
            _write_config_variant(
                source_config=config_path,
                output_config=output_config,
                output_name=output_name,
                start_date=window_start,
                end_date=window_end,
            )
            rows.append(
                {
                    "config": _display_cli_path(config_path, cwd=cwd),
                    "config_variant": _display_cli_path(output_config, cwd=cwd),
                    "year": year,
                    "start_date": window_start,
                    "end_date": window_end,
                    "output_name": output_name,
                    "command": _build_command(Path(_display_cli_path(output_config, cwd=cwd))),
                }
            )

    plan_json = report_dir / "long_window_run_plan.json"
    plan_md = report_dir / "README.md"
    plan_json.write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    _write_markdown(plan_md, rows)
    return LongWindowRunPlanResult(plan_json=plan_json, plan_md=plan_md)


def _write_markdown(path: Path, rows: list[dict[str, str | int]]) -> None:
    lines = [
        "# 长窗口稳健性实验入口",
        "",
        "本文档由 `code/data/build_long_window_run_plan.py` 生成，用于把当前短窗口 formal 配置扩展为按年度复跑的命令清单。",
        "",
        "| 原配置 | 派生配置 | 年份 | 窗口 | 输出目录 | 命令 |",
        "|--------|----------|-----:|------|----------|------|",
    ]
    for row in rows:
        lines.append(
            "| {config} | {variant} | {year} | {start} 至 {end} | {output} | `{command}` |".format(
                config=row["config"],
                variant=row["config_variant"],
                year=row["year"],
                start=row["start_date"],
                end=row["end_date"],
                output=row["output_name"],
                command=row["command"],
            )
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a reproducible long-window formal run plan.")
    parser.add_argument("--config", type=Path, action="append", required=True)
    parser.add_argument("--start-date", type=str, required=True)
    parser.add_argument("--end-date", type=str, required=True)
    parser.add_argument("--report-dir", type=Path, required=True)
    args = parser.parse_args()

    result = build_long_window_run_plan(
        config_paths=[path.resolve() for path in args.config],
        start_date=args.start_date,
        end_date=args.end_date,
        report_dir=args.report_dir.resolve(),
    )
    print(result.plan_json.as_posix())
    print(result.plan_md.as_posix())


if __name__ == "__main__":
    main()
