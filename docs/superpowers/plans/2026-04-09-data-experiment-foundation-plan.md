# Data Experiment Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the formal A-share data and baseline experiment foundation for the thesis so `HS300`, `SZ50`, and `ZZ500` can run as separate formal samples on top of a shared long-term A-share master, explicit preprocessing, stable `stock-factor-time` tensor inputs, and standardized metrics and artifact outputs.

**Architecture:** Branch 1 treats the data foundation as a layered contract: long-term A-share coverage is preserved in shared master data and `all_a_tradable` history, current thesis experiments are limited to `HS300` / `SZ50` / `ZZ500`, preprocessing becomes an explicit boundary between raw formal panels and tensor construction, and experiment outputs are written as machine-readable artifacts under `code/outputs`. The implementation path should converge existing shared-kline, full-master, factor-panel, config, tensor, and output code rather than introducing a second parallel pipeline.

**Tech Stack:** Python, baostock, CSV, Parquet, DuckDB, NumPy, existing `code/stock_tensor` pipeline, existing `code/tests` unittest suite

---

## Branch Scope

This branch covers only **Research Data and Experiment Foundation**.

In scope:

- formal data directory and field contracts
- universe-history completion
- shared-kline / full-master convergence
- preprocessing as an explicit phase
- stable tensor-ready factor inputs
- configurable split strategies with thesis default = time-based
- `CP` / `Tucker` baseline experiment loop on formal samples
- metrics and artifact contracts for downstream thesis and system work

Out of scope for this branch:

- Go gateway and web route work
- frontend pages
- multi-market implementation beyond preserving A-share-compatible abstractions
- GPU/Triton optimization work beyond keeping current code paths compatible with later extension

## Branch Contracts To Freeze

### 1. Formal Data Directory Contract

The branch must make the formal directory layout explicit and stable.

Required formal layers:

- `code/data/formal/baostock/`: upstream fetch manifests and staged raw pulls
- `code/data/formal/master/`: shared market master inputs and reconciliation artifacts
- `code/data/formal/universes/`: `HS300`, `SZ50`, `ZZ500`, and `all_a_tradable` history files
- `code/data/formal/factors/`: tensor-ready factor panels for current formal samples
- `code/data/formal/parquet/`: parquet mirrors of formal CSV-backed contracts
- `code/data/formal/catalog.duckdb`: formal query catalog

Hard rules:

- sample data remains separate from formal data
- formal CSV and Parquet objects must map one-to-one
- manifests must identify data window, source, schema version, and producing script
- formal experiments consume current sample-specific factor panels, but long-term coverage remains broader A-share

### 2. Long-Term Coverage vs Current Formal Samples

The branch must keep two layers distinct:

- **long-term coverage layer:** broader A-share via shared master plus `all_a_tradable` history
- **current formal experiment layer:** separate `HS300`, `SZ50`, and `ZZ500` runs

The implementation must not collapse these into one static stock list or one merged thesis sample.

### 3. Preprocessing Boundary Contract

Preprocessing must be represented as its own explicit stage between factor-panel loading and tensor construction.

Required responsibilities:

- sample filtering
- date and field alignment
- missing-value handling
- outlier handling
- factor direction normalization and standardization
- label and metadata separation
- leakage control across train/eval boundaries

Future return labels remain evaluation targets and must not enter the model input tensor.

### 4. Tensor Input Contract

The experiment input object remains a `stock-factor-time` tensor per formal sample.

Required tensor contract:

- one stock axis per sample universe after historical membership filtering
- one factor axis from the formal factor panel contract
- one time axis after date alignment and split preparation
- labels stored separately from tensor inputs
- enough metadata retained to map outputs back to stock code, date, factor name, industry, market, and universe

### 5. Metrics and Artifact Contract

Every formal run under `code/outputs/<run_id or experiment_name>/` must produce machine-readable artifacts that both thesis interpretation and later system work can consume.

Minimum artifact set:

- `run_manifest.json`
- `metrics.csv`
- `metrics.json`
- `selection_candidates.csv`
- `selection_candidates.json`
- `factor_summary_<model>.csv`
- `factor_summary_<model>.json`
- `factor_association_<model>.csv`
- `factor_association_<model>.json`
- `time_regimes_<model>.csv`
- `time_regimes_<model>.json`
- `summary.md`

Minimum metrics set:

- reconstruction error metrics
- compression / rank behavior metrics
- rolling stability metrics
- pattern interpretation summaries
- prediction or decision usefulness metrics computed on held-out data
- split metadata and actual train/eval coverage written to the run manifest

## Planned File Ownership

The branch should prefer modifying and tightening existing files over creating duplicate implementations.

### Data contracts and formal docs

- Modify: `code/data/formal/README.md`
- Modify: `code/data/formal/universes/README.md`
- Modify: `code/data/formal/master/FULL_MASTER_CONTRACT.md`
- Modify: `code/data/formal/factors/README.md`
- Modify: `code/data/formal/DATABASE_DESIGN.md`
- Create: `code/data/formal/PREPROCESSING_CONTRACT.md`
- Create: `code/data/formal/factors/TENSOR_INPUT_CONTRACT.md`
- Create: `code/outputs/README.md`

### Data build and reconciliation scripts

- Modify: `code/data/build_all_a_tradable_history.py`
- Modify: `code/data/build_baostock_member_history.py`
- Modify: `code/data/build_union_kline_panel.py`
- Modify: `code/data/build_full_master_for_year.py`
- Modify: `code/data/reconcile_full_master_year.py`
- Modify: `code/data/build_formal_factor_panel.py`
- Modify: `code/data/convert_formal_csv_to_parquet.py`
- Modify: `code/data/register_formal_duckdb_catalog.py`
- Modify: `code/data/refresh_formal_baostock_manifest.py`

### Experiment config and runtime

- Modify: `code/configs/formal_hs300.yaml`
- Modify: `code/configs/formal_sz50.yaml`
- Modify: `code/configs/formal_zz500.yaml`
- Modify: `code/stock_tensor/config.py`
- Modify: `code/stock_tensor/market.py`
- Modify: `code/stock_tensor/dataset.py`
- Modify: `code/stock_tensor/pipeline.py`
- Modify: `code/stock_tensor/evaluation.py`
- Modify: `code/stock_tensor/output.py`
- Create: `code/stock_tensor/preprocess.py`
- Create: `code/stock_tensor/splits.py`

### Tests

- Modify: `code/tests/test_formal_config.py`
- Modify: `code/tests/test_baostock_member_history.py`
- Modify: `code/tests/test_union_kline_panel.py`
- Modify: `code/tests/test_build_full_master_for_year.py`
- Modify: `code/tests/test_reconcile_full_master_year.py`
- Modify: `code/tests/test_formal_factor_panel.py`
- Modify: `code/tests/test_dataset.py`
- Modify: `code/tests/test_pipeline.py`
- Modify: `code/tests/test_register_formal_duckdb_catalog.py`
- Create: `code/tests/test_preprocess.py`
- Create: `code/tests/test_split_strategy.py`
- Create: `code/tests/test_output_contract.py`

## Task Sequence

### Task 1: Freeze the formal data directory and manifest contracts

**Dependencies:** none

**Deliverables:**

- a written contract for the formal data tree
- one-to-one CSV/Parquet mapping rules
- explicit separation between sample data and formal data
- manifest fields documented as branch requirements

- [ ] Audit the current formal tree under `code/data/formal/` and list the canonical contract objects that already exist versus the ones that are transitional or underspecified.
- [ ] Update `code/data/formal/README.md`, `code/data/formal/DATABASE_DESIGN.md`, and `code/data/formal/master/FULL_MASTER_CONTRACT.md` so the branch has one documented source of truth for directory roles, schema ownership, and manifest expectations.
- [ ] Add a preprocessing contract doc and tensor input contract doc so downstream tasks do not bury data semantics only inside Python code.
- [ ] Verify that the documented contracts still match the current formal configs and DuckDB registration expectations.
- [ ] Run: `python -m unittest discover -s code/tests -p "test_formal_config.py"` and `python -m unittest discover -s code/tests -p "test_register_formal_duckdb_catalog.py"`

### Task 2: Complete universe-history files and lock the sample protocol

**Dependencies:** Task 1

**Deliverables:**

- complete and documented `HS300`, `SZ50`, `ZZ500`, and `all_a_tradable` history contracts
- sample-specific configs still running separately
- broader A-share coverage preserved without merging the three formal samples together

- [ ] Make `code/data/build_all_a_tradable_history.py` and `code/data/build_baostock_member_history.py` the only supported builders for formal universe histories and remove ambiguity about one-off or transitional sources.
- [ ] Ensure the history contract records at least `market_id`, `universe_id`, `stock_code`, `start_date`, and `end_date`, and document how point-in-time membership is derived.
- [ ] Reconcile `code/configs/formal_hs300.yaml`, `code/configs/formal_sz50.yaml`, and `code/configs/formal_zz500.yaml` so each config points to the correct universe history file and factor panel instead of relying on informal naming assumptions.
- [ ] Add or update tests to prove historical membership filtering uses point-in-time inclusion and that the three thesis samples remain separate runs.
- [ ] Run: `python -m unittest discover -s code/tests -p "test_baostock_member_history.py"` and `python -m unittest discover -s code/tests -p "test_formal_config.py"`

### Task 3: Converge shared-kline and full-master into one formal master story

**Dependencies:** Task 1, Task 2

**Deliverables:**

- a single documented relationship between shared kline panels, year-built master files, and the reconciled full master
- parity checks between CSV and Parquet-backed formal master objects
- DuckDB registration aligned to the converged contract

- [ ] Clarify how `code/data/build_union_kline_panel.py`, `code/data/build_full_master_for_year.py`, and `code/data/reconcile_full_master_year.py` feed one shared formal master contract instead of competing data routes.
- [ ] Define the convergence rule: the shared market master remains the long-term A-share backbone, while sample universes filter that master at experiment time.
- [ ] Tighten reconciliation outputs and checks so a year-level build, the shared kline layer, and the final `full_master` objects can be audited against the same contract.
- [ ] Update DuckDB registration logic so `master.*` and `full_master.*` expose the converged objects with stable names.
- [ ] Run: `python -m unittest discover -s code/tests -p "test_union_kline_panel.py"` and `python -m unittest discover -s code/tests -p "test_reconcile_full_master_year.py"`

### Task 4: Make preprocessing a first-class phase with leakage controls

**Dependencies:** Task 1, Task 2, Task 3

**Deliverables:**

- explicit preprocessing module and contract
- tensor building no longer responsible for hidden preprocessing semantics
- label separation and leakage controls documented and tested

- [ ] Extract preprocessing responsibilities from `code/stock_tensor/dataset.py` into a dedicated `code/stock_tensor/preprocess.py` boundary that can be invoked and tested independently.
- [ ] Encode preprocessing stages explicitly: sample filtering, date alignment, missing-value policy, outlier treatment, factor normalization, and label separation.
- [ ] Ensure future returns remain outside the input tensor and are only attached as evaluation targets after preprocessing and split preparation.
- [ ] Add tests that cover leakage-sensitive behavior, especially that time-based evaluation never uses future information during preprocessing.
- [ ] Run: `python -m unittest discover -s code/tests -p "test_preprocess.py"` and `python -m unittest discover -s code/tests -p "test_dataset.py"`

### Task 5: Stabilize tensor-ready factor panels and configurable split strategies

**Dependencies:** Task 2, Task 3, Task 4

**Deliverables:**

- stable factor panel contract for the three formal thesis samples
- explicit tensor input schema
- configurable split support for time-based, stock-based, and hybrid strategies
- thesis default set to time-based split

- [ ] Make `code/data/build_formal_factor_panel.py` produce factor panels that satisfy the tensor input contract and keep factor columns, label columns, and metadata columns explicit.
- [ ] Introduce split configuration support in `code/stock_tensor/config.py` and a dedicated `code/stock_tensor/splits.py` module so split semantics are not inferred implicitly from pipeline code.
- [ ] Keep `time-based` as the thesis default in the formal configs while preserving `stock-based` and `hybrid` as valid configurable system capabilities.
- [ ] Update the pipeline so split metadata, actual coverage windows, and sample counts are carried through to evaluation and outputs.
- [ ] Run: `python -m unittest discover -s code/tests -p "test_formal_factor_panel.py"` and `python -m unittest discover -s code/tests -p "test_split_strategy.py"`

### Task 6: Close the formal CP/Tucker baseline experiment loop

**Dependencies:** Task 4, Task 5

**Deliverables:**

- baseline formal runs for `HS300`, `SZ50`, and `ZZ500`
- explicit `CP` and `Tucker` experiment loop treated as the main thesis method path
- formal run manifests that record sample, split, tensor shape, and model settings

- [ ] Update `code/stock_tensor/pipeline.py`, `code/stock_tensor/models.py`, and `code/main.py` so the formal experiment loop is centered on `CP` and `Tucker` for the three current thesis samples.
- [ ] Keep any extra comparator such as `PCA` secondary and non-blocking, so the branch narrative remains tensor-decomposition-first rather than generic model benchmarking.
- [ ] Ensure the runtime can run each formal sample separately using the converged data contracts and the explicit preprocessing plus split pipeline.
- [ ] Record enough run metadata to reproduce each baseline result without reading free-form logs.
- [ ] Run: `python code/main.py --config code/configs/formal_hs300.yaml`, `python code/main.py --config code/configs/formal_sz50.yaml`, and `python code/main.py --config code/configs/formal_zz500.yaml`

### Task 7: Unify metrics and artifact contracts for thesis and downstream system work

**Dependencies:** Task 5, Task 6

**Deliverables:**

- stable metrics schema
- stable run artifact schema
- output docs that downstream branch work can treat as formal contracts

- [ ] Expand `code/stock_tensor/evaluation.py` so metrics are layered around decomposition quality, pattern discovery and interpretation, and prediction or decision usefulness on held-out data.
- [ ] Update `code/stock_tensor/output.py` so every formal run emits the required machine-readable artifacts and includes split metadata, actual train/eval coverage, and tensor dimensions in `run_manifest.json`.
- [ ] Add `code/outputs/README.md` documenting the artifact contract and expected file meanings.
- [ ] Add tests that fail if required output files or required metric fields disappear or drift.
- [ ] Run: `python -m unittest discover -s code/tests -p "test_output_contract.py"` and `python -m unittest discover -s code/tests -p "test_pipeline.py"`

### Task 8: Finish branch-level validation and handoff

**Dependencies:** Task 1 through Task 7

**Deliverables:**

- branch acceptance review against Branch 1 scope
- proof that current formal samples run separately while long-term A-share coverage remains broader
- clear handoff to later system and thesis branches

- [ ] Re-run targeted data and experiment tests after the final contract changes settle.
- [ ] Run the full suite for this branch scope: `python -m unittest discover -s code/tests`
- [ ] Inspect at least one completed formal output directory per universe and confirm the artifact contract matches `code/outputs/README.md`.
- [ ] Confirm the branch acceptance checklist below is satisfied and capture any remaining follow-up items outside Branch 1.
- [ ] Commit only after tests pass and the plan acceptance checklist is true.

## Branch Acceptance Checklist

Branch 1 is complete only when all statements below are true:

- [ ] formal data directories and field contracts are documented and match actual producers and consumers
- [ ] `all_a_tradable` history and the three formal universe-history files exist as first-class contracts
- [ ] shared kline and full master are described and enforced as one converged formal master route
- [ ] preprocessing is an explicit tested phase rather than hidden tensor-builder behavior
- [ ] formal factor panels produce stable `stock-factor-time` tensor inputs with labels separated from model inputs
- [ ] split strategies are configurable and include `time-based`, `stock-based`, and `hybrid`
- [ ] the thesis default formal configuration is `time-based`
- [ ] `HS300`, `SZ50`, and `ZZ500` run as separate formal samples
- [ ] broader A-share coverage remains preserved at the long-term data-foundation layer
- [ ] `CP` and `Tucker` baseline runs succeed on the formal experiment path
- [ ] metrics and output artifacts are machine-readable, documented, and stable enough for later system and thesis branches

## Notes For Execution

- Prefer the smallest viable refactor that makes the contracts explicit; do not replace working code with a second implementation tree.
- Preserve existing user or parallel-agent work outside the files listed above.
- When in doubt, push semantics into contracts and tests first, then tighten runtime code to satisfy them.
- Branch 1 should end with stable data and experiment contracts, not with web delivery polish.

