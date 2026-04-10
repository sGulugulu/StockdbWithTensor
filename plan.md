# 基于张量分解的股票因子降维与模式发现实施计划

## Goal Description

基于当前 [draft.md](draft.md)、[毕设.md](毕设.md)、[README.md](README.md) 以及 `code/data/formal/` 下各级 `README.md`、`DATABASE_DESIGN.md` 已确认的信息，本计划的目标是把项目收敛为一条与论文口径一致、同时具备明确系统边界和后续实施顺序的正式研究路线。

本项目的核心不是泛化成普通量化平台，而是围绕以下主问题展开：

1. 以 `股票-因子-时间` 三维张量作为统一研究对象。
2. 以 `CP` / `Tucker` 作为主要方法路径。
3. 在当前正式实验样本上完成因子降维与模式发现验证。
4. 将实验系统、结果产物和 Web 查询能力统一到同一条研究叙事下。
5. 在保留更广股票覆盖范围的前提下，为未来决策应用留口。

## Acceptance Criteria

- AC-1: 论文、草稿与正式计划必须统一把项目主问题定义为“基于张量分解的股票因子降维与模式发现”，而不是普通收益预测或通用选股系统。
  - Positive Tests (expected to PASS):
    - `draft.md`、`plan.md`、相关文档都明确写出统一研究对象是 `股票-因子-时间` 三维张量。
    - 方法章节和系统设计都把 `CP` / `Tucker` 作为主方法路径。
  - Negative Tests (expected to FAIL):
    - 文档把项目主线改写成泛化的黑箱预测系统。
    - 文档不再强调张量分解的核心地位。

- AC-2: 当前正式实验样本固定为 `HS300`、`SZ50`、`ZZ500`，但系统长期股票覆盖范围不得被写死为这三个指数。
  - Positive Tests (expected to PASS):
    - 文档明确这三个指数是当前正式实验样本。
    - 文档同时明确系统长期仍保留更广 A 股覆盖范围。
  - Negative Tests (expected to FAIL):
    - 将三个指数误写为系统长期唯一股票范围。
    - 将长期股票覆盖范围与当前实验样本层混为一谈。

- AC-3: 正式时间窗口固定为 `2015-01-01` 到 `2026-04-01`，并在文档、配置和数据路线中保持一致。
  - Positive Tests (expected to PASS):
    - `draft.md`、`plan.md` 和 formal 文档都明确固定这一窗口。
    - formal 配置与数据规划围绕这个固定窗口组织。
  - Negative Tests (expected to FAIL):
    - 文档继续使用“当前最新可用日期”作为漂移窗口。
    - 不同文档对正式窗口给出不同时间范围。

- AC-4: 实验层必须支持可配置切分策略，但论文主实验默认采用按时间切分。
  - Positive Tests (expected to PASS):
    - 文档明确支持按时间、按股票、混合切分。
    - 文档明确论文默认主实验采用按时间切分。
  - Negative Tests (expected to FAIL):
    - 将单一切分方式写死为系统唯一能力。
    - 论文主实验与系统默认切分语义互相冲突。

- AC-5: 数据预处理必须被提升为原始 formal 数据与张量输入之间的独立阶段，并明确防止信息泄露。
  - Positive Tests (expected to PASS):
    - 文档明确预处理包括样本筛选、时间对齐、缺失处理、异常值处理、标准化、标签拆分。
    - 文档明确未来收益标签只作为评价目标，不进入输入张量。
  - Negative Tests (expected to FAIL):
    - 预处理步骤继续散落在脚本中、没有阶段边界。
    - 未来信息可以穿越训练 / 预测边界。

- AC-6: 评估框架必须分为分解质量、模式发现与解释、预测或决策有效性三层，并同时服务论文与系统输出。
  - Positive Tests (expected to PASS):
    - 文档明确三层评价结构。
    - 文档明确这些评价既服务论文结果章节，也服务系统结果页与 API 合同。
  - Negative Tests (expected to FAIL):
    - 评价只剩单一收益指标。
    - 模式发现与解释层被完全省略。

- AC-7: 系统边界必须固定为“纯 Go API 网关 + Python 实验执行器 + DuckDB 查询层 + `code/outputs` 结果产物层”。
  - Positive Tests (expected to PASS):
    - 文档明确 Go 负责 HTTP、状态、归档和查询聚合。
    - 文档明确 Python 负责 run 请求解析、配置展开、实验执行和结果落盘。
    - 文档明确 DuckDB 承载 formal 查询与 run 归档。
  - Negative Tests (expected to FAIL):
    - 继续把 Python backend 当作长期正式网关。
    - 让 Go 直接重写实验逻辑或让 Python 继续混管 HTTP 与实验执行。

- AC-8: Go 网关的运行设计必须固定为统一响应包裹结构、异步提交模型和双层状态真源。
  - Positive Tests (expected to PASS):
    - 文档明确 `{code, message, data, request_id, timestamp}` 包裹结构。
    - `POST /api/runs` 默认异步，返回 `202 Accepted` 和 `run_id`。
    - Go 持有运行态 JSON 和 DuckDB 归档双层状态真源。
  - Negative Tests (expected to FAIL):
    - 返回结构仍然是裸数组或裸对象。
    - 任务状态继续由 Python 单独持有或只存在内存里。

- AC-9: 正式数据底座必须继续采用“全 A 主数据 + 独立 universe 历史 + 财务/报告分表 + `CSV -> Parquet -> DuckDB`”的结构。
  - Positive Tests (expected to PASS):
    - 文档中明确 `universes/`、`master/`、`factors/`、`financial/`、`reports/`、`parquet/`、`baostock/` 的职责。
    - DuckDB 继续作为本地分析型查询目录。
  - Negative Tests (expected to FAIL):
    - 按指数重复存完整市场主数据。
    - 让 Web 查询层直接依赖原始大型 CSV 扫描。

- AC-10: 总体路线图必须稳定拆成四个一级分支，并保持依赖顺序清晰。
  - Positive Tests (expected to PASS):
    - 文档保留四个一级分支：研究数据与实验底座、系统实现与演示、论文交付与答辩材料、后续扩展与长期演进。
    - 文档明确系统线依赖实验底座，论文线依赖实验结果与系统稳定合同。
  - Negative Tests (expected to FAIL):
    - 把所有任务再次混成一条没有边界的大路线。
    - 不再能看出各分支的上下游关系。

## Path Boundaries

### Upper Bound (Maximum Scope)

- 正式文档、配置、数据目录、输出合同和 Web 查询边界全部统一到当前 thesis 口径。
- 全 A 主数据、财务表、报告表、universe 历史、因子面板、Parquet 镜像和 DuckDB catalog 均形成稳定路线。
- Go 网关完整接管 HTTP 服务、运行态、归档、formal 数据查询和运行结果查询。
- Python runner 成为唯一实验执行主路径，并与 `code/outputs` 合同稳定衔接。
- 完成 `HS300`、`SZ50`、`ZZ500` 三个正式股票池上的张量分解实验、候选股输出和解释结果。

### Lower Bound (Minimum Scope)

- `draft.md` 与 `plan.md` 必须把主问题、三维张量对象、`CP/Tucker` 方法、实验样本边界、切分策略、预处理阶段、系统边界和一级分支结构讲清楚。
- formal 数据路线仍然维持为 `CSV -> Parquet -> DuckDB` 和共享主数据 + universe 历史结构。
- 系统长期覆盖范围与当前正式实验样本之间的区分必须明确。

### Allowed Choices

- 后端固定为纯 `Go` API 网关。
- 前端保持 `React + Vite`。
- Python 保持实验执行和数据处理主路径。
- GPU 主路径使用 `PyTorch`。
- 切分策略允许时间、股票、混合三种模式，但论文主实验默认按时间切分。
- 长期可保留更广股票覆盖范围和 `us_equity` 扩展入口，但当前不将其扩展成新的正式研究主线。

## Dependencies and Sequence

### Milestone 1: 固化研究口径

1. 固化论文主问题、统一研究对象和主要方法。
2. 固化当前正式实验样本与长期股票覆盖范围之间的区分。
3. 固化正式时间窗口。

### Milestone 2: 固化实验协议

1. 固化实验样本协议。
2. 固化切分策略能力边界与论文默认切分。
3. 固化预处理阶段与信息泄露控制原则。

### Milestone 3: 固化系统边界

1. 固化 Go 网关、Python runner、DuckDB 与 outputs 的职责边界。
2. 固化 Go API 的响应结构、默认提交模型和状态真源。
3. 固化实验配置模型与查询接口语义。

### Milestone 4: 固化总体任务树

1. 保持四个一级分支稳定。
2. 明确历史复盘框架。
3. 明确依赖关系与未来保守扩展边界。

## Feasibility Hints

- 当前 `draft.md` 已经足够作为 branch planning 和 RLCR 的上游草稿，不需要再先回到泛化 brainstorm。
- 系统线应从实验配置模型出发，而不是先从路由列表出发。
- 论文线不能丢掉系统与实验结果，但也不能被系统功能叙事反客为主。
- 若后续继续迭代 `draft.md`，应优先保证研究主线和系统边界不发生新的漂移。

## Implementation Notes

- 不要再把项目主问题写成普通收益预测或通用量化平台。
- 不要把长期股票覆盖范围写死成当前三个正式实验指数。
- 不要把未来收益标签写入输入张量。
- 不要把 Python 实验执行层和 Go 网关重新混在同一个 HTTP 进程里。
- 不要让正式数据底座退回到按指数重复存市场主数据的旧路线。
- 代码实现中不要把计划术语如 `AC-`、`Milestone` 直接写进生产代码。
