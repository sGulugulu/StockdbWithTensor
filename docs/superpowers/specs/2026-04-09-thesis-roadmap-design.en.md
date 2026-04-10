# Thesis Roadmap Design

## Purpose

This design document unifies the overall roadmap for `Tensor-Decomposition-Based Stock Factor Reduction and Pattern Discovery` across research, data, system, and delivery concerns. Its purpose is not to immediately produce an implementation checklist, but to define a stable top-level narrative that answers:

1. what the project is fundamentally trying to prove,
2. what historical issues still need to be cleaned up,
3. what the current main workstreams actually are,
4. how future extension should be preserved without letting scope expand indefinitely.

The roadmap covers both the thesis phase and post-thesis evolution, while keeping the long-term extension boundary conservative.

## Project Positioning

This project is neither just a stock-selection system nor just a paper detached from implementation. A more accurate positioning is:

1. the thesis focuses on tensor-decomposition-based stock factor reduction and pattern discovery,
2. the experiment system is responsible for making the method runnable, verifiable, and repeatable,
3. the web system is responsible for turning experiment capability, result contracts, and query capability into demonstrable and callable interfaces.

The research core is explicitly:

1. build a `stock-factor-time` three-dimensional tensor,
2. use `CP` decomposition and `Tucker` decomposition as the primary method paths,
3. validate method effectiveness on the current formal experiment samples,
4. preserve a broader long-term stock coverage range for future decision-support application.

## Unified Narrative

The overall roadmap uses a dual narrative:

1. **experiment-sample validation**
   - current formal experiments are conducted on representative index-based samples,
   - the goal is to verify whether tensor decomposition can effectively achieve factor reduction and pattern discovery.
2. **future decision application**
   - the system still preserves a broader long-term stock range,
   - once validated, the method should be able to extend to broader decision-support scenarios.

Therefore, the thesis should not be written as a generic stock system report. It should instead be written as:

1. a unified study centered on the `stock-factor-time` tensor,
2. with `CP` / `Tucker` as the core methods,
3. with method validation performed on the current formal experiment samples,
4. and with future broader application treated as a controlled extension path.

## Core Scope Decisions

### 1. Current Formal Experiment Samples

Current formal experiments are centered on:

- `HS300`
- `SZ50`
- `ZZ500`

These three indices are the main current experiment samples. They are not the only long-term stock universes that the system will preserve.

### 2. Long-Term Stock Range

At the system level, the broader A-share range should still be preserved. The architecture must therefore distinguish between:

1. the long-term stock coverage range,
2. the current experiment-sample layer,
3. the current major index-focused experiment configuration.

### 3. Tensor Definition

The unified research object is:

1. first dimension: stock,
2. second dimension: factor,
3. third dimension: time.

This is the core object for the thesis, the experiment pipeline, and result interpretation.

### 4. Primary Methods

The core methods are fixed as:

1. `CP` decomposition,
2. `Tucker` decomposition.

These methods are first factor-reduction and pattern-discovery methods, and only secondarily evaluated through prediction or decision usefulness.

### 5. Reference Basis

The methodological direction is primarily grounded in the PDF references under `./参考文献`, which cover tensor methods, tensor decomposition, financial time series, and stock applications.

## Overall Task Tree Structure

The roadmap uses four top-level branches:

1. **Research Data and Experiment Foundation**
2. **System Implementation and Demonstration**
3. **Thesis Delivery and Defense Materials**
4. **Future Extension and Long-Term Evolution**

Their order reflects practical priority:

1. Research Data and Experiment Foundation
2. System Implementation and Demonstration
3. Thesis Delivery and Defense Materials
4. Future Extension and Long-Term Evolution

## Historical Review Framework

Historical review should use a two-layer structure:

1. first, high-level problem categories,
2. then, key historical decisions and their impacts under each category.

Recommended high-level categories are:

### 1. Research Scope Drift

1. formal experiment sample definitions were not always stable,
2. old sample semantics and current formal semantics diverged,
3. the formal time window had to be explicitly fixed.

### 2. Data Foundation Instability

1. the project moved from “duplicating full data by index” to “shared market master data + universe-history filtering”,
2. shared kline, transitional full master, and formal long-term targets still coexist in traces.

### 3. System Boundary Shifts

1. a Python backend scaffold still exists,
2. the long-term backend direction has shifted to a pure Go API gateway,
3. Python remains the experiment runtime rather than the long-term HTTP gateway.

### 4. Thesis–Engineering Misalignment

1. engineering artifacts, result files, and interface prototypes appeared before the thesis narrative fully stabilized,
2. engineering outputs now have to be reorganized around the tensor-decomposition research question.

## Future Task Tree Conventions

Each top-level branch should be expanded using three layers:

1. past legacy tasks,
2. current main tasks,
3. future extension tasks.

Each node should be described with:

1. goal,
2. dependencies,
3. deliverables.

This makes the roadmap useful both for retrospective cleanup and future planning.

## Branch 1: Research Data and Experiment Foundation

### Past Legacy Tasks

1. formal experiment sample definitions were unstable,
2. the shared-data route and transitional route coexisted without full convergence,
3. preprocessing was not elevated into an explicit phase,
4. long-term stock coverage and current experiment-sample semantics could blur together.

### Current Main Tasks

1. unify formal data directories and field contracts,
2. complete universe-history files,
3. converge shared kline and full master routes,
4. elevate preprocessing into an explicit phase,
5. stabilize formal factor panels and tensor inputs,
6. close the baseline experiment loop,
7. unify metrics and result artifact contracts.

### Future Extension Tasks

1. extend the factor set,
2. expand experiment samples,
3. extend application range,
4. expand the comparative-method framework.

## Experiment Sample Protocol

The experiment layer must distinguish between long-term stock coverage and current experiment configuration.

### Long-Term Coverage

The broader A-share range should still be preserved at the system and data-foundation level.

### Current Main Experiment Samples

Current main experiments focus on:

1. `HS300`
2. `SZ50`
3. `ZZ500`

These three indices should be experimented on separately rather than merged too early into a single pooled sample.

### Split Strategy

The system layer must support configurable split strategies:

1. split ratio configurable,
2. split dimension configurable,
3. support for time-based, stock-based, and hybrid splitting.

### Thesis Default Split

The thesis default main experiment should use **time-based split**. Other split modes remain valid system capabilities and future robustness-experiment directions.

## Preprocessing and Leakage Control

Preprocessing must be treated as an explicit phase between raw formal data and tensor input generation. It must include at least:

1. sample filtering,
2. time and field alignment,
3. missing-value handling,
4. outlier handling,
5. factor direction unification and standardization,
6. label and metadata separation.

Hard constraints:

1. no future information may cross the train/prediction boundary,
2. future-return labels are evaluation targets and do not enter the input tensor.

## Experiment Mainline

The experiment mainline is defined in three layers:

1. **tensor construction**
   - build `stock-factor-time` tensors separately for each current experiment sample.
2. **tensor decomposition**
   - apply `CP` and `Tucker`.
3. **validation**
   - compare decomposition quality, pattern-discovery ability, and prediction or decision effectiveness in later windows.

The thesis must avoid reducing `CP` / `Tucker` to generic return-prediction tools. They are first factor-reduction and pattern-discovery methods.

## Evaluation Framework

The evaluation framework should be layered:

1. **decomposition quality**
   - reconstruction quality, rank behavior, and stability.
2. **pattern discovery and interpretation**
   - factor contribution, stock structure, temporal regimes, and interpretive differences between methods.
3. **prediction or decision usefulness**
   - whether structures extracted during training remain valuable in later windows.

These layers serve both:

1. thesis result chapters,
2. system result pages and API contracts.

## Branch 2: System Implementation and Demonstration

### Past Legacy Tasks

1. HTTP, execution, state, and result responsibilities historically mixed inside Python,
2. configuration semantics were closer to script-level parameters than gateway-level API models,
3. result files existed but were not yet fully stabilized as formal interface contracts.

### Current Main Tasks

1. define the experiment configuration model,
2. build the Go run-control layer,
3. solidify the Python runner primary path,
4. expose formal data query endpoints,
5. expose run-result query endpoints,
6. close the frontend demonstration loop.

### Future Extension Tasks

1. expand split-strategy experiment support,
2. support more flexible experiment-sample configuration,
3. improve run management and event history,
4. strengthen result persistence and retrieval.

## System Boundary

The long-term target architecture is fixed as:

1. a pure Go API gateway,
2. Python as the experiment runner and data-processing runtime,
3. DuckDB as the formal-data query layer and run-archive layer,
4. `code/outputs` as the run-result artifact layer.

### Go Responsibilities

1. provide HTTP services,
2. validate requests,
3. provide a unified response envelope,
4. manage run lifecycle,
5. persist state,
6. archive run information,
7. aggregate DuckDB queries and result-file reads.

### Python Responsibilities

1. parse run requests,
2. generate `submitted_config.yaml`,
3. execute experiments,
4. write outputs under `code/outputs/<run_id>/`.

## API and Run Design

### Unified Response Envelope

The Go gateway should return the following wrapped structure:

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

1. run submission and lifecycle management,
2. run result queries,
3. formal data queries.

### Default Submission Model

`POST /api/runs` is asynchronous by default:

1. validate request,
2. allocate `run_id`,
3. write runtime state,
4. return `202 Accepted`,
5. asynchronously start the Python runner,
6. let the frontend poll status or detail endpoints.

### Experiment Configuration Model

A run request should include at least:

1. config profile,
2. training-sample configuration,
3. prediction-sample configuration,
4. split strategy,
5. model settings,
6. output settings.

Therefore, system design should define the experiment configuration model first, then derive routes from it, not the other way around.

### Source of Truth for State

Go owns the run-state source of truth with two layers:

1. runtime JSON state, for example `var/runs/<run_id>.json`,
2. DuckDB archive tables, for example `gateway_runs` and `gateway_run_events`.

Python does not overwrite the Go-owned state source of truth.

## Branch 3: Thesis Delivery and Defense Materials

### Past Legacy Tasks

1. the thesis risked being diluted by system functionality,
2. engineering results appeared before the academic storyline stabilized,
3. the relationship between current experiment samples and long-term application range was not always clear.

### Current Main Tasks

1. lock the thesis core problem,
2. define the dual structure of “sample validation + prediction/application extension”,
3. write the method section around the tensor object and decomposition methods,
4. write the data and preprocessing section,
5. write the experiment design and result interpretation section,
6. prepare defense materials.

### Future Extension Tasks

1. add robustness-experiment writing,
2. compare more methods,
3. expand application discussion once the system matures further.

## Thesis Narrative

The thesis should use a two-part narrative:

1. **sample validation**
   - validate the tensor-decomposition method on the current main experiment samples.
2. **prediction / application extension**
   - explain how the validated method can be migrated into broader future use scenarios.

The thesis center must remain tensor-decomposition-driven factor reduction and pattern discovery, not a generic stock-system report.

## Branch 4: Future Extension and Long-Term Evolution

### Past Legacy Tasks

1. extension directions were previously too easy to let expand uncontrollably,
2. long-term ideas and current priorities were not always clearly separated.

### Current Main Tasks

1. define a bounded extension map,
2. preserve market-extension hooks,
3. preserve richer factor and method extension space,
4. preserve stronger run-management and result-retention directions.

### Future Extension Tasks

1. add more experiment samples,
2. expand application range,
3. compare more split strategies,
4. gradually evolve the project into a longer-term research platform.

## Dependency Structure

The dependency structure between the four top-level branches should be explicit:

1. **Research Data and Experiment Foundation** is the upstream base.
2. **System Implementation and Demonstration** depends on the experiment foundation.
3. **Thesis Delivery and Defense Materials** depends on both experiment outputs and stabilized system contracts.
4. **Future Extension and Long-Term Evolution** depends on the first three branches reaching basic stability.

Some parallelism is acceptable, but only after upstream contracts stabilize:

1. later data-foundation work can overlap with early system work,
2. later system work can overlap with early thesis packaging.

## Non-Goals

This roadmap does not currently define:

1. a full commercial product roadmap,
2. a multi-user permission system,
3. production monitoring and operations,
4. market-scale expansion plans beyond conservative research-related extensions.

## Success Criteria

This design is successful if it gives the project a stable planning and narrative scaffold such that:

1. the thesis always remains centered on tensor decomposition over the `stock-factor-time` tensor,
2. the system implementation remains centered on experiment configuration, result contracts, and query capability,
3. historical cleanup and future planning can coexist in one roadmap without becoming a diary-like dump,
4. the roadmap can later be decomposed into implementation plans branch by branch.
