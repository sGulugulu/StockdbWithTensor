# Thesis Experiment Pipeline

This repository now includes a runnable Python experiment pipeline under `code/` for the thesis topic `基于张量分解的股票因子降维与模式发现`.

## Run

Use the default sample configuration:

```powershell
python code/main.py
```

Run the test suite:

```powershell
python -m unittest discover -s code/tests
```

## Structure

- `code/configs/default.yaml`: sample experiment configuration
- `code/configs/sample_us_equity.yaml`: sample US-equity configuration showing the future market interface
- `code/data/sample_a_share_factors.csv`: synthetic A-share style factor sample
- `code/data/sample_csi_a500_history.csv`: sample CSI A500 membership history input
- `code/stock_tensor/`: preprocessing, tensor construction, models, evaluation, and output logic
- `code/tests/`: automated tests for config loading, dataset building, model fitting, and pipeline execution
- `web/backend/`: minimal FastAPI backend for exposing run and stock-selection results
- `code/outputs/`: generated experiment artifacts

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
