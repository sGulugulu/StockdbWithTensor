# Round 12 Summary

## Work Completed
- Reworked `refresh_formal_baostock_manifest.py` so canonical Stage 3 shared artifacts are rebuilt from a single explicit source of truth instead of relying on copied per-pool metadata files.
- Added explicit canonical shared-output generation via `build_union_kline_panel()` using committed `hs300_kline_panel.csv`, `sz50_kline_panel.csv`, and `zz500_kline_panel.csv`.
- Prevented copied source trees from overwriting canonical `metadata/selected_codes.csv`; the canonical selected-code list is now rebuilt from the shared union flow instead of inheriting the last copied pool.
- Added hard consistency checks before writing the canonical manifest:
  - canonical `selected_codes.csv` must equal the canonical `kline_panel.csv` code set
  - canonical shared code set must cover every code used by committed formal factor panels
- Strengthened `test_union_kline_panel.py` so it now asserts exact merged row output, exact code union output, and dedupe behavior on overlapping `(date, code)` rows.
- Added `test_refresh_formal_baostock_manifest.py` to lock the refresh-path contract: canonical refresh must rebuild shared union outputs even if source directories contain conflicting `selected_codes.csv`.
- Completed the missing formal Web contract assertions in `test_backend.py` for `formal_sz50` and `formal_zz500`, matching the `formal_hs300` coverage.
- Kept the path-relativization work coherent with the backend contract:
  - added `code/stock_tensor/path_utils.py`
  - made output snapshots/manifests/logs serialize project paths relative to repo where possible
  - made formal run outputs assert relative path snapshots in `test_formal_config.py`
- Refreshed committed canonical files so `code/data/formal/baostock/metadata/selected_codes.csv` and `manifest.json` now reflect the 572-code shared union state.

## Files Changed
- Modified: `code/data/refresh_formal_baostock_manifest.py`
- Modified: `code/data/formal/baostock/manifest.json`
- Modified: `code/data/formal/baostock/metadata/selected_codes.csv`
- Modified: `code/tests/test_union_kline_panel.py`
- Added: `code/tests/test_refresh_formal_baostock_manifest.py`
- Modified: `code/tests/test_backend.py`
- Added: `code/stock_tensor/path_utils.py`
- Modified: `web/backend/app.py`
- Modified: `code/stock_tensor/output.py`
- Modified: `code/stock_tensor/pipeline.py`
- Modified: `code/tests/test_formal_config.py`

## Validation
- `python -m unittest discover -s code/tests -p 'test_union_kline_panel.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_refresh_formal_baostock_manifest.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_backend.py'`
  - Result: passed
- `python -m unittest discover -s code/tests -p 'test_formal_config.py'`
  - Result: passed
- `python code/data/refresh_formal_baostock_manifest.py`
  - Result: succeeded and rewrote canonical manifest / selected codes
- Direct canonical probe over `code/data/formal/baostock`
  - Result: `kline_panel.csv` has `14300` rows / `572` codes; canonical `metadata/selected_codes.csv` now also has `572` codes; no missing codes in either direction
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设' && .venv/bin/python -m unittest discover -s code/tests"`
  - Result: passed, `Ran 29 tests ... OK`
- `wsl bash -lc "cd '/mnt/d/Personal folders/Desktop/宋田琦/毕设/web/frontend' && npm run build"`
  - Result: passed

## Remaining Items
- Stage 2 formal outputs remain absent under canonical `code/data/formal/baostock/financial` and `code/data/formal/baostock/reports`.
- Committed formal datasets still remain short 2026 slices:
  - `hs300_history.csv`, `sz50_history.csv`, `zz500_history.csv` still cover `2026-03-02` to `2026-03-30`
  - `hs300_factor_panel.csv`, `sz50_factor_panel.csv`, `zz500_factor_panel.csv` still cover `2026-03-02` to `2026-04-03`
  - `hs300_factor_panel.csv` still contains only 30 stocks
- CUDA end-to-end validation is still not recorded. CPU fallback and torch-path coverage are validated, but AC-8 remains partial until real CUDA evidence exists or unavailable hardware is explicitly accepted as the blocker.
- Windows-side `python -m unittest discover -s code/tests` still fails on `test_baostock_fetch.py` because the Windows Python environment in this session does not have `baostock` installed; the WSL project `.venv` does have `baostock`, and the full suite passed there.

## Goal Tracker Update Request

### Requested Changes:
- Mark the canonical Stage 3 consistency subtask as substantially advanced:
  - canonical refresh now rebuilds shared union outputs from the three formal kline panels
  - canonical `selected_codes.csv` and shared `kline_panel.csv` are now consistent (`572` / `572`)
  - consistency is locked by dedicated refresh-path and union-path tests
- Mark the Web formal profile contract gap as resolved:
  - `formal_sz50` and `formal_zz500` now receive the same `submitted_config.yaml` assertions as `formal_hs300`
- Keep the Stage 2 formal-output task, long-range formal-data task, and CUDA validation task open
- Update Open Issues wording so the canonical Stage 3 blocker is no longer “selected_codes mismatch”, but instead the remaining blockers are Stage 2 materialization and long-range data regeneration

### Justification:
- This round closes the specific reproducibility bug Codex identified in Round 11/12: canonical shared artifacts are now built from one source of truth and checked before manifest write.
- This round also closes the missing formal Web profile contract assertions that left `formal_sz50` / `formal_zz500` under-tested.
- The remaining blockers are real and substantive, but they are now narrower than before and should be tracked as such.

## BitLesson Delta
- Action: none
- Lesson ID(s): NONE
- Notes: `bitlesson-selector` was not available in the current shell environment, and this round did not add a reusable project-specific lesson entry beyond the existing template.
