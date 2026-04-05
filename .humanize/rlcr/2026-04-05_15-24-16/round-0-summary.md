# Round 0 Summary

## What Was Implemented

- Initialized the new RLCR goal tracker against the current `plan.md` and mapped the new formal data plan into concrete active tasks.
- Updated `code/data/fetch_baostock_data.py` so pure helper logic can be imported and tested even when `baostock` is not installed in the active Python environment.
- Added all-A-share tradable universe history generation logic:
  - helper `build_all_a_tradable_history_rows(...)`
  - CLI `code/data/build_all_a_tradable_history.py`
- Extended the baostock fetch CLI with:
  - `--metadata-scope selected|all_a`
  - `--all-a-history-output`
  so a formal run can now fetch all-A metadata and emit `all_a_tradable_history.csv` in one pipeline.
- Updated `code/data/formal/README.md` to document the new formal data layout:
  - shared all-A master data
  - separate universe-history files
  - split `financial/` and `reports/`
  - future `parquet/` mirror
- Added tests for:
  - A-share equity row filtering
  - all-A tradable history generation from `stock_basic.csv`
  - continued compatibility of existing baostock helper tests

## Files Changed

- Modified: `.humanize/rlcr/2026-04-05_15-24-16/goal-tracker.md`
- Modified: `code/data/fetch_baostock_data.py`
- Added: `code/data/build_all_a_tradable_history.py`
- Modified: `code/tests/test_baostock_fetch.py`
- Modified: `code/data/formal/README.md`

## Validation

- `python -m unittest discover -s code/tests -p 'test_baostock_fetch.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_baostock_member_history.py'`
  - Result: passed
- `python -m unittest discover -s code/tests`
  - Result: passed, `Ran 31 tests ... OK`
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m unittest discover -s code/tests -p 'test_baostock_fetch.py'"`
  - Result: passed
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m unittest discover -s code/tests"`
  - Result: passed, `Ran 31 tests ... OK`

## Remaining Items

- No real full-data fetch has been executed yet with `--metadata-scope all_a`; this round only added the code path and tests.
- The new formal directory structure is documented, but the full migration of committed formal inputs into the new layout is still pending.
- Canonical `financial/` and `reports/` outputs under the new formal plan remain absent.
- Long-range formal data (`2015-01-01` to `2026-04-01`) remains unmaterialized.
- `Parquet` conversion is not started yet.
- CUDA end-to-end validation is still pending.

## BitLesson Delta

Action: none
Lesson ID(s): NONE
Notes: `bitlesson-selector` was not available in the current shell environment. This round focused on making the formal data pipeline importable and testable without live baostock dependencies, plus adding the all-A tradable history generation path required by the new plan.
