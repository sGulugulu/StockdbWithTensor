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

Baostock workflow:

1. Create a dedicated output directory, for example `code/data/formal/baostock/`.
2. Download index constituents and derived change records for:
   - 沪深300 (`hs300`)
   - 上证50 (`sz50`)
   - 中证500 (`zz500`)
3. Download company metadata and financial/report tables for the union of all selected constituent stocks.
4. Example command:

```powershell
.venv/bin/python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-04 `
  --indices hs300,sz50,zz500
```

Output layout:

- `index_memberships/<index>_snapshots.csv`
- `index_memberships/<index>_changes.csv`
- `metadata/stock_basic.csv`
- `metadata/stock_industry.csv`
- `financial/*.csv`
- `reports/*.csv`
- `manifest.json`

After the constituent snapshots are ready, you can build member-history files and kline panels:

```powershell
.venv/bin/python code/data/build_baostock_member_history.py `
  --snapshot code/data/formal/baostock/index_memberships/hs300_snapshots.csv `
  --output code/data/formal/hs300_history.csv
```

```powershell
.venv/bin/python code/data/fetch_baostock_kline.py `
  --codes-file code/data/formal/baostock/metadata/selected_codes.csv `
  --output-path code/data/formal/baostock/kline_panel.csv `
  --start-date 2015-01-01 `
  --end-date 2026-04-04
```
