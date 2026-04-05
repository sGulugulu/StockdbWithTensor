# Formal Data Layout

This directory now has two responsibilities:

1. Keep the legacy local formal fixtures as backward-compatible raw inputs.
2. Host the newer full-data layout for the formal all-A-share pipeline.

Legacy committed files such as `hs300_history.csv` and `hs300_factor_panel.csv` are still kept here as source fixtures and migration fallbacks, while the formal profiles are moving to the structured `universes/` and `factors/` layout.

For the newer formal layout, prefer the following structure:

- `code/data/formal/baostock/`
  - canonical baostock root for shared metadata, index memberships, shared kline panel, and manifest
- `code/data/formal/universes/`
  - `all_a_tradable_history.csv`
  - `hs300_history.csv`
  - `sz50_history.csv`
  - `zz500_history.csv`
- `code/data/formal/master/`
  - shared CN-A master / shared kline panel used by formal profile builders
- `code/data/formal/financial/`
  - table-split full-data financial exports
- `code/data/formal/reports/`
  - table-split full-data report exports
- `code/data/formal/parquet/`
  - parquet mirrors of validated CSV outputs

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

1. Create a dedicated canonical output directory, for example `code/data/formal/baostock/`.
2. Download index constituents and derived change records for:
   - 沪深300 (`hs300`)
   - 上证50 (`sz50`)
   - 中证500 (`zz500`)
3. Download company metadata with `--metadata-scope all_a` so `stock_basic.csv` and `stock_industry.csv` can support the formal all-A-share universe history.
   This also writes `metadata/all_a_codes.csv`, which is the raw baostock code list for the shared all-A master kline fetch.
4. Build `all_a_tradable_history.csv` from `stock_basic.csv`.
5. Download financial/report tables into the canonical root.
4. Example command:

```powershell
.venv/bin/python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-01 `
  --indices hs300,sz50,zz500 `
  --metadata-scope all_a `
  --all-a-history-output code/data/formal/universes/all_a_tradable_history.csv
```

Output layout:

- `index_memberships/<index>_snapshots.csv`
- `index_memberships/<index>_changes.csv`
- `metadata/stock_basic.csv`
- `metadata/stock_industry.csv`
- `metadata/all_a_codes.csv`
- `code/data/formal/universes/all_a_tradable_history.csv`
- `financial/*.csv`
- `reports/*.csv`
- `manifest.json`

After the constituent snapshots are ready, you can build member-history files and kline panels:

```powershell
.venv/bin/python code/data/build_baostock_member_history.py `
  --snapshot code/data/formal/baostock/index_memberships/hs300_snapshots.csv `
  --output code/data/formal/universes/hs300_history.csv `
  --horizon-date 2026-04-01
```

```powershell
.venv/bin/python code/data/fetch_baostock_kline.py `
  --codes-file code/data/formal/baostock/metadata/all_a_codes.csv `
  --output-path code/data/formal/master/shared_kline_panel.csv `
  --start-date 2015-01-01 `
  --end-date 2026-04-01
```

If `stock_basic.csv` already exists, you can build the tradable all-A-share universe history offline:

```powershell
.venv/bin/python code/data/build_all_a_tradable_history.py `
  --stock-basic-path code/data/formal/baostock/metadata/stock_basic.csv `
  --output-path code/data/formal/universes/all_a_tradable_history.csv `
  --horizon-date 2026-04-01
```

Once the structured CSV outputs are validated, you can create parquet mirrors:

```powershell
.venv/bin/python code/data/convert_formal_csv_to_parquet.py `
  --formal-root code/data/formal `
  --overwrite
```
