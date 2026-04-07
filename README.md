# Thesis Experiment Pipeline

This repository now includes a runnable Python experiment pipeline under `code/` for the thesis topic `基于张量分解的股票因子降维与模式发现`.

## Formal Scope

The formal A-share research scope is now based on:

- `HS300`
- `SZ50`
- `ZZ500`

The formal data architecture is:

- one shared **all-A-share master dataset** for market data
- one shared **all-A-share financial/report dataset** split by table type
- separate universe-history files for:
  - `HS300`
  - `SZ50`
  - `ZZ500`
  - tradable all-A-share universe

The formal full-data window is fixed to:

- `2015-01-01` to `2026-04-01`

The legacy sample datasets remain in the repository only for smoke tests and lightweight validation. They are not the formal research baseline.

## Run

Create the local virtual environment and install dependencies:

```powershell
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

The runtime now expects a PyTorch-capable environment so the project can use:

- `device=cpu`
- `device=cuda`
- `device=auto`

When CUDA is available, the numerical post-processing path prefers GPU execution; otherwise it safely falls back to CPU. The first-stage GPU path is `PyTorch`, with `Triton` or native `CUDA` reserved for later hotspot optimization.

Stage 1: fetch universe-history inputs and metadata from baostock:

```powershell
.venv/bin/python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-01 `
  --indices hs300,sz50,zz500 `
  --skip-financials `
  --skip-reports
```

For formal daily panels, the repository now defaults to **前复权** (`adjustflag=2`) when pulling baostock kline data.

Formal A-share config profiles now exist for:

- `code/configs/formal_hs300.yaml`
- `code/configs/formal_sz50.yaml`
- `code/configs/formal_zz500.yaml`

Stage 2: fetch formal financial and report tables with resume support:

```powershell
.venv/bin/python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-01 `
  --indices hs300,sz50,zz500 `
  --skip-index-memberships `
  --skip-metadata
```

Stage 3: build or refresh the formal daily market panel and downstream factor panel from the canonical formal root.

Stage 4: convert validated formal `CSV` outputs into matching `Parquet` files for larger-scale training and faster reads.

Stage 5: register validated formal `CSV` / `Parquet` datasets into the local `DuckDB` catalog for stable research SQL and web-facing summary queries.

```powershell
.venv/bin/python code/data/register_formal_duckdb_catalog.py `
  --formal-root code/data/formal `
  --catalog-path code/data/formal/catalog.duckdb
```

Use the smoke-test configuration only for lightweight validation:

```powershell
.venv/bin/python code/main.py --config code/configs/sample_cn_smoke.yaml
```

For formal runs, prefer the full-data profiles instead of the smoke profile:

```powershell
.venv/bin/python code/main.py --config code/configs/formal_hs300.yaml
```

The formal profiles are expected to read from the shared all-A-share master data plus universe-history filtering, rather than from duplicated per-index full market datasets.

Run the test suite:

```powershell
.venv/bin/python -m unittest discover -s code/tests
```

## Structure

- `code/configs/default.yaml`: legacy compatibility config, not the formal baseline
- `code/configs/formal_hs300.yaml`: formal HS300 profile
- `code/configs/formal_sz50.yaml`: formal SZ50 profile
- `code/configs/formal_zz500.yaml`: formal ZZ500 profile
- `code/configs/sample_cn_smoke.yaml`: smoke-test configuration for the bundled A-share sample data
- `code/configs/sample_us_equity.yaml`: sample US-equity configuration showing the future market interface
- `code/data/sample_a_share_factors.csv`: synthetic A-share style factor sample
- `code/data/sample_csi_a500_history.csv`: sample CSI A500 membership history input
- `code/data/fetch_baostock_data.py`: downloader for universe histories, metadata, and formal financial/report data
- `code/data/formal/baostock/`: canonical formal baostock root
- `code/data/formal/`: formal derived inputs and outputs
- `code/data/register_formal_duckdb_catalog.py`: DuckDB catalog registration for formal datasets
- `code/stock_tensor/`: preprocessing, tensor construction, models, evaluation, and output logic
- `code/tests/`: automated tests for config loading, dataset building, model fitting, and pipeline execution
- `web/backend/`: minimal FastAPI backend for exposing run and stock-selection results
- `web/frontend/`: React + Vite frontend scaffold for experiment and selection views
- `code/outputs/`: generated experiment artifacts

## Formal Data Layout

The intended formal data layout is:

- all-A-share master market data in one shared dataset
- all-A-share financial/report tables split by source table
- separate universe-history files for `HS300`, `SZ50`, `ZZ500`, and tradable all-A-share
- formal outputs available first as `CSV`, then mirrored into `Parquet`

This layout avoids duplicating the full market dataset once per index and keeps the backtest logic aligned with historical universe membership.

## Web API

Run the backend:

```powershell
.venv/bin/python -m uvicorn web.backend.app:create_app --factory --reload
```

Formal data routes now include:

- `GET /api/formal/coverage`
  - returns shared master coverage, full-master coverage, factor coverage, and financial/report dataset coverage from DuckDB views
- `GET /api/formal/universes/{universe_id}?trade_date=YYYY-MM-DD`
  - returns historical universe members for a specific trading date from DuckDB `vw_*_on_date` views

## Outputs

Each run writes an experiment folder under `code/outputs/` with:

- `run_manifest.json`
- `config_snapshot.yaml`
- `metrics.csv` and `metrics.json`
- `selection_*.csv` and `selection_*.json`
- `factor_summary_*.csv` and `factor_summary_*.json`
- `stock_similarity_*.csv`
- `factor_association_*.csv`
- `time_regimes_*.csv`
- summary SVG charts and `summary.md`
