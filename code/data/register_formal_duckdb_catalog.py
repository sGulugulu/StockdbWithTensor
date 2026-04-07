from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    import duckdb
except ImportError:
    duckdb = None


UNIVERSE_DATASETS = (
    "all_a_tradable_history",
    "hs300_history",
    "sz50_history",
    "zz500_history",
)
FACTOR_DATASETS = (
    "hs300_factor_panel",
    "sz50_factor_panel",
    "zz500_factor_panel",
)
FINANCIAL_DATASETS = (
    "profit_data",
    "operation_data",
    "growth_data",
    "balance_data",
    "cash_flow_data",
    "dupont_data",
)
REPORT_DATASETS = (
    "performance_express_report",
    "forecast_report",
)
SCHEMAS = (
    "universes",
    "master",
    "factors",
    "financial",
    "reports",
    "full_master",
)


def duckdb_available() -> bool:
    return duckdb is not None


def _require_duckdb():
    if duckdb is None:
        raise ModuleNotFoundError("duckdb is required to register the formal catalog in this environment.")
    return duckdb


def _sql_literal(value: str) -> str:
    return value.replace("'", "''")


def _read_relation_sql(path: Path) -> str:
    resolved = _sql_literal(path.resolve().as_posix())
    if path.suffix.lower() == ".parquet":
        return f"read_parquet('{resolved}')"
    return f"read_csv_auto('{resolved}', HEADER=TRUE)"


def _read_glob_sql(pattern: str, *, parquet: bool) -> str:
    resolved = _sql_literal(pattern)
    if parquet:
        return f"read_parquet('{resolved}')"
    return f"read_csv_auto('{resolved}', HEADER=TRUE)"


def _prefer_single_file(parquet_path: Path, csv_path: Path) -> Path | None:
    if parquet_path.exists():
        return parquet_path
    if csv_path.exists():
        return csv_path
    return None


def _prefer_glob(parquet_dir: Path, csv_dir: Path) -> tuple[str, bool] | None:
    parquet_files = sorted(parquet_dir.glob("*.parquet")) if parquet_dir.exists() else []
    if parquet_files:
        return ((parquet_dir / "*.parquet").resolve().as_posix(), True)
    csv_files = sorted(csv_dir.glob("*.csv")) if csv_dir.exists() else []
    if csv_files:
        return ((csv_dir / "*.csv").resolve().as_posix(), False)
    return None


def _collect_full_master_year_sources(formal_root: Path) -> dict[str, Path]:
    sources: dict[str, Path] = {}
    parquet_root = formal_root / "parquet" / "master"
    csv_root = formal_root / "master"
    for path in sorted(parquet_root.glob("full_master_*.parquet")):
        match = re.fullmatch(r"full_master_(\d{4})\.parquet", path.name)
        if match:
            sources[match.group(1)] = path
    for path in sorted(csv_root.glob("full_master_*.csv")):
        match = re.fullmatch(r"full_master_(\d{4})\.csv", path.name)
        if match and match.group(1) not in sources:
            sources[match.group(1)] = path
    return sources


def _baostock_code_to_normalized_expr(column_name: str) -> str:
    return (
        "CASE "
        f"WHEN {column_name} IS NULL OR trim(CAST({column_name} AS VARCHAR)) = '' THEN NULL "
        f"WHEN lower(substr(CAST({column_name} AS VARCHAR), 1, 3)) IN ('sh.', 'sz.', 'bj.') "
        f"THEN upper(substr(CAST({column_name} AS VARCHAR), 4) || '.' || substr(CAST({column_name} AS VARCHAR), 1, 2)) "
        f"ELSE upper(CAST({column_name} AS VARCHAR)) "
        "END"
    )


def _coverage_union_sql(entries: list[tuple[str, str, str]]) -> str:
    return "\nUNION ALL\n".join(
        [
            (
                "SELECT "
                f"'{_sql_literal(dataset_name)}' AS dataset_name, "
                f"'{_sql_literal(group_name)}' AS dataset_group, "
                "COUNT(*) AS row_count, "
                f"COUNT(DISTINCT {distinct_column}) AS stock_count, "
                "MIN(COALESCE(TRY_CAST(trade_date AS DATE), TRY_CAST(date AS DATE), TRY_CAST(start_date AS DATE), "
                "TRY_CAST(pubDate AS DATE), TRY_CAST(profitForcastExpPubDate AS DATE))) AS min_date, "
                "MAX(COALESCE(TRY_CAST(trade_date AS DATE), TRY_CAST(date AS DATE), TRY_CAST(end_date AS DATE), "
                "TRY_CAST(pubDate AS DATE), TRY_CAST(profitForcastExpPubDate AS DATE))) AS max_date "
                f"FROM {relation_name}"
            )
            for dataset_name, group_name, relation_name in entries
        ]
    )


def register_formal_duckdb_catalog(
    *,
    formal_root: Path,
    catalog_path: Path | None = None,
) -> dict[str, object]:
    duckdb_module = _require_duckdb()
    resolved_formal_root = formal_root.resolve()
    resolved_catalog_path = (catalog_path or (resolved_formal_root / "catalog.duckdb")).resolve()
    resolved_catalog_path.parent.mkdir(parents=True, exist_ok=True)

    registered_objects: list[str] = []
    source_bindings: dict[str, str] = {}

    connection = duckdb_module.connect(str(resolved_catalog_path))
    try:
        for schema_name in SCHEMAS:
            connection.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")

        universe_views: list[str] = []
        for dataset_name in UNIVERSE_DATASETS:
            source_path = _prefer_single_file(
                resolved_formal_root / "parquet" / "universes" / f"{dataset_name}.parquet",
                resolved_formal_root / "universes" / f"{dataset_name}.csv",
            )
            if source_path is None:
                continue
            object_name = f"universes.{dataset_name}"
            connection.execute(f"CREATE OR REPLACE VIEW {object_name} AS SELECT * FROM {_read_relation_sql(source_path)}")
            registered_objects.append(object_name)
            source_bindings[object_name] = source_path.resolve().as_posix()
            universe_views.append(object_name)

        factor_views: list[tuple[str, str]] = []
        for dataset_name in FACTOR_DATASETS:
            source_path = _prefer_single_file(
                resolved_formal_root / "parquet" / "factors" / f"{dataset_name}.parquet",
                resolved_formal_root / "factors" / f"{dataset_name}.csv",
            )
            if source_path is None:
                continue
            object_name = f"factors.{dataset_name}"
            connection.execute(f"CREATE OR REPLACE VIEW {object_name} AS SELECT * FROM {_read_relation_sql(source_path)}")
            registered_objects.append(object_name)
            source_bindings[object_name] = source_path.resolve().as_posix()
            factor_views.append((dataset_name, object_name))

        shared_master_source = _prefer_single_file(
            resolved_formal_root / "parquet" / "master" / "shared_kline_panel.parquet",
            resolved_formal_root / "master" / "shared_kline_panel.csv",
        )
        if shared_master_source is not None:
            connection.execute(
                f"CREATE OR REPLACE VIEW master.shared_kline_panel AS "
                f"SELECT * FROM {_read_relation_sql(shared_master_source)}"
            )
            connection.execute(
                "CREATE OR REPLACE VIEW master.shared_kline_panel_normalized AS "
                "SELECT "
                "CAST(date AS DATE) AS trade_date, "
                f"{_baostock_code_to_normalized_expr('code')} AS stock_code, "
                "open, high, low, close, preclose, volume, amount, adjustflag, turn, tradestatus, pctChg, "
                "peTTM, pbMRQ, psTTM, pcfNcfTTM, isST "
                "FROM master.shared_kline_panel"
            )
            registered_objects.extend(
                [
                    "master.shared_kline_panel",
                    "master.shared_kline_panel_normalized",
                ]
            )
            source_bindings["master.shared_kline_panel"] = shared_master_source.resolve().as_posix()
            source_bindings["master.shared_kline_panel_normalized"] = "master.shared_kline_panel"

        full_master_year_views: list[tuple[str, str]] = []
        for year, source_path in sorted(_collect_full_master_year_sources(resolved_formal_root).items()):
            object_name = f"master.full_master_{year}"
            connection.execute(f"CREATE OR REPLACE VIEW {object_name} AS SELECT * FROM {_read_relation_sql(source_path)}")
            registered_objects.append(object_name)
            source_bindings[object_name] = source_path.resolve().as_posix()
            full_master_year_views.append((year, object_name))

        if full_master_year_views:
            union_sql = "\nUNION ALL\n".join(
                [
                    (
                        "SELECT "
                        "CAST(date AS DATE) AS trade_date, "
                        f"{_baostock_code_to_normalized_expr('code')} AS stock_code, "
                        "open, high, low, close, preclose, volume, amount, adjustflag, pctChg AS pct_chg, "
                        "turn, tradestatus AS trade_status, isST AS is_st, peTTM AS pe_ttm, pbMRQ AS pb_mrq, "
                        "psTTM AS ps_ttm, pcfNcfTTM AS pcf_ncf_ttm, "
                        f"'{_sql_literal(year)}' AS source_year "
                        f"FROM {object_name}"
                    )
                    for year, object_name in full_master_year_views
                ]
            )
            connection.execute(f"CREATE OR REPLACE VIEW full_master.daily AS {union_sql}")
            connection.execute(
                "CREATE OR REPLACE VIEW full_master.coverage_summary AS "
                "SELECT "
                "COUNT(*) AS row_count, "
                "COUNT(DISTINCT stock_code) AS stock_count, "
                "MIN(trade_date) AS min_trade_date, "
                "MAX(trade_date) AS max_trade_date "
                "FROM full_master.daily"
            )
            registered_objects.extend(["full_master.daily", "full_master.coverage_summary"])
            source_bindings["full_master.daily"] = ", ".join(name for _, name in full_master_year_views)
            source_bindings["full_master.coverage_summary"] = "full_master.daily"

        if full_master_year_views:
            connection.execute(
                "CREATE OR REPLACE VIEW master.vw_trade_dates AS "
                "SELECT DISTINCT trade_date FROM full_master.daily"
            )
            registered_objects.append("master.vw_trade_dates")
            source_bindings["master.vw_trade_dates"] = "full_master.daily"
        elif shared_master_source is not None:
            connection.execute(
                "CREATE OR REPLACE VIEW master.vw_trade_dates AS "
                "SELECT DISTINCT trade_date FROM master.shared_kline_panel_normalized"
            )
            registered_objects.append("master.vw_trade_dates")
            source_bindings["master.vw_trade_dates"] = "master.shared_kline_panel_normalized"

        if shared_master_source is not None:
            connection.execute(
                "CREATE OR REPLACE VIEW master.vw_shared_master_coverage AS "
                "SELECT "
                "COUNT(*) AS row_count, "
                "COUNT(DISTINCT stock_code) AS stock_count, "
                "MIN(trade_date) AS min_trade_date, "
                "MAX(trade_date) AS max_trade_date "
                "FROM master.shared_kline_panel_normalized"
            )
            registered_objects.append("master.vw_shared_master_coverage")
            source_bindings["master.vw_shared_master_coverage"] = "master.shared_kline_panel_normalized"

        if "master.vw_trade_dates" in registered_objects:
            universe_view_specs = {
                "all_a_tradable_history": "universes.vw_all_a_tradable_on_date",
                "hs300_history": "universes.vw_hs300_on_date",
                "sz50_history": "universes.vw_sz50_on_date",
                "zz500_history": "universes.vw_zz500_on_date",
            }
            for dataset_name, view_name in universe_view_specs.items():
                relation_name = f"universes.{dataset_name}"
                if relation_name not in universe_views:
                    continue
                connection.execute(
                    f"CREATE OR REPLACE VIEW {view_name} AS "
                    "SELECT "
                    "d.trade_date, "
                    "u.market_id, "
                    "u.universe_id, "
                    "u.stock_code, "
                    "CAST(u.start_date AS DATE) AS start_date, "
                    "CAST(u.end_date AS DATE) AS end_date "
                    "FROM master.vw_trade_dates AS d "
                    f"JOIN {relation_name} AS u "
                    "ON d.trade_date BETWEEN CAST(u.start_date AS DATE) AND CAST(u.end_date AS DATE)"
                )
                registered_objects.append(view_name)
                source_bindings[view_name] = f"master.vw_trade_dates + {relation_name}"

        if factor_views:
            coverage_sql = "\nUNION ALL\n".join(
                [
                    (
                        "SELECT "
                        f"'{_sql_literal(dataset_name.replace('_factor_panel', '').upper())}' AS universe_id, "
                        "COUNT(*) AS row_count, "
                        "COUNT(DISTINCT stock_code) AS stock_count, "
                        "MIN(CAST(trade_date AS DATE)) AS min_trade_date, "
                        "MAX(CAST(trade_date AS DATE)) AS max_trade_date "
                        f"FROM {relation_name}"
                    )
                    for dataset_name, relation_name in factor_views
                ]
            )
            connection.execute(f"CREATE OR REPLACE VIEW factors.vw_factor_panel_coverage AS {coverage_sql}")
            registered_objects.append("factors.vw_factor_panel_coverage")
            source_bindings["factors.vw_factor_panel_coverage"] = ", ".join(name for _, name in factor_views)

        financial_views: list[tuple[str, str]] = []
        for dataset_name in FINANCIAL_DATASETS:
            preferred_source = _prefer_glob(
                resolved_formal_root / "parquet" / "financial" / dataset_name,
                resolved_formal_root / "baostock" / "financial" / dataset_name,
            )
            if preferred_source is None:
                preferred_source = _prefer_glob(
                    resolved_formal_root / "parquet" / "financial" / dataset_name,
                    resolved_formal_root / "financial" / dataset_name,
                )
            if preferred_source is None:
                continue
            pattern, parquet = preferred_source
            object_name = f"financial.{dataset_name}"
            connection.execute(
                f"CREATE OR REPLACE VIEW {object_name} AS SELECT * FROM {_read_glob_sql(pattern, parquet=parquet)}"
            )
            registered_objects.append(object_name)
            source_bindings[object_name] = pattern
            financial_views.append((dataset_name, object_name))

        if financial_views:
            coverage_sql = "\nUNION ALL\n".join(
                [
                    (
                        "SELECT "
                        f"'{_sql_literal(dataset_name)}' AS dataset_name, "
                        "COUNT(*) AS row_count, "
                        "COUNT(DISTINCT code) AS stock_count, "
                        "MIN(TRY_CAST(query_year AS INTEGER)) AS min_query_year, "
                        "MAX(TRY_CAST(query_year AS INTEGER)) AS max_query_year "
                        f"FROM {relation_name}"
                    )
                    for dataset_name, relation_name in financial_views
                ]
            )
            connection.execute(f"CREATE OR REPLACE VIEW financial.vw_financial_dataset_coverage AS {coverage_sql}")
            registered_objects.append("financial.vw_financial_dataset_coverage")
            source_bindings["financial.vw_financial_dataset_coverage"] = ", ".join(
                name for _, name in financial_views
            )

        report_views: list[tuple[str, str]] = []
        for dataset_name in REPORT_DATASETS:
            preferred_source = _prefer_glob(
                resolved_formal_root / "parquet" / "reports" / dataset_name,
                resolved_formal_root / "baostock" / "reports" / dataset_name,
            )
            if preferred_source is None:
                preferred_source = _prefer_glob(
                    resolved_formal_root / "parquet" / "reports" / dataset_name,
                    resolved_formal_root / "reports" / dataset_name,
                )
            if preferred_source is None:
                continue
            pattern, parquet = preferred_source
            object_name = f"reports.{dataset_name}"
            connection.execute(
                f"CREATE OR REPLACE VIEW {object_name} AS SELECT * FROM {_read_glob_sql(pattern, parquet=parquet)}"
            )
            registered_objects.append(object_name)
            source_bindings[object_name] = pattern
            report_views.append((dataset_name, object_name))

        if report_views:
            coverage_sql = "\nUNION ALL\n".join(
                [
                    (
                        "SELECT "
                        f"'{_sql_literal(dataset_name)}' AS dataset_name, "
                        "COUNT(*) AS row_count, "
                        "COUNT(DISTINCT code) AS stock_count, "
                        "MIN(TRY_CAST(query_year AS INTEGER)) AS min_query_year, "
                        "MAX(TRY_CAST(query_year AS INTEGER)) AS max_query_year "
                        f"FROM {relation_name}"
                    )
                    for dataset_name, relation_name in report_views
                ]
            )
            connection.execute(f"CREATE OR REPLACE VIEW reports.vw_report_dataset_coverage AS {coverage_sql}")
            registered_objects.append("reports.vw_report_dataset_coverage")
            source_bindings["reports.vw_report_dataset_coverage"] = ", ".join(name for _, name in report_views)
    finally:
        connection.close()

    return {
        "catalog_path": resolved_catalog_path.as_posix(),
        "formal_root": resolved_formal_root.as_posix(),
        "registered_objects": sorted(set(registered_objects)),
        "source_bindings": source_bindings,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Register formal CSV/Parquet datasets into a local DuckDB catalog.")
    parser.add_argument("--formal-root", type=Path, default=Path("code/data/formal"))
    parser.add_argument("--catalog-path", type=Path, default=None)
    args = parser.parse_args()
    summary = register_formal_duckdb_catalog(
        formal_root=args.formal_root,
        catalog_path=args.catalog_path,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
