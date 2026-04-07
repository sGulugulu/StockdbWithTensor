from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

from data.register_formal_duckdb_catalog import register_formal_duckdb_catalog

try:
    import duckdb
except ImportError:
    duckdb = None


UNIVERSE_VIEW_BY_ID: dict[str, str] = {
    "ALL_A_TRADABLE": "universes.vw_all_a_tradable_on_date",
    "HS300": "universes.vw_hs300_on_date",
    "SZ50": "universes.vw_sz50_on_date",
    "ZZ500": "universes.vw_zz500_on_date",
}


def _require_duckdb():
    if duckdb is None:
        raise ModuleNotFoundError("duckdb is required to serve formal data routes.")
    return duckdb


def _normalize_universe_id(universe_id: str) -> str:
    cleaned = universe_id.strip().upper()
    aliases = {
        "ALL_A": "ALL_A_TRADABLE",
        "ALL_A_TRADABLE_HISTORY": "ALL_A_TRADABLE",
    }
    return aliases.get(cleaned, cleaned)


def ensure_formal_catalog(formal_root: Path, catalog_path: Path | None = None) -> Path:
    resolved_formal_root = formal_root.resolve()
    resolved_catalog_path = (catalog_path or (resolved_formal_root / "catalog.duckdb")).resolve()
    if not resolved_catalog_path.exists():
        register_formal_duckdb_catalog(
            formal_root=resolved_formal_root,
            catalog_path=resolved_catalog_path,
        )
    return resolved_catalog_path


def _serialize_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return value


def _fetch_all(connection: Any, sql: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    cursor = connection.execute(sql, params)
    columns = [item[0] for item in cursor.description]
    return [
        {column: _serialize_value(value) for column, value in zip(columns, row, strict=False)}
        for row in cursor.fetchall()
    ]


def get_formal_coverage(*, formal_root: Path, catalog_path: Path | None = None) -> dict[str, Any]:
    duckdb_module = _require_duckdb()
    resolved_catalog_path = ensure_formal_catalog(formal_root, catalog_path)
    connection = duckdb_module.connect(str(resolved_catalog_path), read_only=True)
    try:
        master_rows = _fetch_all(
            connection,
            "SELECT row_count, stock_count, min_trade_date, max_trade_date "
            "FROM master.vw_shared_master_coverage",
        )
        full_master_rows = _fetch_all(
            connection,
            "SELECT row_count, stock_count, min_trade_date, max_trade_date "
            "FROM full_master.coverage_summary",
        )
        factor_rows = _fetch_all(
            connection,
            "SELECT universe_id, row_count, stock_count, min_trade_date, max_trade_date "
            "FROM factors.vw_factor_panel_coverage ORDER BY universe_id",
        )
        financial_rows = _fetch_all(
            connection,
            "SELECT dataset_name, row_count, stock_count, min_query_year, max_query_year "
            "FROM financial.vw_financial_dataset_coverage ORDER BY dataset_name",
        )
        report_rows = _fetch_all(
            connection,
            "SELECT dataset_name, row_count, stock_count, min_query_year, max_query_year "
            "FROM reports.vw_report_dataset_coverage ORDER BY dataset_name",
        )
    finally:
        connection.close()

    return {
        "catalog_path": resolved_catalog_path.as_posix(),
        "master": master_rows[0] if master_rows else None,
        "full_master": full_master_rows[0] if full_master_rows else None,
        "factors": factor_rows,
        "financial": financial_rows,
        "reports": report_rows,
    }


def get_universe_members_for_date(
    *,
    formal_root: Path,
    universe_id: str,
    trade_date: str,
    catalog_path: Path | None = None,
) -> list[dict[str, Any]]:
    normalized_universe_id = _normalize_universe_id(universe_id)
    view_name = UNIVERSE_VIEW_BY_ID.get(normalized_universe_id)
    if view_name is None:
        raise KeyError(universe_id)

    duckdb_module = _require_duckdb()
    resolved_catalog_path = ensure_formal_catalog(formal_root, catalog_path)
    connection = duckdb_module.connect(str(resolved_catalog_path), read_only=True)
    try:
        return _fetch_all(
            connection,
            f"SELECT trade_date, market_id, universe_id, stock_code, start_date, end_date "
            f"FROM {view_name} WHERE trade_date = CAST(? AS DATE) ORDER BY stock_code",
            (trade_date,),
        )
    finally:
        connection.close()
