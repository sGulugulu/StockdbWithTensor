# Database Guidelines

> Database patterns and conventions for this project.

---

## Overview

This project does not use a traditional OLTP database as the primary research store.
The database layer is a local analytical stack:

1. canonical `CSV` outputs under `code/data/formal/`
2. mirrored `Parquet` outputs under `code/data/formal/parquet/`
3. a local `DuckDB` catalog, planned at `code/data/formal/catalog.duckdb`
4. FastAPI handlers reading stable files or DuckDB views for web queries

The formal thesis plan is explicitly `Parquet + DuckDB`, not `MySQL` or
`PostgreSQL`, because the workload is single-machine research, batch analytics,
coverage checks, and web read APIs over large historical files.

Current source-of-truth examples:

- `README.md`: formal data architecture and DuckDB direction
- `plan.md`: target schemas, object names, and stage ordering
- `code/data/formal/README.md`: structured formal data layout
- `code/data/formal/master/FULL_MASTER_CONTRACT.md`: shared master field contract
- `web/backend/app.py`: current web layer reads stable output artifacts

Use the following mental model:

- `CSV` is the canonical landing format for inspection and validation
- `Parquet` is the preferred compute/query format
- `DuckDB` is the query catalog and semantic layer
- the web backend should read normalized DuckDB views or stable output files,
  not ad-hoc raw CSV scans

---

## Data Layers

### Layer 1: Raw / Canonical Files

Keep formal structured files under `code/data/formal/`:

- `universes/`
- `master/`
- `factors/`
- `financial/`
- `reports/`
- `baostock/`

Examples already present in the repo:

- `code/data/formal/universes/hs300_history.csv`
- `code/data/formal/master/shared_kline_panel.csv`
- `code/data/formal/master/full_master_2026.csv`
- `code/data/formal/factors/hs300_factor_panel.csv`
- `code/data/formal/baostock/financial/profit_data/2025.csv`
- `code/data/formal/baostock/reports/forecast_report/2025.csv`

### Layer 2: Columnar Mirrors

After validation, convert formal CSV files into matching Parquet files under
`code/data/formal/parquet/`.

Conventions:

- keep the same dataset boundary as the CSV source
- preserve date range and field contract
- record parity in manifest or validation logs
- prefer Parquet for training, coverage checks, and DuckDB views

Examples already present:

- `code/data/formal/parquet/universes/hs300_history.parquet`
- `code/data/formal/parquet/master/shared_kline_panel.parquet`
- `code/data/formal/parquet/factors/hs300_factor_panel.parquet`

### Layer 3: DuckDB Catalog

DuckDB is the semantic query layer over the formal files.

Planned catalog location:

- `code/data/formal/catalog.duckdb`

Planned logical schemas from `plan.md`:

- `universes.*`
- `master.*`
- `factors.*`
- `financial.*`
- `reports.*`
- `full_master.*`

The catalog should expose stable object names for research SQL and web services.
Prefer views over physical duplication unless a workload is repeatedly heavy.

---

## Query Patterns

### Preferred Pattern

Query Parquet first, fall back to CSV only when Parquet is not ready.

Good:

- DuckDB view over `read_parquet(...)`
- coverage and summary views in DuckDB
- backend service reading a stable view name

Avoid:

- scanning large CSV files directly in request handlers
- duplicating the full market dataset once per index
- mixing smoke-test files with formal full-data queries

### Canonical Query Boundary

The project has two query paths today:

1. experiment outputs from `code/outputs/<run_id>/`
2. formal data queries from the planned DuckDB catalog

Current web examples:

- `web/backend/app.py` reads `selection_candidates.json`
- `web/backend/app.py` reads `run_manifest.json`
- `web/backend/app.py` resolves formal profiles from fixed YAML files

Planned database-facing APIs should read stable DuckDB objects such as:

- `universes.vw_all_a_tradable_on_date`
- `universes.vw_hs300_on_date`
- `master.vw_shared_master_coverage`
- `factors.vw_factor_panel_coverage`
- `financial.vw_financial_dataset_coverage`

### Batch-First Rule

This repository is batch-oriented.

- build files in pipeline stages
- validate files in tests or offline scripts
- expose read-only query objects to the web layer

Do not treat DuckDB like a high-concurrency transactional write database.
Ingest by rebuilding files or refreshing catalog objects, not by row-at-a-time
API writes.

### Recommended Object Shapes

#### `universes`

Base objects:

- `all_a_tradable_history`
- `hs300_history`
- `sz50_history`
- `zz500_history`

Expected normalized columns:

- `market_id`
- `universe_id`
- `stock_code`
- `start_date`
- `end_date`

Recommended uniqueness:

- `(universe_id, stock_code, start_date)`

#### `master`

Base objects:

- `shared_kline_panel`
- yearly `tdx_full_master_base_<year>`
- yearly `full_master_<year>`

Expected normalized columns for query views:

- `trade_date`
- `stock_code`
- `open`
- `high`
- `low`
- `close`
- `preclose`
- `volume`
- `amount`
- `adjustflag`
- `pct_chg`
- `turn`
- `trade_status`
- `is_st`
- `pe_ttm`
- `pb_mrq`
- `ps_ttm`
- `pcf_ncf_ttm`

Recommended uniqueness:

- `(trade_date, stock_code)`

Note: the raw full-master contract currently uses baostock-style names such as
`date`, `code`, `pctChg`, `tradestatus`, `isST`, `peTTM`, `pbMRQ`, `psTTM`,
and `pcfNcfTTM`. Normalize these in DuckDB views instead of mutating every raw
source file immediately.

#### `factors`

Base objects:

- `hs300_factor_panel`
- `sz50_factor_panel`
- `zz500_factor_panel`

Expected core columns based on current configs:

- `trade_date`
- `stock_code`
- `industry`
- `future_return`
- `value_factor`
- `momentum_factor`
- `quality_factor`
- `volatility_factor`

Recommended uniqueness:

- `(trade_date, stock_code, universe_id)` in normalized views

#### `financial` and `reports`

Keep one dataset per source table, not one giant merged finance table.

Financial datasets:

- `profit_data`
- `operation_data`
- `growth_data`
- `balance_data`
- `cash_flow_data`
- `dupont_data`

Report datasets:

- `performance_express_report`
- `forecast_report`

Use dataset-specific raw columns, but normalize shared access fields in views
where possible:

- `stock_code`
- `report_date`
- `pub_date`
- `stat_date`
- `source_year`
- `source_path`

Because baostock tables are heterogeneous, do not force every raw file into a
single wide finance schema.

---

## Migrations

This project is file-schema-first, not migration-table-first.

### What counts as a migration here

A database migration is one of:

1. changing a CSV/Parquet field contract
2. changing DuckDB object names
3. changing how files are registered into the catalog
4. changing cross-layer payload contracts that depend on database fields

### Migration process

1. update the file contract doc first
2. update build scripts that emit the dataset
3. refresh Parquet mirrors if the CSV contract changed
4. rebuild or refresh DuckDB views
5. update tests that assert config paths, output contracts, or query objects

### What not to do

- do not rely on ad-hoc `ALTER TABLE` history inside DuckDB as the primary
  migration record
- do not rename stable view names casually
- do not change formal profile paths without updating tests and web consumers

For cross-layer changes, check:

- `web/backend/app.py`
- `code/tests/test_backend.py`
- `code/tests/test_formal_config.py`
- `code/data/formal/master/FULL_MASTER_CONTRACT.md`

The durable migration record should be the code, file contracts, manifests, and
docs committed in the repo.

---

## Naming Conventions

### Schemas

Use lowercase snake_case schema names:

- `universes`
- `master`
- `factors`
- `financial`
- `reports`
- `full_master`

### Tables / Views

Use lowercase snake_case.

Examples:

- `hs300_history`
- `shared_kline_panel`
- `full_master_2026`
- `hs300_factor_panel`
- `profit_data`
- `forecast_report`

Coverage or semantic helper views should be prefixed with `vw_`:

- `vw_all_a_tradable_on_date`
- `vw_hs300_on_date`
- `vw_shared_master_coverage`
- `vw_factor_panel_coverage`
- `vw_financial_dataset_coverage`

### Columns

For normalized DuckDB objects, prefer lowercase snake_case:

- `trade_date`
- `stock_code`
- `market_id`
- `universe_id`
- `future_return`
- `trade_status`
- `is_st`
- `pe_ttm`

For raw source files, keep upstream names when that helps traceability.
Normalize in views instead of destroying provenance.

### Keys

Prefer natural composite keys in analytics datasets:

- universe history: `(universe_id, stock_code, start_date)`
- daily market master: `(trade_date, stock_code)`
- factor panel: `(trade_date, stock_code, universe_id)`
- selection candidates: `(trade_date, stock_code)` within one run output

### Codes and Dates

- stock codes should use baostock-style identifiers in shared master datasets:
  `sh.600000`, `sz.000001`
- dates must use explicit ISO `YYYY-MM-DD`
- never rely on ambiguous relative dates in stored data contracts

### Path Naming

Formal profiles must align in three places:

1. `market.universe_id`
2. `market.universe_path`
3. `data.path`

Real examples:

- `code/configs/formal_hs300.yaml`
- `code/configs/formal_sz50.yaml`
- `code/configs/formal_zz500.yaml`

---

## Common Mistakes

### 1. Treating the project like a transactional app

This is an analytical thesis pipeline. Do not introduce relational OLTP
complexity unless a real transactional use case appears.

### 2. Duplicating full market data per index

The formal plan is:

- one shared all-A master dataset
- separate universe history files for `HS300`, `SZ50`, `ZZ500`, and tradable
  all-A

Filtering by index should happen through universe history, not through three
duplicated market masters.

### 3. Mixing smoke and formal data

Do not point formal configs to sample files or vice versa.
The repository intentionally keeps:

- smoke inputs for tests and demos
- formal inputs for real runs

### 4. Letting profile metadata drift

Do not change `universe_id` text without also changing:

- universe history path
- factor panel path
- web profile mapping
- tests that assert these contracts

`code/tests/test_backend.py` already guards against this drift.

### 5. Querying raw files directly from the web layer

The web layer should consume:

- stable experiment artifacts such as `selection_candidates.json`
- stable DuckDB views for formal data summaries

Avoid ad-hoc CSV parsing inside request handlers for large formal datasets.

### 6. Forcing heterogeneous financial tables into one raw schema

Baostock financial/report tables have different semantics and fields.
Keep them split by dataset, and normalize only shared query fields at the view
layer.
