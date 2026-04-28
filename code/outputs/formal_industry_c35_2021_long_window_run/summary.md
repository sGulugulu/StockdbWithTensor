# Experiment Summary

## Models
- cp: rank=2, mse=0.956839, explained_variance=0.0214, rank_ic_mean=0.1901
- tucker: rank=(3, 2, 2), mse=0.599998, explained_variance=0.3864, rank_ic_mean=0.1954
- pca: rank=3, mse=0.070637, explained_variance=0.9278, rank_ic_mean=0.1161

## Output Files
- `metrics.csv` / `metrics.json`: model comparison table
- `stock_similarity_*.csv`: stock linkage candidates
- `factor_association_*.csv`: factor resonance candidates
- `time_regimes_*.csv`: largest adjacent time shifts
- `selection_*.csv` / `selection_*.json`: per-date stock selection signals
- `selection_candidates.csv` / `selection_candidates.json`: unified per-date candidate pool
- `factor_summary_*.csv` / `factor_summary_*.json`: factor importance summaries
- `portfolio_metrics.csv` / `portfolio_metrics.json`: Top-N portfolio summary metrics
- `group_returns_*.csv` / `group_returns_*.json`: per-date portfolio return series
- `drawdown_*.csv` / `drawdown_*.json`: cumulative nav and drawdown series
- `exposure_*.csv` / `exposure_*.json`: industry and style exposure summaries
- `quantile_returns_*.csv` / `quantile_returns_*.json`: quantile portfolio return series
- `long_short_*.csv` / `long_short_*.json`: top-bottom long-short series
- `cost_adjusted_*.csv` / `cost_adjusted_*.json`: transaction-cost adjusted series
- `excess_returns_*.csv` / `excess_returns_*.json`: benchmark-relative excess return series
- `run_manifest.json`: machine-readable run metadata for web services
- `model_explained_variance.svg` and `model_rank_ic.svg`: signed metric bar charts
- `model_metrics_overview.svg`: grouped comparison of core metrics
- `time_regime_timeline.svg`: timeline of daily regime shifts
- `factor_importance_heatmap.svg`: factor importance heatmap across models
- `group_returns_overview.svg`: cumulative portfolio NAV comparison
- `drawdown_overview.svg`: portfolio drawdown comparison
- `long_short_overview.svg`: long-short portfolio NAV comparison
- `excess_returns_overview.svg`: excess return NAV comparison
- `cost_adjusted_overview.svg`: cost-adjusted portfolio NAV comparison