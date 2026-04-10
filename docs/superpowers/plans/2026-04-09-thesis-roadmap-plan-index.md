# Thesis Roadmap Implementation Plan Index

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompose the approved thesis roadmap spec into executable branch-level implementation plans, ordered by dependency and practical priority.

**Architecture:** The roadmap spec is too broad for a single implementation plan because it spans four independent but connected branches: data/experiments, system/gateway, thesis delivery, and future extension. This plan index defines the execution order, gating rules, and output files for the branch-specific plans so implementation can proceed without losing the approved top-level structure.

**Tech Stack:** Markdown planning docs, Python experiment pipeline, Go API gateway target architecture, DuckDB, React + Vite

---

## Scope Decision

The approved spec at [2026-04-09-thesis-roadmap-design.md](D:/Personal%20folders/Desktop/宋田琦/毕设/docs/superpowers/specs/2026-04-09-thesis-roadmap-design.md) covers multiple independent subsystems. It should therefore be executed through separate implementation plans rather than one giant plan.

This file is the master plan index. It does **not** replace the branch plans below. It defines:

1. the required branch plans,
2. the dependency order,
3. the gating conditions for starting each branch,
4. the minimum deliverables each branch plan must produce.

## File Structure

**Master index**

- Create: `docs/superpowers/plans/2026-04-09-thesis-roadmap-plan-index.md`

**Required branch plans**

- Create: `docs/superpowers/plans/2026-04-09-data-experiment-foundation-plan.md`
- Create: `docs/superpowers/plans/2026-04-09-system-demo-plan.md`
- Create: `docs/superpowers/plans/2026-04-09-thesis-delivery-plan.md`
- Create: `docs/superpowers/plans/2026-04-09-future-extension-plan.md`

**Referenced spec**

- Read-only input: `docs/superpowers/specs/2026-04-09-thesis-roadmap-design.md`
- Read-only input: `docs/superpowers/specs/2026-04-09-thesis-roadmap-design.en.md`
- Read-only input: `draft.md`
- Read-only input: `plan.md`

## Execution Order

1. Branch 1: Research Data and Experiment Foundation
2. Branch 2: System Implementation and Demonstration
3. Branch 3: Thesis Delivery and Defense Materials
4. Branch 4: Future Extension and Long-Term Evolution

## Gating Rules

### Gate A: Before Branch 1 starts

- The formal experiment scope must already be fixed as `HS300`, `SZ50`, `ZZ500`.
- The long-term stock range must remain broader than the current experiment samples.
- The thesis default split must remain time-based, while the system design still preserves configurable split strategies.

### Gate B: Before Branch 2 starts

- Branch 1 must have a stable definition of:
  - formal directory contracts,
  - universe-history semantics,
  - preprocessing boundaries,
  - tensor input contracts,
  - result artifact contracts.

### Gate C: Before Branch 3 starts

- Branch 1 must produce stable experiment outputs.
- Branch 2 must produce stable result-query and run-lifecycle contracts.

### Gate D: Before Branch 4 starts

- Branches 1-3 must have already formed a stable baseline.
- Branch 4 must not redefine the current thesis core or destabilize current branch deliverables.

## Branch Plan Requirements

### Branch 1: Research Data and Experiment Foundation

**Required focus**

- formal data directory and field contracts
- universe-history completion
- shared kline / full master convergence
- preprocessing as an explicit stage
- factor panel and tensor input stabilization
- baseline experiment loop
- metrics and artifact contract stabilization

**Required outputs**

- a branch plan with executable steps for data and experiment foundations
- explicit treatment of the `stock-factor-time` tensor
- explicit treatment of `CP` / `Tucker`
- explicit treatment of preprocessing and leakage control

### Branch 2: System Implementation and Demonstration

**Required focus**

- experiment configuration model
- Go run-control layer
- Python runner primary path
- formal data query endpoints
- run-result query endpoints
- frontend demo loop

**Required outputs**

- a branch plan that starts from experiment configuration semantics, not just route definitions
- explicit Go/Python/DuckDB/outputs boundaries
- explicit run lifecycle and state source-of-truth rules

### Branch 3: Thesis Delivery and Defense Materials

**Required focus**

- thesis core problem statement
- method section structure
- data and preprocessing writeup
- experiment design and interpretation
- defense materials

**Required outputs**

- a branch plan that organizes the thesis as “sample validation + prediction/application extension”
- explicit mapping between experiment outputs and thesis chapters

### Branch 4: Future Extension and Long-Term Evolution

**Required focus**

- bounded extension map
- market-extension hooks
- factor/model extension space
- stronger run and result retention directions

**Required outputs**

- a branch plan with conservative scope
- no productization sprawl
- no disruption of current thesis priorities

## Task Breakdown

### Task 1: Lock the decomposition strategy

**Files:**
- Modify: `docs/superpowers/plans/2026-04-09-thesis-roadmap-plan-index.md`
- Read: `docs/superpowers/specs/2026-04-09-thesis-roadmap-design.md`

- [ ] **Step 1: Verify the approved roadmap still supports branch decomposition**

Run: `Get-Content -Raw docs\superpowers\specs\2026-04-09-thesis-roadmap-design.md`
Expected: The spec clearly separates the four branches and their dependencies.

- [ ] **Step 2: Confirm branch order**

Expected branch order:

```text
1. Research Data and Experiment Foundation
2. System Implementation and Demonstration
3. Thesis Delivery and Defense Materials
4. Future Extension and Long-Term Evolution
```

- [ ] **Step 3: Keep this plan index as the parent control document**

Expected result: This file remains the control index and does not expand into branch-level implementation details.

### Task 2: Create the Branch 1 plan first

**Files:**
- Create: `docs/superpowers/plans/2026-04-09-data-experiment-foundation-plan.md`
- Read: `draft.md`
- Read: `plan.md`

- [ ] **Step 1: Use the approved spec as source of truth for Branch 1**

Required Branch 1 scope:

```text
- formal data directory contracts
- universe-history completion
- shared kline and full master convergence
- preprocessing and leakage control
- factor panels and tensor inputs
- baseline CP/Tucker experiment loop
- metrics and artifact contracts
```

- [ ] **Step 2: Ensure Branch 1 includes the experiment-sample protocol**

Branch 1 must explicitly preserve:

```text
- long-term broader A-share coverage
- current formal experiment samples: HS300 / SZ50 / ZZ500
- configurable split strategies
- thesis default split: time-based
```

- [ ] **Step 3: Do not start Branch 2 planning until Branch 1 plan exists**

Expected result: `docs/superpowers/plans/2026-04-09-data-experiment-foundation-plan.md` is the first branch plan to be written after this index.

### Task 3: Queue Branch 2 after Branch 1 contracts stabilize

**Files:**
- Create: `docs/superpowers/plans/2026-04-09-system-demo-plan.md`
- Read: `docs/superpowers/specs/2026-04-09-thesis-roadmap-design.md`

- [ ] **Step 1: Treat Branch 1 outputs as prerequisites**

Branch 2 must not proceed without stable definitions for:

```text
- formal directory contracts
- preprocessing boundaries
- tensor input contracts
- run artifact contracts
```

- [ ] **Step 2: Use experiment configuration as the starting point**

Expected result: Branch 2 planning starts from configuration semantics, not from route lists alone.

- [ ] **Step 3: Preserve the target backend architecture**

Required architecture:

```text
- pure Go API gateway
- Python experiment runner
- DuckDB query and archive layer
- code/outputs result artifact layer
```

### Task 4: Queue Branch 3 after outputs and contracts stabilize

**Files:**
- Create: `docs/superpowers/plans/2026-04-09-thesis-delivery-plan.md`
- Read: `docs/superpowers/specs/2026-04-09-thesis-roadmap-design.md`

- [ ] **Step 1: Require stable experiment outputs**

Branch 3 should not start until Branch 1 and Branch 2 can provide:

```text
- stable metrics outputs
- stable factor interpretation outputs
- stable result-query contracts
```

- [ ] **Step 2: Preserve the thesis narrative**

Required thesis framing:

```text
- sample validation
- prediction/application extension
- tensor decomposition as the core research question
```

- [ ] **Step 3: Prevent the thesis plan from redefining the system roadmap**

Expected result: Branch 3 consumes system and experiment outputs; it does not override them.

### Task 5: Queue Branch 4 last and keep it bounded

**Files:**
- Create: `docs/superpowers/plans/2026-04-09-future-extension-plan.md`
- Read: `docs/superpowers/specs/2026-04-09-thesis-roadmap-design.md`

- [ ] **Step 1: Preserve conservative scope**

Branch 4 must remain bounded to:

```text
- market-extension hooks
- richer factor and method space
- stronger experiment management
- longer-term research platform evolution
```

- [ ] **Step 2: Explicitly reject product sprawl**

Expected exclusions:

```text
- full product roadmap
- multi-user permissions
- production ops
- broad commercial platform scope
```

- [ ] **Step 3: Make Branch 4 dependent on Branches 1-3 stability**

Expected result: Branch 4 is always planned and executed after the main thesis branches stabilize.

## Self-Review Checklist

- [ ] The approved roadmap has been decomposed into separate branch plans.
- [ ] This plan index does not pretend to be the full implementation plan for all branches.
- [ ] The branch order matches the approved roadmap priorities.
- [ ] No placeholders such as `TBD` or `TODO` remain.
- [ ] The thesis core remains tensor decomposition over `stock-factor-time`.
- [ ] The target backend remains pure Go gateway plus Python runner.

## Execution Handoff

Plan complete and saved to `docs/superpowers/plans/2026-04-09-thesis-roadmap-plan-index.md`.

Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per branch plan, review between branches
2. Inline Execution - execute planning and implementation inline from this session, branch by branch
