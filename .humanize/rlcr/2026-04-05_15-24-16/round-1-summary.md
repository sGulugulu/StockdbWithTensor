# Round 1 Summary

## Work Completed
- Corrected the baostock Stage 2 scope semantics in `code/data/fetch_baostock_data.py`.
  - Added explicit `stage2_scope` handling so financial/report fetching can use either the selected index union or the full A-share code base derived from `stock_basic.csv`.
  - Added `_load_stock_basic_rows_from_output()`, `_all_a_codes_from_stock_basic_rows()`, and `_resolve_stage2_codes()` to make the scope decision explicit and testable.
- Fixed the misleading `all_a_tradable_history.csv` behavior.
  - `--all-a-history-output` is no longer enabled by default.
  - The CLI now rejects `all_a_history_output` unless `metadata_scope=all_a`.
  - This removes the prior correctness bug where a selected-union metadata fetch could silently write a file named as if it were full all-A history.
- Locked the formal time window to the new plan baseline.
  - Updated `formal_hs300.yaml`, `formal_sz50.yaml`, and `formal_zz500.yaml` to use `end_date: 2026-04-01`.
  - Updated `code/data/run_baostock_full.sh` so the default end date is also `2026-04-01`.
- Removed the deprecated formal A500 surface from the backend.
  - Deleted `formal_cn_a` from `_PROFILE_CONFIGS`.
  - Removed the `formal_cn_a` / `CSI_A500` market option from `/api/markets`.
  - Formal profile submission no longer allows request payloads to override the fixed formal window.
- Wired the formal runtime to the new structured layout instead of only documenting it.
  - Formal configs now read from:
    - `code/data/formal/universes/*.csv`
    - `code/data/formal/factors/*.csv`
  - `run_baostock_full.sh` now writes member histories and factor panels to those structured directories.
  - Added runtime-compatible scaffolding under:
    - `code/data/formal/universes/`
    - `code/data/formal/factors/`
    - `code/data/formal/master/`
    - `code/data/formal/financial/`
    - `code/data/formal/reports/`
    - `code/data/formal/parquet/`
- Updated `refresh_formal_baostock_manifest.py` so it can read the new `universes/` and `factors/` layout while still falling back to legacy root-level files when needed.
- Extended tests to lock the new behavior:
  - formal config path/window assertions
  - backend market catalog removal of deprecated A500 formal option
  - backend formal submission contract keeping the fixed formal window
  - stage2 code-scope helper behavior
  - invalid `all_a_history_output` usage

## Files Changed
- Modified: `code/data/fetch_baostock_data.py`
- Modified: `code/data/run_baostock_full.sh`
- Modified: `code/data/refresh_formal_baostock_manifest.py`
- Modified: `code/data/formal/README.md`
- Modified: `code/configs/formal_hs300.yaml`
- Modified: `code/configs/formal_sz50.yaml`
- Modified: `code/configs/formal_zz500.yaml`
- Modified: `web/backend/app.py`
- Modified: `code/tests/test_baostock_fetch.py`
- Modified: `code/tests/test_config_profiles.py`
- Modified: `code/tests/test_formal_config.py`
- Modified: `code/tests/test_backend.py`
- Added / populated: `code/data/formal/universes/`
- Added / populated: `code/data/formal/factors/`
- Added / populated: `code/data/formal/master/`
- Added placeholders: `code/data/formal/financial/`
- Added placeholders: `code/data/formal/reports/`
- Added placeholders: `code/data/formal/parquet/`

## Validation
- `python -m unittest discover -s code/tests -p 'test_baostock_fetch.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_config_profiles.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_formal_config.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_backend.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_refresh_formal_baostock_manifest.py'`
  - Result: passed
- `python -m unittest discover -s code/tests`
  - Result: passed, `Ran 34 tests ... OK`
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m unittest discover -s code/tests"`
  - Result: passed, `Ran 34 tests ... OK`
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设/web/frontend' && npm run build"`
  - Result: passed

## Remaining Items
- Real all-A metadata, all-A financial tables, and all-A report tables are still not materialized on disk. This round fixed the semantics and directory structure, but did not execute the full fetch.
- `code/data/formal/universes/all_a_tradable_history.csv` is still not generated from real all-A metadata in committed artifacts.
- The current shared kline / factor inputs are still the previously committed short-window data, not the full `2015-01-01` to `2026-04-01` range.
- CSV-to-Parquet conversion and parity validation are still not implemented.
- CUDA end-to-end validation remains pending.

## Goal Tracker Update Request

### Requested Changes:
- Add a Plan Evolution entry noting that the formal runtime has now been switched from legacy root-level profile paths to `universes/` and `factors/`, and that the backend formal market catalog no longer exposes deprecated `formal_cn_a` / `CSI_A500`.
- Update the active Stage 2 / all-A data task notes to reflect that:
  - Stage 2 scope semantics are now explicit
  - `all_a_history_output` is now gated behind true all-A metadata scope
  - the remaining blocker is real full-data materialization, not CLI ambiguity
- Add an Open Issue that the newly created structured directories currently contain migrated short-window fixtures and placeholders rather than real full-range all-A data.

### Justification:
- This round resolved the correctness issues Codex identified around Stage 2 scope, misleading all-A history defaults, deprecated formal A500 exposure, and fixed-window enforcement.
- The remaining gaps are now narrower and more operational: full data materialization, parquet generation, and CUDA validation.

## BitLesson Delta
- Action: none
- Lesson ID(s): NONE
- Notes: `bitlesson-selector` was not available in the current shell environment. This round focused on correcting formal data pipeline semantics, locking the formal window, and wiring the structured formal layout into the runtime.
