# Goal Tracker

<!--
This file tracks the ultimate goal, acceptance criteria, and plan evolution.
It prevents goal drift by maintaining a persistent anchor across all rounds.

RULES:
- IMMUTABLE SECTION: Do not modify after initialization
- MUTABLE SECTION: Update each round, but document all changes
- Every task must be in one of: Active, Completed, or Deferred
- Deferred items require explicit justification
-->

## IMMUTABLE SECTION
<!-- Do not modify after initialization -->

### Ultimate Goal

本计划基于当前 `draft.md` 生成，目标是把项目收敛为一条可执行、可验证、可交付的正式实施路线。整个项目必须始终围绕同一个研究主线展开：

1. 统一研究对象是 `股票 - 因子 - 时间` 三维张量。
2. 统一核心方法是 `CP` 与 `Tucker` 张量分解。
3. 统一系统边界是 `Go API 网关 + Python 数据与实验执行 + DuckDB 查询层 + Parquet/CSV 数据底座`。
4. 统一实验主线是“formal 数据构建 -> 张量构造 -> 分解实验 -> 评估比较 -> 结果落盘 -> 查询展示”。
5. 统一论文叙事是“在当前正式样本上验证方法有效性，并将实验结果沉淀为论文结论与系统展示能力”。

与上一版相比，这次计划还必须把 `draft.md` 中新增的 `Baostock 抓取层改造计划` 正式纳入执行约束。也就是说，计划不仅要覆盖 `adjust_factor / dividend / macro` 的扩展任务，还要明确：

1. 哪些外部参考项目只可吸收优点，不可照搬骨架。
2. 当前仓库已有的 `canonical root -> manifest -> DuckDB catalog -> formal outputs` 主链不能被外部参考带偏。
3. 抓取层应继续沿“公共能力模块化、dataset 化、schema 约束化、可恢复化”的方向收口。
4. 项目完成后必须继续完成实验、Typst 论文写作、附件整理和正式提交物导出。

### Acceptance Criteria
<!-- Each criterion must be independently verifiable -->
<!-- Claude must extract or define these in Round 0 -->

- AC-T1: 研究主线必须稳定锚定为 `股票 - 因子 - 时间` 三维张量上的 `CP / Tucker` 因子降维与模式发现问题。
  - Pass Signal:
    - `draft.md`、`plan.md`、相关正式文档都不再把项目写成普通选股网站、通用量化平台或黑箱收益预测器。
  - Fail Signal:
    - 任一关键文档改写主问题、弱化张量分解中心地位或把收益预测准确率写成唯一目标。

- AC-T2: formal 数据、实验样本和系统边界必须稳定，包括正式时间窗口、长期股票覆盖范围以及 `Go + Python + DuckDB + Parquet/CSV` 架构边界。
  - Pass Signal:
    - 文档持续固定 `2015-01-01` 到 `2026-04-01` 正式窗口，明确全 A 股长期覆盖和 `HS300 / SZ50 / ZZ500` 当前正式样本，并保持长期架构边界不漂移。
  - Fail Signal:
    - 时间窗口继续漂移，样本边界被混淆，或重新引入 Python 长期网关 / MySQL 主链。

- AC-T3: 实验协议必须闭环，显式定义预处理、切分、泄漏控制、三层评估框架和结果契约。
  - Pass Signal:
    - 文档与后续实现明确 split-aware 预处理、按时间默认切分、三层评估结构，以及 `metrics / selection / factor_summary / time_regimes` 输出契约。
  - Fail Signal:
    - 预处理与切分规则散落、未来信息泄漏、评估层只剩单一收益指标或结果产物无法沉淀到查询层与论文。

- AC-T4: Baostock 扩展必须形成 `公共能力 -> raw 抓取 -> manifest -> DuckDB raw/coverage view` 的可恢复闭环。
  - Pass Signal:
    - `baostock_common.py`、`adjust_factor/dividend/macro` 抓取脚本、manifest 扩展、DuckDB raw/coverage views 与对应测试都进入实现并可验证。
  - Fail Signal:
    - raw 数据无法 resume、无法注册、无法覆盖查询，或扩展脱离现有 canonical root 主链。

- AC-T5: Baostock 抓取层改造必须明确“吸收什么 / 放弃什么”，并补齐 dataset 规格、输入校验、最小字段策略和统一 schema。
  - Pass Signal:
    - 外部参考只作为接口覆盖、校验、字段裁剪和轻量标准化参考；抓取层具备 dataset 级规格、统一校验与 schema。
  - Fail Signal:
    - 直接照搬外部项目骨架、重新引入 MySQL/单票导出式 ad hoc 组织，或继续让零散脚本各自定义规则。

- AC-T6: `adjust_factor` 与 `dividend` 必须优先提升为解释层可直接消费的正式资产，`macro`、财务 PIT 和 supplement 扩展按后续阶段推进。
  - Pass Signal:
    - `adjust_factor_daily.csv`、`dividend_events.csv`、相关 DuckDB views 与测试进入主线；宏观与 PIT 路线被保留但不抢占当前主线资源。
  - Fail Signal:
    - 只抓 raw 不做面板提升，或一开始就把所有宏观字段并入 `full_master` / 张量输入。

- AC-T7: 项目完成后必须继续完成正式实验、Typst 论文写作与提交物整理。
  - Pass Signal:
    - 计划和后续执行都覆盖实验结果沉淀、Typst 论文、文献综述、翻译、附录、附件清单与 PDF/Word 导出。
  - Fail Signal:
    - 计划只停留在代码实现，不覆盖实验和最终论文交付。

---

## MUTABLE SECTION
<!-- Update each round with justification for changes -->

### Plan Version: 1 (Updated: Round 0)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | - | - |
| 0 | 将 tracker 的 Immutable AC 收敛为 7 条可追踪的聚合标准 | 原计划 AC 数量较多，Round 0 tracker 更需要稳定追踪与防漂移 | AC-T1 至 AC-T7 成为后续 round 的固定验收锚点 |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| 固化研究主问题、样本边界、时间窗口与系统边界 | AC-T1, AC-T2 | pending | coding | claude | 对应 `task-01`，作为所有后续任务的口径锚点 |
| 固化外部参考的吸收/放弃边界 | AC-T5 | pending | analyze | codex | 对应 `task-02`，防止抓取层被外部骨架带偏 |
| 审核 formal 目录、DuckDB 设计与 manifest 影响面 | AC-T2, AC-T4, AC-T5 | pending | analyze | codex | 对应 `task-03`，为 aux 数据接入提供影响分析 |
| 抽出 `baostock_common.py` 并统一 session / relogin / resume 语义 | AC-T4, AC-T5 | pending | coding | claude | 对应 `task-04` |
| 设计 `adjust_factor / dividend / macro` 的 dataset 规格与输入校验规则 | AC-T5 | pending | analyze | codex | 对应 `task-05` |
| 实现 `adjust_factor`、`dividend`、`macro` 抓取脚本与输出目录 | AC-T4, AC-T5, AC-T6 | pending | coding | claude | 对应 `task-06`、`task-07`、`task-08` |
| 扩展 canonical root 文档、manifest 与 DuckDB raw/coverage views | AC-T4, AC-T5 | pending | coding | claude | 对应 `task-09`、`task-10` |
| 构建 `adjust_factor_daily.csv` 与 `dividend_events.csv` | AC-T6 | pending | coding | claude | 对应 `task-11`、`task-12` |
| 设计 `macro`、财务 PIT、macro aligned panel 的后续接口边界 | AC-T6 | pending | analyze | codex | 对应 `task-13` |
| 将新增数据产物接入实验输入/输出和 Go 查询读路径 | AC-T3, AC-T4, AC-T6 | pending | coding | claude | 对应 `task-14` |
| 补齐 common / fetch / catalog / panel 构建测试 | AC-T4, AC-T6 | pending | coding | claude | 对应 `task-15` |
| 设计 Typst 论文骨架并完成实验后论文交付 | AC-T7 | pending | analyze | codex | 对应 `task-16`，后续正文与提交物整理对应 `task-17` |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|

### Open Issues
<!-- Issues discovered during implementation -->
| Issue | Discovered Round | Blocking AC | Resolution Path |
|-------|-----------------|-------------|-----------------|
| `bitlesson-selector` 命令在当前环境中不可用 | 0 | - | 本轮按 `NONE` 处理，并在 summary 的 `BitLesson Delta` 中记录；若后续环境补齐该命令，再恢复正式选择流程 |
