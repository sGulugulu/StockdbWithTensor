# Formal Data Placeholder

Put the real A-share production inputs here before running `code/configs/default.yaml`.

Expected files:

- `csi_a500_history.csv`
- `csi_a500_factor_panel.csv`

The formal configuration intentionally points to these paths so that the default run fails fast when real data has not been provided, instead of silently falling back to the bundled smoke-test fixtures.

Tongdaxin workflow:

1. Export the full daily panel to `tdx_daily_raw.csv`.
2. Prepare member files for:
   - `hs300_history.csv`
   - `csi_a500_history.csv`
   - `csi_a50_history.csv`
3. Build index-specific daily CSV files with:

```powershell
python3 code/data/build_tdx_index_files.py `
  --raw-daily code/data/formal/tdx_daily_raw.csv `
  --hs300-members code/data/formal/hs300_history.csv `
  --csi-a500-members code/data/formal/csi_a500_history.csv `
  --csi-a50-members code/data/formal/csi_a50_history.csv `
  --date-column trade_date `
  --member-start-column start_date `
  --member-end-column end_date `
  --output-dir code/data/formal
```
