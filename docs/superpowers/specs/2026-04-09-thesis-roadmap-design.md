# Thesis Roadmap Design

## Purpose

This design unifies the thesis roadmap for `基于张量分解的股票因子降维与模式发现` across research, data, system, and delivery concerns. The goal is not to produce an implementation checklist yet, but to define a stable top-level structure that explains:

1. what the project is fundamentally trying to prove,
2. what historical problems must be cleaned up,
3. what the current main workstreams are,
4. how future extensions should remain bounded.

The roadmap covers both the thesis period and post-thesis evolution, but keeps the extension boundary conservative.

## Project Positioning

This project is not just a stock selection system, and it is not just a paper detached from implementation. Its core positioning is:

- the thesis focuses on tensor-decomposition-based factor reduction and pattern discovery,
- the experiment system validates and externalizes the method,
- the web system makes the experiment and result contracts queryable and demonstrable.

The research core is:

- build a three-dimensional tensor with `stock-factor-time`,
- use `CP` decomposition and `Tucker` decomposition as the main methodological paths,
- verify method effectiveness on representative index-based experiment samples,
- preserve a broader long-term stock universe for future decision support.

## Unified Narrative

The roadmap adopts a dual narrative:

1. **training-sample validation**
   - the current formal experiments use representative index-based samples,
   - the purpose is to verify whether tensor decomposition can achieve meaningful factor reduction and pattern discovery.
2. **future decision application**
   - the long-term data range still preserves the broader A-share universe,
   - the system should later support decision use beyond the current experiment samples.

The thesis should therefore be written as:

- a method paper centered on tensor decomposition over `stock-factor-time`,
- with experiment validation on the current sample universes,
- and with a clearly bounded application extension path.

## Core Scope Decisions

### Formal Experiment Scope

The current formal experiment samples are centered on:

- `HS300`
- `SZ50`
- `ZZ500`

These are not the only long-term supported stock universes. They are the current main experiment samples.

### Long-Term Stock Range

The long-term system-level stock range should still preserve the broader A-share universe. The architecture must therefore distinguish:

- the long-term stock coverage range,
- the current experiment sample layer,
- the current main index-focused experiment configuration.

### Tensor Definition

The unified tensor object is:

- stock dimension
- factor dimension
- time dimension

This is the core research object for the thesis and the main experiment pipeline.

### Primary Methods

The main methods are:

- `CP` decomposition
- `Tucker` decomposition

These are first pattern-discovery and factor-reduction methods, and only secondarily evaluated through prediction or decision effectiveness.

### Reference Basis

The method direction is aligned with the literature under `./参考文献`, which currently consists primarily of PDF references related to tensor methods, tensor decomposition, financial time series, and stock applications.

## Task Tree Structure

The roadmap should use four top-level branches:

1. **Research Data and Experiment Foundation**
2. **System Implementation and Demonstration**
3. **Thesis Delivery and Defense Materials**
4. **Future Extension and Long-Term Evolution**

The branch order should reflect practical priority:

1. Research Data and Experiment Foundation
2. System Implementation and Demonstration
3. Thesis Delivery and Defense Materials
4. Future Extension and Long-Term Evolution

## Historical Review Framework

Historical review should be written in two layers:

1. high-level problem categories,
2. concrete historical decisions and their effects.

The recommended categories are:

### 1. Research Scope Drift

- experiment universes were not always consistently defined,
- old sample semantics and current formal semantics diverged,
- the formal window had to be explicitly fixed.

### 2. Data Foundation Instability

- the project moved from duplicated per-index storage thinking to shared market data plus universe history filtering,
- multiple intermediate routes now coexist, including shared kline, transitional full master, and formal long-term targets.

### 3. System Boundary Shifts

- the Python backend scaffold exists,
- the long-term backend direction has shifted to a pure Go API gateway,
- Python remains the experiment runtime rather than the long-term HTTP gateway.

### 4. Thesis and Engineering Misalignment

- engineering outputs and files existed before the academic narrative fully stabilized,
- the thesis now needs to explicitly reorganize those results around the tensor-decomposition research question.

## Future Task Tree Conventions

Each top-level branch should be expanded with three layers:

1. **past legacy tasks**
2. **current main tasks**
3. **future extension tasks**

Each node under those layers should be documented using:

- goal,
- dependencies,
- deliverables.

This keeps the roadmap useful both for retrospective cleanup and forward planning.

## Branch 1: Research Data and Experiment Foundation

### Past Legacy Tasks

- formal experiment universes were previously unstable,
- the shared data route and transitional data route coexisted without a clear hierarchy,
- preprocessing was not always treated as its own explicit stage,
- long-term stock range and current experiment sample semantics could blur together.

### Current Main Tasks

1. unify the formal data directories and field contracts,
2. complete universe-history files,
3. converge shared kline and full master routes,
4. elevate preprocessing into an explicit phase,
5. stabilize formal factor panels and tensor inputs,
6. close the baseline experiment loop,
7. unify metrics and result artifact contracts.

### Future Extension Tasks

1. extend the factor set,
2. expand experiment samples,
3. extend application ranges,
4. expand comparative method evaluation.

## Experiment Sample Protocol

The experiment layer should distinguish between long-term stock coverage and current experiment setup.

### Long-Term Coverage

The broader A-share range should still be preserved at the system and data-foundation level.

### Current Main Experiment Samples

Current formal experiments are centered on:

- `HS300`
- `SZ50`
- `ZZ500`

These experiments should be run separately rather than prematurely merged into one combined sample.

### Split Strategy

The system should support configurable split strategies:

- ratio configurable,
- axis configurable,
- time-based / stock-based / hybrid split modes supported.

### Thesis Default Split

The thesis default main experiment should use **time-based split**. Other split strategies remain valid system capabilities and future robustness experiments.

## Preprocessing and Leakage Control

Preprocessing should be treated as an explicit phase between raw formal data and tensor input generation.

It should include:

1. sample filtering,
2. time and field alignment,
3. missing-value handling,
4. outlier handling,
5. factor direction normalization and standardization,
6. label and metadata separation.

The hard rule is:

- no future information may leak across the training/prediction boundary,
- future return labels are evaluation targets and do not enter the input tensor.

## Experiment Mainline

The experiment mainline should be described in three layers:

1. **tensor construction**
   - build `stock-factor-time` tensors per experiment sample.
2. **decomposition**
   - apply `CP` and `Tucker`.
3. **validation**
   - compare decomposition quality, pattern discovery quality, and downstream predictive or decision usefulness.

The thesis should avoid reducing `CP` and `Tucker` to mere predictive tools. They are primarily factor-reduction and pattern-discovery methods.

## Evaluation Framework

Evaluation should be layered:

1. **decomposition quality**
   - reconstruction quality and rank behavior.
2. **pattern discovery and interpretation**
   - factor contribution, stock structure, temporal regimes, explanatory differences between methods.
3. **prediction or decision usefulness**
   - whether structures extracted on the training part remain useful on the later part.

This framework should serve both:

- the thesis result chapters,
- the system result pages and API contracts.

## Branch 2: System Implementation and Demonstration

### Past Legacy Tasks

- HTTP, execution, state, and result responsibilities historically mixed in Python,
- configuration semantics were closer to script-level operation than gateway-grade API modeling,
- result files existed but were not fully stabilized as formal API contracts.

### Current Main Tasks

1. define the experiment configuration model,
2. build the Go run-control layer,
3. define the Python runner primary path,
4. expose formal data query endpoints,
5. expose run-result query endpoints,
6. close the frontend demonstration loop.

### Future Extension Tasks

1. broaden split-strategy experimentation support,
2. support richer experiment-sample configuration,
3. improve run management and event history,
4. strengthen result persistence and retrieval.

## System Boundary

The target backend architecture is:

- a pure Go API gateway,
- Python as experiment runner and data-processing runtime,
- DuckDB for formal data querying and run archival,
- `code/outputs` as the run-result artifact layer.

### Go Responsibilities

- HTTP service,
- request validation,
- unified response structure,
- run lifecycle management,
- state persistence,
- run archival,
- query aggregation from DuckDB and result files.

### Python Responsibilities

- parse run requests,
- generate `submitted_config.yaml`,
- execute experiments,
- write outputs under `code/outputs/<run_id>/`.

## API and Run Design

### Unified Response Envelope

The gateway should return a wrapped response:

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "req_xxx",
  "timestamp": "2026-04-09T00:00:00Z"
}
```

### Route Groups

Recommended route groups:

1. run submission and lifecycle
2. run result queries
3. formal data queries

### Default Submission Model

`POST /api/runs` should be asynchronous by default:

- validate request,
- allocate `run_id`,
- persist run state,
- return `202 Accepted`,
- start Python runner asynchronously,
- let the frontend poll status or detail endpoints.

### Experiment Configuration Model

A run request should model at least:

- config profile,
- training sample configuration,
- prediction sample configuration,
- split strategy,
- model settings,
- output settings.

This is the preferred design starting point, rather than defining routes first and experiment semantics later.

### State Source of Truth

Go should own the run state source of truth through:

- runtime JSON state, for example `var/runs/<run_id>.json`,
- DuckDB archival tables, for example `gateway_runs` and `gateway_run_events`.

Python should not overwrite the Go-owned state source of truth.

## Branch 3: Thesis Delivery and Defense Materials

### Past Legacy Tasks

- the thesis question risked becoming too system-centric,
- engineering outputs existed before the academic storyline fully stabilized,
- sample-range semantics and long-term application semantics were not always clearly distinguished.

### Current Main Tasks

1. lock the thesis core problem statement,
2. define the dual structure of validation and application,
3. write the method section around the tensor object and decomposition methods,
4. write the data and preprocessing section,
5. write the experiment and result interpretation section,
6. prepare defense materials.

### Future Extension Tasks

1. add robustness experiment writeups,
2. compare more methods,
3. expand application discussion when the system matures further.

## Thesis Narrative

The thesis should be organized as:

1. **sample-based validation**
   - validate the tensor-decomposition method on the current main experiment samples.
2. **prediction/application extension**
   - explain how the validated method can be carried into broader future use.

The thesis should not collapse into a generic stock system report. Its center remains tensor-based factor reduction and pattern discovery.

## Branch 4: Future Extension and Long-Term Evolution

### Past Legacy Tasks

- extension directions were previously too easy to let expand without boundary,
- future ideas could blur into current implementation priorities.

### Current Main Tasks

1. keep a bounded extension map,
2. preserve market-extension hooks,
3. preserve richer factor and method extension space,
4. preserve stronger run and result management directions.

### Future Extension Tasks

1. add more experiment samples,
2. extend application ranges,
3. evaluate more split strategies,
4. evolve into a more durable research platform.

## Dependency Structure

The branch dependencies should be explicit:

1. **Research Data and Experiment Foundation** is the upstream base.
2. **System Implementation and Demonstration** depends on that base.
3. **Thesis Delivery and Defense Materials** depends on both experiment outputs and system-stabilized contracts.
4. **Future Extension and Long-Term Evolution** depends on the first three branches reaching stability.

Parallel work is possible, but only after the upstream contracts are stable enough:

- late data-foundation work can overlap with early system work,
- late system work can overlap with early thesis packaging.

## Non-Goals

This roadmap does not define:

- a full commercial product roadmap,
- multi-user permissions,
- production operations and monitoring,
- complete market-by-market rollout plans beyond conservative research-linked extensions.

## Success Criteria For This Design

This design is successful if it gives the project a stable narrative and planning scaffold where:

1. the thesis remains centered on tensor decomposition over `stock-factor-time`,
2. the system work remains aligned with the experiment and result contracts,
3. historical cleanup and future planning can live in one roadmap without becoming a vague diary,
4. the roadmap can later be turned into implementation plans branch by branch.
