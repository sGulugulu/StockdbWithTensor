# Thesis Experiment Pipeline

This repository now includes a runnable Python experiment pipeline under `code/` for the thesis topic `基于张量分解的股票因子降维与模式发现`.

## Run

Create the local virtual environment and install dependencies:

```powershell
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Fetch index constituents, change records, and company fundamentals from baostock:

```powershell
.venv/bin/python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-04 `
  --indices hs300,sz50,zz500 `
  --skip-financials `
  --skip-reports
```

Formal A-share config profiles now exist for:

- `code/configs/formal_hs300.yaml`
- `code/configs/formal_sz50.yaml`
- `code/configs/formal_zz500.yaml`
- `code/configs/default.yaml` for `CSI_A500`

After stage 1 finishes, fetch the financial/report tables with resume support:

```powershell
.venv/bin/python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-04 `
  --indices hs300,sz50,zz500 `
  --skip-index-memberships `
  --skip-metadata
```

Use the smoke-test configuration:

```powershell
.venv/bin/python code/main.py --config code/configs/sample_cn_smoke.yaml
```

Run the test suite:

```powershell
.venv/bin/python -m unittest discover -s code/tests
```

## Structure

- `code/configs/default.yaml`: sample experiment configuration
- `code/configs/default.yaml`: formal A-share research configuration with 2015-2026 requested window
- `code/configs/sample_cn_smoke.yaml`: smoke-test configuration for the bundled A-share sample data
- `code/configs/sample_us_equity.yaml`: sample US-equity configuration showing the future market interface
- `code/data/sample_a_share_factors.csv`: synthetic A-share style factor sample
- `code/data/sample_csi_a500_history.csv`: sample CSI A500 membership history input
- `code/data/fetch_baostock_data.py`: downloader for hs300/sz50/zz500 constituents, change records, and financial data
- `code/stock_tensor/`: preprocessing, tensor construction, models, evaluation, and output logic
- `code/tests/`: automated tests for config loading, dataset building, model fitting, and pipeline execution
- `web/backend/`: minimal FastAPI backend for exposing run and stock-selection results
- `web/frontend/`: React + Vite frontend scaffold for experiment and selection views
- `code/outputs/`: generated experiment artifacts

## Web API

Run the backend:

```powershell
.venv/bin/python -m uvicorn web.backend.app:create_app --factory --reload
```

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
