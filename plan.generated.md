# 基于张量分解的股票因子降维与模式发现实施计划

## Goal Description

基于当前 `draft.md`、`README.md`、`毕设.md` 以及 `code/data/formal/` 下的正式数据文档，形成一份可直接执行的实施计划，统一论文、实验系统与 Web 系统的叙事口径，并将项目收敛为一条围绕 `股票-因子-时间` 三维张量与 `CP` / `Tucker` 方法展开的正式研究路线。该计划既要明确正式实验样本、时间窗口、实验协议、评估框架和系统边界，也要给出 formal 数据主链、一级任务树和依赖顺序，避免项目继续在研究口径、数据结构和系统职责上漂移。

## Acceptance Criteria

Following TDD philosophy, each criterion includes positive and negative tests for deterministic verification.

- AC-1: 项目主问题必须统一定义为“基于张量分解的股票因子降维与模式发现”，统一研究对象为 `股票-因子-时间` 三维张量，核心方法固定为 `CP` / `Tucker`。
  - Positive Tests (expected to PASS):
    - `draft.md`、`README.md`、`plan.generated.md` 均明确写出统一研究对象是 `股票-因子-时间` 三维张量。
    - 文档明确 `CP` / `Tucker` 首先用于因子降维与模式发现，而不是普通收益预测器。
  - Negative Tests (expected to FAIL):
    - 任一文档把项目改写成通用量化平台或黑箱收益预测系统。
    - 任一文档不再强调张量分解在论文主线中的核心地位。

- AC-2: 当前正式实验样本必须固定为 `HS300`、`SZ50`、`ZZ500`，并与长期更广的全 A 股覆盖范围明确区分。
  - Positive Tests (expected to PASS):
    - 文档明确三大指数只是当前正式实验样本，而不是系统长期唯一股票范围。
    - 文档明确长期股票范围保留全 A 股，并通过 universe-history 进行历史过滤。
  - Negative Tests (expected to FAIL):
    - 文档把长期股票覆盖范围写死为三个指数。
    - 文档混淆正式实验样本层与长期系统覆盖层。

- AC-3: 正式时间窗口必须固定为 `2015-01-01` 到 `2026-04-01`，并在文档、配置与 formal 数据路线中保持一致。
  - Positive Tests (expected to PASS):
    - `draft.md`、`README.md`、`plan.generated.md` 和 `code/data/formal/README.md` 均明确写出该时间窗口。
    - 文档明确禁止继续使用“当前最新可用日期”作为漂移窗口。
  - Negative Tests (expected to FAIL):
    - 不同文档对正式时间窗口给出不同日期范围。
    - 文档仍用相对时间描述替代固定窗口。

- AC-4: 实验协议必须明确支持按时间、按股票和混合切分，且论文主实验默认采用按时间切分。
  - Positive Tests (expected to PASS):
    - 文档同时写出三类切分策略，并明确论文默认主实验是按时间切分。
    - 文档说明切分策略是系统能力，不等于论文主结果全部同时展开。
  - Negative Tests (expected to FAIL):
    - 文档把单一切分方式写死成系统唯一能力。
    - 文档在默认切分语义上自相矛盾。

- AC-5: 预处理阶段必须被定义为原始 formal 数据与张量输入之间的独立阶段，并明确防止信息泄露。
  - Positive Tests (expected to PASS):
    - 文档明确预处理至少包括样本筛选、时间对齐、缺失值处理、异常值处理、因子方向统一、截面标准化、标签与元信息拆分。
    - 文档明确未来收益标签只用于评估，不进入输入张量，且未来信息不得穿越训练 / 预测边界。
  - Negative Tests (expected to FAIL):
    - 预处理步骤仍然散落在脚本里、没有阶段边界。
    - 文档允许标签进入输入张量或允许未来信息穿越边界。

- AC-6: 评估框架必须固定为分解质量、模式发现与解释、预测或决策有效性三层，并同时服务论文结果与系统输出。
  - Positive Tests (expected to PASS):
    - 文档明确写出三层评估结构及各层关注点。
    - 文档明确这些评估同时服务论文结果章节、系统结果页和 API 输出契约。
  - Negative Tests (expected to FAIL):
    - 文档只保留单一收益指标。
    - 模式发现与解释层被省略。

- AC-7: 系统边界必须固定为“纯 Go API 网关 + Python 实验执行器 + DuckDB 查询层 + `code/outputs` 结果产物层”。
  - Positive Tests (expected to PASS):
    - 文档明确 Go 负责 HTTP 接口、运行状态和查询聚合，Python 负责数据处理、实验执行与结果落盘。
    - 文档明确 DuckDB 是 formal 查询与 catalog 视图层，`code/outputs` 是实验产物层。
  - Negative Tests (expected to FAIL):
    - 文档继续把 Python backend 当作长期正式网关。
    - 文档把 Go 和 Python 的职责重新混在同一层。

- AC-8: API 与运行契约必须明确区分“当前实现”与“长期目标”，尤其是 Go 网关统一响应包裹、异步提交模型和状态真源。
  - Positive Tests (expected to PASS):
    - 文档明确统一响应包裹 `{code, message, data, request_id, timestamp}` 是长期目标契约。
    - 文档明确当前 `POST /api/runs` 的现状返回码与长期目标返回码的区别，并说明 Go 持有双层状态真源。
  - Negative Tests (expected to FAIL):
    - 文档把目标契约误写成当前已经落地的 wire contract。
    - 文档没有区分当前状态与长期目标。

- AC-9: formal 数据底座必须明确为“`baostock -> universes -> master -> financial/reports -> factors -> parquet -> DuckDB -> code/outputs`”的稳定主链。
  - Positive Tests (expected to PASS):
    - 文档完整写出 formal 数据主链及各目录职责。
    - 文档明确 shared all-A master data 与 universe-history 过滤的长期原则。
  - Negative Tests (expected to FAIL):
    - formal 数据主链仍然缺失或职责顺序不清。
    - 文档退回按指数重复保存完整主数据的旧路线。

- AC-10: 总体任务树必须稳定拆分为四个一级分支，并明确依赖顺序与历史复盘框架。
  - Positive Tests (expected to PASS):
    - 文档明确四个一级分支：研究数据与实验底座、系统实现与演示、论文交付与答辩材料、后续扩展与长期演进。
    - 文档明确系统线依赖实验底座，论文线依赖实验结果与稳定合同，并给出至少四类历史复盘问题。
  - Negative Tests (expected to FAIL):
    - 文档不再体现四个一级分支的分工和依赖顺序。
    - 文档没有历史复盘框架，只剩零散任务列表。

## Path Boundaries

### Upper Bound (Maximum Acceptable Scope)

计划完整收口项目的研究口径、正式样本、正式时间窗口、实验协议、评估框架、系统边界、API 运行契约、formal 数据主链、任务树和历史复盘框架，并明确哪些是当前实现、哪些是长期目标。计划内容可直接作为后续 RLCR、实现阶段和论文写作的正式上游约束文档使用。

### Lower Bound (Minimum Acceptable Scope)

至少形成一份结构清晰的计划文件，明确项目主问题、正式样本、固定时间窗口、三类切分策略、预处理边界、三层评估框架、Go/Python/DuckDB/outputs 边界、formal 数据主链和四个一级分支。即使暂不展开实现细节，也必须让计划足以约束后续实现不再继续漂移。

### Allowed Choices

- Can use:
  - `Go` 作为长期正式网关
  - `Python` 作为实验执行与数据处理主路径
  - `DuckDB` 作为查询与 catalog 层
  - `CSV -> Parquet -> DuckDB` 作为正式数据路线
  - `PyTorch` 作为当前 GPU 主路径
- Cannot use:
  - 把项目重新定义成通用量化平台
  - 把长期股票覆盖范围写死成三大指数
  - 把未来收益标签直接并入输入张量
  - 把 Python 与 Go 重新混成同一层长期网关
  - 引入 MySQL 作为当前正式主数据库路线

## Feasibility Hints and Suggestions

### Conceptual Approach

可按“先统一顶层叙事，再收口正式数据主链，最后映射为任务树”的顺序生成计划：

1. 先从 `draft.md` 提炼 Goal Description，锁定主问题、研究对象和方法主线。
2. 再从 `draft.md`、`README.md`、`code/data/formal/README.md`、`DATABASE_DESIGN.md` 提取正式样本、时间窗口、数据主链和系统边界。
3. 最后把这些约束映射为 Acceptance Criteria、里程碑和任务拆分。

### Relevant References

- `draft.md` - 项目研究定位、formal 主链和任务清单的最完整草稿来源
- `README.md` - 当前对外主入口文档，应与计划保持一致
- `code/data/formal/README.md` - formal 数据目录职责与数据路线参考
- `code/data/formal/DATABASE_DESIGN.md` - DuckDB、schema 和查询层设计参考
- `docs/superpowers/specs/2026-04-09-thesis-roadmap-design.md` - 权威设计文档，包含 API 运行契约和四分支结构

## Dependencies and Sequence

### Milestones

1. Milestone 1: 固化研究口径
   - Phase A: 锁定项目主问题、三维张量对象和 `CP` / `Tucker` 方法定位
   - Phase B: 固化正式样本、长期覆盖范围与正式时间窗口

2. Milestone 2: 固化实验协议与评估框架
   - Phase A: 明确切分策略、预处理阶段与信息泄露控制
   - Phase B: 明确三层评估框架及其论文 / 系统输出落点

3. Milestone 3: 固化系统与数据边界
   - Phase A: 收口 Go/Python/DuckDB/outputs 的长期边界与 API 运行契约
   - Phase B: 收口 formal 数据主链与目录职责

4. Milestone 4: 固化总体任务树
   - Phase A: 明确四个一级分支及依赖顺序
   - Phase B: 明确历史复盘框架与后续扩展边界

## Task Breakdown

Each task must include exactly one routing tag:
- `coding`: implemented by Claude
- `analyze`: executed via Codex (`/humanize:ask-codex`)

| Task ID | Description | Target AC | Tag (`coding`/`analyze`) | Depends On |
|---------|-------------|-----------|----------------------------|------------|
| task1 | 统一项目主问题、三维张量对象与 `CP/Tucker` 方法主线 | AC-1 | coding | - |
| task2 | 固化正式实验样本、长期覆盖范围与正式时间窗口 | AC-2, AC-3 | coding | task1 |
| task3 | 明确切分策略、预处理阶段与信息泄露控制 | AC-4, AC-5 | coding | task2 |
| task4 | 固化三层评估框架及论文 / 系统落点 | AC-6 | coding | task3 |
| task5 | 固化 Go/Python/DuckDB/outputs 边界与 API 运行契约 | AC-7, AC-8 | coding | task4 |
| task6 | 固化 formal 数据主链、目录职责与数据路线 | AC-9 | coding | task5 |
| task7 | 固化四个一级分支、依赖顺序与历史复盘框架 | AC-10 | coding | task6 |

## Claude-Codex Deliberation

### Agreements

- 计划必须直接围绕 `draft.md` 的研究主线展开，而不是额外发明新的业务目标。
- formal 数据主链、API 契约和一级任务树应被写成显式约束，而不是分散的说明段落。

### Resolved Disagreements

- 无显著分歧。本次生成计划以现有仓库文档为统一来源，重点在结构化整理而非方案竞争。

### Convergence Status

- Final Status: `converged`

## Pending User Decisions

- DEC-1: 是否用生成的新计划替换现有 `plan.md`
  - Claude Position: 先生成到新文件，复核无误后再决定是否替换现有计划。
  - Codex Position: 无显式分歧。
  - Tradeoff Summary: 直接覆盖现有 `plan.md` 风险更高；先生成新文件可保留回退路径。
  - Decision Status: `PENDING`

## Implementation Notes

### Code Style Requirements

- 实施代码和注释不得包含 `AC-`、`Milestone`、`Phase`、`Task ID` 等计划术语。
- 这些术语仅用于计划文档，不直接进入生产代码或配置文件。
- 代码中应使用与金融张量分解领域匹配的自然命名。

