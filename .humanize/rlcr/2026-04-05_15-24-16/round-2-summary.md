# Round 2 Summary

## Work Completed
- Corrected the all-A Stage 2 live code contract.
  - Added `_to_baostock_code()` and changed `_all_a_codes_from_stock_basic_rows()` so the all-A Stage 2 path now emits baostock-native raw symbols such as `sh.600000` / `sz.000001`, not normalized `600000.SH` / `000001.SZ`.
  - Extended `test_baostock_fetch.py` to lock this behavior.
- Added explicit all-A master code-list output.
  - When `metadata_scope=all_a`, `fetch_baostock_data.py` now writes `code/data/formal/baostock/metadata/all_a_codes.csv`.
  - `run_baostock_full.sh` now uses `all_a_codes.csv` instead of `selected_codes.csv` for the shared master kline fetch.
- Reworked canonical refresh defaults so the batch path no longer depends on legacy fixture roots.
  - `refresh_formal_baostock_manifest.py` defaults now point at the canonical formal baostock root instead of `baostock_fg_test`, `baostock_sz50_fg`, and `baostock_zz500_fg`.
  - Added a self-copy guard in `_copy_tree()` so canonical refresh does not fail or overwrite itself when source and destination are the same path.
  - Extended `test_refresh_formal_baostock_manifest.py` to verify the canonical refresh path no longer depends on legacy fixture defaults.
- Added an actual CSV-to-Parquet conversion implementation.
  - New script: `code/data/convert_formal_csv_to_parquet.py`
  - Supports structured directories under `universes/`, `factors/`, `master/`, `financial/`, and `reports/`
  - Detects parquet-engine availability (`pyarrow` / `fastparquet`) explicitly instead of failing deep inside pandas
  - Added `test_convert_formal_csv_to_parquet.py`
  - Added `pandas` and `pyarrow` to `requirements.txt`
- Materialized real all-A metadata and tradable-universe artifacts in the canonical formal root.
  - Ran a real baostock metadata fetch in WSL with:
    - `--skip-index-memberships`
    - `--metadata-scope all_a`
    - `--all-a-history-output code/data/formal/universes/all_a_tradable_history.csv`
  - This produced:
    - `code/data/formal/baostock/metadata/stock_basic.csv` with `8680` rows
    - `code/data/formal/baostock/metadata/stock_industry.csv` with `5509` rows
    - `code/data/formal/baostock/metadata/all_a_codes.csv` with `5059` rows
    - `code/data/formal/universes/all_a_tradable_history.csv` with `5059` rows

## Files Changed
- Modified: `.humanize/rlcr/2026-04-05_15-24-16/goal-tracker.md`
- Added: `.humanize/rlcr/2026-04-05_15-24-16/round-2-summary.md`
- Modified: `code/data/fetch_baostock_data.py`
- Modified: `code/data/run_baostock_full.sh`
- Modified: `code/data/refresh_formal_baostock_manifest.py`
- Added: `code/data/convert_formal_csv_to_parquet.py`
- Modified: `code/data/formal/README.md`
- Modified: `requirements.txt`
- Modified: `code/tests/test_baostock_fetch.py`
- Modified: `code/tests/test_refresh_formal_baostock_manifest.py`
- Added: `code/tests/test_convert_formal_csv_to_parquet.py`
- Modified: `code/data/formal/baostock/manifest.json`
- Modified: `code/data/formal/baostock/metadata/stock_basic.csv`
- Modified: `code/data/formal/baostock/metadata/stock_industry.csv`
- Added: `code/data/formal/baostock/metadata/all_a_codes.csv`
- Added: `code/data/formal/universes/all_a_tradable_history.csv`

## Validation
- `python -m unittest discover -s code/tests -p 'test_baostock_fetch.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_convert_formal_csv_to_parquet.py'`
  - Result: passed (`1` skip on Windows due missing parquet engine)
- `python -m unittest discover -s code/tests -p 'test_refresh_formal_baostock_manifest.py'`
  - Result: passed
- `python -m unittest discover -s code/tests`
  - Result: passed, `Ran 39 tests ... OK (skipped=1)`
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m unittest discover -s code/tests"`
  - Result: passed, `Ran 39 tests ... OK (skipped=1)`
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设/web/frontend' && npm run build"`
  - Result: passed
- Real metadata materialization:
  - `wsl bash -lc ".venv/bin/python code/data/fetch_baostock_data.py --output-root code/data/formal/baostock --start-date 2015-01-01 --end-date 2026-04-01 --indices hs300,sz50,zz500 --skip-index-memberships --metadata-scope all_a --all-a-history-output code/data/formal/universes/all_a_tradable_history.csv --skip-financials --skip-reports"`
  - Result: passed
  - Output counts:
    - `stock_basic.csv`: `8680`
    - `stock_industry.csv`: `5509`
    - `all_a_codes.csv`: `5059`
    - `all_a_tradable_history.csv`: `5059`

## Remaining Items
- The shared master kline base is still not a real full all-A master panel; `code/data/formal/master/shared_kline_panel.csv` is still the previously committed short-window migrated fixture.
- Full all-A financial tables and report tables are still not materialized under `code/data/formal/financial/` and `code/data/formal/reports/`.
- Structured `factors/` outputs are still short-window migrated fixtures, not rebuilt from a real full all-A master panel.
- Parquet conversion code now exists, but no real parquet outputs have been generated yet because the active environments still lack a parquet engine and the formal CSV base is not fully materialized.
- CUDA end-to-end validation remains pending.

## Goal Tracker Update Request

### Requested Changes:
- Add a Round 2 plan-evolution entry recording that:
  - all-A Stage 2 code format is now aligned to baostock-native raw symbols
  - the canonical refresh defaults no longer point to legacy fixture roots
  - parquet conversion now exists as executable code rather than README-only intent
- Update the all-A metadata active-task notes to reflect that real all-A metadata and `all_a_tradable_history.csv` are now materialized in the canonical formal root.
- Add an open issue that the shared master kline and structured factor outputs are still migrated short-window fixtures rather than rebuilt full all-A outputs.
- Add an open issue that parquet conversion code exists but the environment still needs a parquet engine plus real full-range CSV outputs before parity can be completed.

### Justification:
- This round closes two correctness bugs identified in the Round 1 review: wrong symbol format for all-A Stage 2 live fetches and canonical refresh dependence on stale fixture defaults.
- It also converts the all-A metadata task from “just semantics” into real materialized outputs.
- The remaining blockers are now more specific: full all-A kline/factor/report materialization, parquet output generation, and CUDA validation.

## BitLesson Delta
- Action: none
- Lesson ID(s): NONE
- Notes: `bitlesson-selector` was not available in the current shell environment. This round focused on correcting live baostock symbol contracts, removing canonical refresh dependence on legacy fixtures, adding parquet conversion code, and materializing real all-A metadata outputs.
