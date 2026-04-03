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
- `code/data/sample_a_share_factors.csv`: synthetic A-share style factor sample
- `code/stock_tensor/`: preprocessing, tensor construction, models, evaluation, and output logic
- `code/tests/`: automated tests for config loading, dataset building, model fitting, and pipeline execution
- `code/outputs/`: generated experiment artifacts

## Outputs

Each run writes an experiment folder under `code/outputs/` with:

- `config_snapshot.yaml`
- `metrics.csv` and `metrics.json`
- `stock_similarity_*.csv`
- `factor_association_*.csv`
- `time_regimes_*.csv`
- summary SVG charts and `summary.md`
