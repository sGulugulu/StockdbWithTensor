# Round 3 Summary

## Work Completed
- Repaired the canonical manifest provenance path in `refresh_formal_baostock_manifest.py`.
  - The refresh flow no longer reads canonical `manifest.json` back as three fake stage-source manifests.
  - `stage_1_stage_2_committed_sources` is now rebuilt from the current canonical files per index:
    - snapshot path / row count / date range
    - change path / row count / date range
    - current metadata row counts
    - current selected-code / all-A-code counts
  - Added a self-copy guard so `src == dst` refresh runs do not recurse or fail.
- Finished the parquet pipeline from “script exists” to “real outputs exist”.
  - Added `summarize_parquet_outputs()` to `code/data/convert_formal_csv_to_parquet.py`
  - Added manifest recording for `stage_4_parquet_outputs`
  - Installed `pyarrow` in the WSL `.venv`
  - Generated real parquet outputs for the current structured CSV base under:
    - `code/data/formal/parquet/universes/`
    - `code/data/formal/parquet/factors/`
    - `code/data/formal/parquet/master/`
  - Each recorded parquet entry now includes:
    - CSV path
    - parquet path
    - existence flag
    - row-count parity
    - column parity
    - date-range parity when a date column exists
- Completed real all-A metadata materialization and carried it into the canonical root:
  - `stock_basic.csv`: `8680`
  - `stock_industry.csv`: `5509`
  - `all_a_codes.csv`: `5059`
  - `all_a_tradable_history.csv`: `5059`
- Locked the all-A Stage 2 live symbol format via tests so all-A live fetches stay on baostock-native `sh.600000` / `sz.000001` format.

## Files Changed
- Modified: `.humanize/rlcr/2026-04-05_15-24-16/goal-tracker.md`
- Added: `.humanize/rlcr/2026-04-05_15-24-16/round-3-summary.md`
- Modified: `code/data/convert_formal_csv_to_parquet.py`
- Modified: `code/data/refresh_formal_baostock_manifest.py`
- Modified: `code/tests/test_convert_formal_csv_to_parquet.py`
- Modified: `code/tests/test_refresh_formal_baostock_manifest.py`
- Modified: `code/data/formal/baostock/manifest.json`
- Modified: `code/data/formal/baostock/metadata/stock_basic.csv`
- Modified: `code/data/formal/baostock/metadata/stock_industry.csv`
- Added: `code/data/formal/baostock/metadata/all_a_codes.csv`
- Added: `code/data/formal/universes/all_a_tradable_history.csv`
- Added: `code/data/formal/parquet/universes/all_a_tradable_history.parquet`
- Added: `code/data/formal/parquet/universes/hs300_history.parquet`
- Added: `code/data/formal/parquet/universes/sz50_history.parquet`
- Added: `code/data/formal/parquet/universes/zz500_history.parquet`
- Added: `code/data/formal/parquet/factors/hs300_factor_panel.parquet`
- Added: `code/data/formal/parquet/factors/sz50_factor_panel.parquet`
- Added: `code/data/formal/parquet/factors/zz500_factor_panel.parquet`
- Added: `code/data/formal/parquet/master/shared_kline_panel.parquet`

## Validation
- `python -m unittest discover -s code/tests`
  - Result: passed, `Ran 39 tests ... OK (skipped=1)`
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m unittest discover -s code/tests"`
  - Result: passed, `Ran 39 tests ... OK`
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设/web/frontend' && npm run build"`
  - Result: passed
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m pip install pyarrow"`
  - Result: passed
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m unittest discover -s code/tests -p 'test_convert_formal_csv_to_parquet.py'"`
  - Result: passed
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python code/data/convert_formal_csv_to_parquet.py --formal-root code/data/formal --overwrite"`
  - Result: passed, converted `8` CSV files to parquet with row / column / date-range parity
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python code/data/refresh_formal_baostock_manifest.py"`
  - Result: passed

## Remaining Items
- The canonical shared master kline is still not a real full all-A `2015-01-01` to `2026-04-01` panel; it is still the short-window migrated fixture (`572` codes, `2026-03-02` to `2026-04-03`).
- Structured factor panels are still built from the short-window shared master fixture rather than a rebuilt full all-A master base.
- `code/data/formal/financial/` and `code/data/formal/reports/` are still not materialized with real all-A Stage 2 outputs.
- Although parquet output generation is now real and parity is recorded, the parquet set currently mirrors the same short-window structured CSV base, not the final full-range formal data base.
- CUDA end-to-end validation remains pending; only CPU-path validation exists in the current environment.

## Goal Tracker Update Request

### Requested Changes:
- Add a Round 3 plan-evolution entry noting that:
  - canonical manifest provenance is now rebuilt from the current canonical file set instead of re-reading canonical `manifest.json` as fake source manifests
  - parquet conversion is now fully operational in the project `.venv` and real parity-checked parquet outputs exist for the current structured CSV base
- Update the active parquet task notes to reflect that:
  - converter implementation exists
  - real parquet outputs now exist
  - remaining blocker is that they mirror short-window structured CSVs rather than final full-range formal data
- Add an open issue that the all-A shared master and rebuilt factor panels remain short-window fixtures even though all-A metadata is now real.

### Justification:
- This round closes the specific manifest-provenance defect called out in the Round 2 review.
- It also turns AC-5 progress from “script exists” into actual generated parquet outputs with parity metadata.
- The remaining blockers are now concentrated on true full-range all-A kline / factor / financial / report materialization and CUDA validation.

## BitLesson Delta
- Action: none
- Lesson ID(s): NONE
- Notes: `bitlesson-selector` was not available in the current shell environment. This round focused on fixing canonical manifest provenance and making parquet generation real, parity-checked, and reproducible in the active `.venv`.
