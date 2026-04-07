# Round 4 Summary

## Work Completed
- Added year-partitioned date-window support for baostock fetch flows.
  - New helper: `code/data/year_windows.py`
  - `iter_year_date_ranges()` now splits any `[start_date, end_date]` request into exact year windows.
- Updated `code/data/fetch_baostock_kline.py` so kline fetching can run in year-partitioned mode and recover cleanly across long runs.
  - Added `--partition-by-year`
  - Progress tracking now records per-code per-year completion via `completed_units`
  - Output rows include `query_year` when year partitioning is enabled
  - Login / relogin and progress metadata now record year-complete / run-complete status so the long-range shared-master job can resume with less ambiguity.
- Updated `code/data/fetch_baostock_data.py` so Stage 2 financial and report fetching now materializes by `dataset/year.csv` and resumes by `code|year`.
  - Financial and report rows now persist `query_year`
  - Existing `dataset/year.csv` files are re-read to infer completed `code|year` units before continuing
  - The Stage 2 progress file now stores `_meta` for dataset / year / last completed code, instead of only coarse per-code completion
  - Query selection, timeout handling, and relogin behavior were tightened so long all-A Stage 2 runs fail less often and can restart from the right granularity
- Updated `code/data/run_baostock_full.sh` so the standard formal batch path now protects fresh runs and rebuilds Stage 4 in the same execution flow.
  - Introduced stable path variables for `FORMAL_ROOT`, `BAOSTOCK_ROOT`, `SHARED_MASTER_PATH`, and `SHARED_MASTER_PROGRESS`
  - Added default fresh-run cleanup for `master/shared_kline_panel.csv` plus its progress file via `BAOSTOCK_FULL_FRESH_RUN`
  - The shared-master fetch now passes an explicit `--progress-path`
  - The batch now runs `code/data/convert_formal_csv_to_parquet.py --formal-root code/data/formal --overwrite` before refreshing the canonical manifest
- Added automated coverage for the new year-window and batch-contract behavior.
  - Extended `code/tests/test_baostock_fetch.py` with dataset-year helper coverage
  - Added `code/tests/test_baostock_batch_scripts.py` to lock stable progress-path wiring and Stage 4 ordering
  - Extended `code/tests/test_refresh_formal_baostock_manifest.py` so manifest refresh reports non-empty canonical Stage 2 financial / report outputs when those files exist
- Verified the formal runtime path against a real formal profile in the current environment.
  - `code/main.py --config code/configs/formal_hs300.yaml` completed successfully
  - CUDA is available in the active WSL `.venv`, and explicit CPU fallback remains resolvable

## Files Changed
- Modified: `.humanize/rlcr/2026-04-05_15-24-16/goal-tracker.md`
- Added: `.humanize/rlcr/2026-04-05_15-24-16/round-4-summary.md`
- Added: `code/data/year_windows.py`
- Modified: `code/data/fetch_baostock_kline.py`
- Modified: `code/data/fetch_baostock_data.py`
- Modified: `code/data/refresh_formal_baostock_manifest.py`
- Modified: `code/data/run_baostock_full.sh`
- Modified: `code/tests/test_baostock_fetch.py`
- Modified: `code/tests/test_refresh_formal_baostock_manifest.py`
- Added: `code/tests/test_baostock_batch_scripts.py`
- Added: `code/tests/test_year_windows.py`

## Validation
- `bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m unittest discover -s code/tests && echo UNITTEST_OK"`
  - Result: passed, `Ran 60 tests in 35.362s ... OK`
- `bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设/web/frontend' && npm run build"`
  - Result: passed
- `bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python code/main.py --config code/configs/formal_hs300.yaml"`
  - Result: passed, output written to `code/outputs/formal_hs300_run`
- `bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python - <<\"PY\" ... resolve_device('auto') / resolve_device('cpu') ... PY"`
  - Result: passed
  - `DEVICE_AUTO DeviceContext(requested_device='auto', resolved_device='cuda', torch_available=True)`
  - `DEVICE_CPU DeviceContext(requested_device='cpu', resolved_device='cpu', torch_available=True)`
- `bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python - <<\"PY\" ... torch.cuda.is_available() ... PY"`
  - Result: passed
  - `CUDA_STATUS {'cuda_available': True, 'device_count': 1}`

## Remaining Items
- The canonical shared master kline is still not the required full all-A `2015-01-01` to `2026-04-01` base.
- Structured factor panels are still short-window outputs and still need to be rebuilt from the real full all-A shared master.
- Canonical `financial/` and `reports/` are still not materialized with real all-A Stage 2 data.
- Although fetching is now resumable at `code|year` granularity and the standard batch now rebuilds Stage 4 before manifest refresh, the full all-A Stage 2 and shared-master jobs still need to be executed to completion.
- CUDA is available and both `auto` and explicit `cpu` device resolution were verified, but this round still did not run a separate benchmark-oriented GPU-vs-CPU comparison workload.

## Goal Tracker Update Request

### Requested Changes:
- Amend the Round 4 plan-evolution entry so it records the stronger current state:
  - shared kline fetching is partitioned by year with an explicit stable progress file in the standard batch path
  - Stage 2 financial and report fetching now checkpoints and resumes by `code|year` into `dataset/year.csv`
  - the standard formal batch now runs Stage 4 parquet conversion before manifest refresh
- Update the active-task notes for shared-master / Stage 2 / parquet work to reflect that the pipeline is now resumable at yearly granularity and that Stage 4 is part of the standard batch path, while the real full-range outputs are still not fully materialized.
- Resolve or remove the Round 4 open issue that said `run_baostock_full.sh` lacked a stable shared-master progress path and fresh-run cleanup, because that is now implemented.
- Resolve or replace the Round 4 open issue that said report fetching was still only checkpointing at whole-code granularity, because it now persists and resumes by `code|year`.

### Justification:
- The current summary in the tracker understates the code that now exists in the working tree.
- Round 4 no longer only improves request-window safety; it now also lands the missing batch reproducibility pieces that Codex explicitly called out for shared-master progress handling and Stage 4 ordering.
- Keeping the tracker aligned with the actual checkpoint granularity matters because the remaining blocked work is now “execute the long jobs to completion,” not “invent the resume strategy.”

## BitLesson Delta
- Action: none
- Lesson ID(s): NONE
- Notes: `bitlesson-selector` was not available in the current shell environment. This round focused on making baostock fetches resumable at `code|year` granularity, making the standard batch safer for fresh long-range rebuilds, and ensuring Stage 4 rebuilds happen before manifest refresh.
