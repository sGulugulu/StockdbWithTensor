# 基于张量分解的股票因子降维与模式发现执行计划（生成稿 v2）

## Goal Description

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

本计划不是泛化的软件需求文档，而是研究型毕设项目的执行蓝图。它既要约束代码和数据路线，也要覆盖实验、论文、答辩材料与最终提交物。

## Acceptance Criteria

遵循 TDD 风格，每条 AC 都给出正向与反向验证，便于后续实现时做最小充分校验。

- AC-1: 项目主问题、研究对象和方法口径必须统一，不得漂移成普通选股系统或纯收益预测器。
  - Positive Tests (expected to PASS):
    - `draft.md`、`plan.generated.v2.md` 与后续正式 `plan.md` 都明确写出统一研究对象是 `股票 - 因子 - 时间` 三维张量。
    - 文档明确 `CP` 与 `Tucker` 是当前论文与实验的固定核心方法。
    - 文档明确主问题是因子降维与模式发现，预测或决策价值属于后续验证层。
  - Negative Tests (expected to FAIL):
    - 文档把项目改写为通用量化平台、选股网站或黑箱预测系统。
    - 文档不再强调张量分解的主线地位。
    - 文档把预测收益率准确率当成唯一目标。

- AC-2: 数据边界必须稳定，包括正式时间窗口、长期股票覆盖范围、当前 formal 样本池与重点实验指数三层边界。
  - Positive Tests (expected to PASS):
    - 文档明确正式时间窗口固定为 `2015-01-01` 到 `2026-04-01`。
    - 文档明确长期股票覆盖范围保留全 A 股。
    - 文档明确当前重点实验指数为 `HS300`、`SZ50`、`ZZ500`，但不把它们写死成系统唯一股票池。
  - Negative Tests (expected to FAIL):
    - 文档继续使用“当前最新可用日期”作为滚动边界。
    - 文档把全 A 股覆盖范围与当前实验样本混为一谈。
    - 文档把三个指数误写成系统长期唯一股票范围。

- AC-3: 系统边界必须固定为 `Go + Python + DuckDB + Parquet/CSV`，并明确各自职责，不引入平行主链。
  - Positive Tests (expected to PASS):
    - 文档明确 Go 负责 HTTP 接口、请求校验、运行状态管理、DuckDB/输出读取与实验调度。
    - 文档明确 Python 负责 formal 数据处理、张量构造、`CP/Tucker` 实验执行与结果文件落盘。
    - 文档明确 DuckDB 负责 catalog、formal 查询视图与结构化数据读取。
    - 文档明确 `Parquet + DuckDB` 是主要数据层，不引入 MySQL 作为新主链。
  - Negative Tests (expected to FAIL):
    - 将 Python backend 当作长期正式网关。
    - 让 Go 重写实验内核或让 Python 继续混管 HTTP 与实验执行。
    - 新增 MySQL 或平行数据库工程作为主路径。

- AC-4: 数据预处理、切分策略和泄漏控制必须被提升为显式阶段，形成 split-aware 的一致实验协议。
  - Positive Tests (expected to PASS):
    - 文档明确预处理阶段至少包括样本筛选、时间对齐、字段清洗、缺失值处理、异常值处理、因子方向统一、标准化、标签与元信息分离。
    - 文档明确支持按时间切分、按股票切分、混合切分，且比例与维度可配置。
    - 文档明确论文主实验默认按时间切分。
    - 文档明确未来收益标签只用于评估，不进入输入张量。
  - Negative Tests (expected to FAIL):
    - 把切分策略写死成一种方式。
    - 预处理逻辑继续散落在实验脚本内部，没有阶段边界。
    - 未来信息可以穿越训练/预测边界。

- AC-5: 实验主线与评估框架必须闭环，且输出结果要能同时服务论文、系统和后续查询。
  - Positive Tests (expected to PASS):
    - 文档明确实验主线包括张量构建、张量分解、评估与比较三层。
    - 文档明确评估体系包括分解质量、模式发现与解释、预测/排序/决策有效性三层。
    - 文档明确 Python 输出 `metrics`、`selection`、`factor_summary`、`time_regimes` 等结果文件。
    - 文档明确这些结果同时服务论文结果章节、系统结果页和 API 输出契约。
  - Negative Tests (expected to FAIL):
    - 项目只保留模型运行，不再定义评价结构。
    - 模式发现与解释层被删掉，只剩单一收益指标。
    - 结果产物没有稳定输出语义，无法沉淀到 DuckDB 或论文章节。

- AC-6: Baostock 扩展必须沿当前 formal 主链增量实现，形成 `公共能力 -> raw 抓取 -> catalog 注册 -> coverage 查询` 的闭环。
  - Positive Tests (expected to PASS):
    - 计划包含 `code/data/baostock_common.py`，统一 `login/logout`、`query_with_relogin`、股票代码规范化、progress/append/resume 语义。
    - 计划包含 `fetch_baostock_adjust_factor.py`、`fetch_baostock_dividend.py`、`fetch_baostock_macro.py` 三类脚本及对应输出目录。
    - 计划明确更新 `README.md`、`code/data/formal/baostock/README.md`、`code/data/formal/baostock/manifest.json`。
    - 计划明确更新 `code/data/register_formal_duckdb_catalog.py` 并新增 raw/coverage views。
  - Negative Tests (expected to FAIL):
    - 直接复用外部仓库骨架或表结构。
    - 为新增 Baostock 数据单独再建一套平行工程。
    - raw 数据抓完后无法 resume、无法注册、无法做 coverage 查询。

- AC-7: Baostock 抓取层改造必须把“吸收什么 / 放弃什么”写成硬边界，防止外部参考改写当前主链。
  - Positive Tests (expected to PASS):
    - 计划明确 `BaoStockDemo` 只作为接口覆盖字典参考。
    - 计划明确 `mcp-baostock-server` 只吸收统一 API 包装、代码规范化和入参校验思路。
    - 计划明确 `vnpy_baostock` 只吸收最小字段和频率映射思路。
    - 计划明确放弃 MySQL 主链、demo 式绝对路径输出、每函数独立 `login/logout`、外部整套运行骨架。
  - Negative Tests (expected to FAIL):
    - 计划默认照搬外部仓库目录结构或数据库设计。
    - 计划允许 MCP 服务、交易引擎或通用量化平台骨架反向改写本项目边界。
    - 计划没有写明明确放弃项。

- AC-8: `adjust_factor` 与 `dividend` 必须优先沉淀为可被查询和解释层直接使用的对齐面板，`macro` 和财务 PIT 属于后续扩展。
  - Positive Tests (expected to PASS):
    - 计划包含 `code/data/build_adjust_factor_panel.py`，输出 `code/data/formal/master/adjust_factor_daily.csv`。
    - 计划包含 `code/data/build_dividend_event_panel.py`，输出 `code/data/formal/reports/dividend_events.csv`。
    - 计划明确 `adjust_factor` 和 `dividend` 优先级高于 `macro`。
    - 计划明确 `build_financial_point_in_time.py`、`build_macro_aligned_panel.py` 等属于后续阶段。
  - Negative Tests (expected to FAIL):
    - 一开始就把所有宏观字段并入 `full_master` 或张量输入。
    - 只抓 raw，不构建可解释层输出。
    - 未形成对齐面板就直接扩展复杂前端页面。

- AC-9: 抓取层必须显式补齐“数据集注册表、输入校验、最小字段策略、统一 schema”四个改造点，而不是继续散落式扩脚本。
  - Positive Tests (expected to PASS):
    - 计划明确对 `adjust_factor`、`dividend(report/operate/dividend)`、`macro(...)` 建立 dataset 级规格。
    - 计划明确补股票代码、指数代码、`yearType`、`frequency`、日期范围、dataset 名称校验。
    - 计划明确按用途定义字段集，而不是默认抓全字段。
    - 计划明确统一 raw CSV、manifest、DuckDB view 的 schema。
  - Negative Tests (expected to FAIL):
    - 继续用零散脚本各自定义输出列和进度格式。
    - 新脚本没有统一入参校验。
    - 辅助数据字段不加选择地全部透传到下游。

- AC-10: 测试与验证必须覆盖新增核心逻辑，文档轮次可以不跑代码测试，但要说明原因；代码轮次必须有对应最小充分验证。
  - Positive Tests (expected to PASS):
    - 计划明确新增测试文件：`test_baostock_common.py`、`test_fetch_baostock_adjust_factor.py`、`test_fetch_baostock_dividend.py`、`test_fetch_baostock_macro.py`、`test_register_formal_duckdb_catalog_aux.py`、`test_build_adjust_factor_panel.py`、`test_build_dividend_event_panel.py`。
    - 计划把测试纳入每个里程碑的完成标准，而不是收尾时再补。
    - 文档轮次交付时明确说明“本轮仅为计划文档生成，未运行代码测试”。
  - Negative Tests (expected to FAIL):
    - 新增脚本和 DuckDB 注册逻辑但没有测试。
    - 交付时不说明是否验证、为什么没验证。
    - 只做手工口头验证，不落自动化测试。

- AC-11: 任务树必须明确分为“必做 / 可选 / 暂缓”，并且依赖顺序清晰，不再混线推进。
  - Positive Tests (expected to PASS):
    - 计划明确列出必做项、可选项、暂缓项。
    - 计划明确先做 formal/实验闭环，再做解释增强和展示扩展，再做长期扩展。
    - 计划中的里程碑和任务分解与这一优先级保持一致。
  - Negative Tests (expected to FAIL):
    - 把所有事项重新混成一条无边界路线。
    - 先做低优先级页面或新技术栈，再回头补正式主链。
    - 必做和可选任务无法区分。

- AC-12: 项目完成后必须继续完成实验、论文和正式提交物，且论文排版优先使用 Typst。
  - Positive Tests (expected to PASS):
    - 计划明确项目实现完成后进入实验阶段，产出可复现实验结果。
    - 计划明确按 `2026理学院毕业设计指导书-V1(1).doc` 整理摘要、目录、正文、参考文献、附录、外文翻译、文献综述、开题材料、附件清单等交付物。
    - 计划明确优先使用 Typst 写作，最终导出 PDF/Word 提交物。
    - 计划明确实验结果要沉淀到论文章节，而不是与论文脱节。
  - Negative Tests (expected to FAIL):
    - 计划只覆盖代码实现，不覆盖实验与论文交付。
    - 论文写作阶段没有引用学校格式要求。
    - 论文只保留空模板，没有把实验结果和图表写进去。

## Path Boundaries

Path boundaries 用来约束实现范围，避免再次出现主线漂移、边界混乱或过度设计。

### Upper Bound (Maximum Acceptable Scope)

- formal 数据底座、Baostock 扩展、DuckDB catalog、实验 pipeline、Go 查询/运行接口、结果落盘与论文写作形成完整闭环。
- `HS300`、`SZ50`、`ZZ500` 三个正式样本均可完成正式实验配置、结果生成与论文图表沉淀。
- `adjust_factor_daily`、`dividend_events`、aux raw/coverage views 完整可查，`macro` 和 PIT 路线具备可继续推进的稳定接口。
- 抓取层完成公共模块化、dataset 规格化、schema 约束化、输入校验化，不再依赖零散 ad hoc 脚本习惯。
- Typst 论文源文件、图表资源、参考文献、文献综述、翻译与附件清单全部可复现、可导出、可提交。

### Lower Bound (Minimum Acceptable Scope)

- 文档层把研究主线、数据边界、系统边界、实验闭环、Baostock 扩展范围、抓取层改造原则、论文交付线讲清楚。
- `adjust_factor` 与 `dividend` 的公共能力、raw 抓取、catalog 注册和测试清单进入明确排期。
- “吸收什么 / 放弃什么 / 先做什么 / 暂缓什么”四层边界明确。
- 论文线被纳入主计划，而不是留到项目结束后临时补。

### Allowed Choices

- Can use:
  - `Go` 作为长期后端网关。
  - `Python` 作为数据处理与实验执行主语言。
  - `DuckDB + Parquet + CSV` 作为本地分析型数据层。
  - `PyTorch` 作为 GPU/模型主路径。
  - `Typst` 作为论文主写作工具，必要时导出 Word/PDF。
  - `Baostock` 作为当前 A 股数据扩展来源。
  - 外部项目仅作为接口和设计参考，不作为运行依赖。
- Cannot use:
  - 引入 `MySQL` 或双主链数据库体系。
  - 直接照搬外部仓库的数据库设计、pipeline 或运行骨架。
  - 将所有新增 raw 字段提前写入张量输入。
  - 在 formal 主链未稳定前先做复杂前端或展示层过度设计。
  - 把 Python HTTP 服务继续当作长期正式架构。

## Feasibility Hints and Suggestions

> 该部分用于帮助后续执行，不构成额外强制需求；强制要求以 AC 与任务树为准。

### Conceptual Approach

建议按“先收口主链、再扩展解释层、最后沉淀论文”的顺序推进：

1. 先固定文档与配置口径，确保研究主问题、样本边界、时间窗口、系统边界不会继续漂移。
2. 先做 `baostock_common.py`，把当前已存在的登录、重试、resume、progress 等公共能力真正收口。
3. 再做 `adjust_factor/dividend` raw 抓取，优先拿到高价值、低歧义的数据。
4. 在这一步同步补 dataset 规格、输入校验、最小字段策略和统一 schema。
5. 再做 DuckDB 注册与 coverage views，把“抓到了什么”变成可核验、可查询的正式资产。
6. 再构建 `adjust_factor_daily` 和 `dividend_events`，把 raw 数据升级成实验和解释层可直接消费的面板。
7. 然后把新增数据能力接入实验输出和 Go 查询层。
8. 项目实现闭环后，集中完成实验、图表、论文章节、文献综述、翻译和附件整理。

### Relevant References

- `draft.md`
  - 当前最完整的研究主线、Baostock 扩展、抓取层改造与论文交付约束来源。
- `code/data/fetch_baostock_data.py`
  - 当前 Baostock 主链之一，后续应优先抽公共能力而不是推翻重写。
- `code/data/fetch_baostock_kline.py`
  - 当前共享 kline 抓取主链之一，已有 progress/resume 机制可复用。
- `code/data/refresh_formal_baostock_manifest.py`
  - 当前 canonical root 与 manifest 汇总逻辑来源。
- `code/data/register_formal_duckdb_catalog.py`
  - 当前 DuckDB catalog 注册逻辑来源。
- `code/data/formal/README.md`
  - formal 数据目录职责与当前数据底座说明。
- `code/data/formal/DATABASE_DESIGN.md`
  - DuckDB / formal 数据设计口径。
- `code/data/formal/baostock/README.md`
  - 当前 Baostock canonical root 说明。
- `code/data/formal/baostock/manifest.json`
  - 当前 manifest 语义，需要在 aux 数据接入时同步扩展。
- `2026理学院毕业设计指导书-V1(1).doc`
  - 论文与附件交付规范来源。

## Dependencies and Sequence

### Milestones

1. 里程碑 1：固定研究口径与项目边界
   - 阶段 A：统一研究主问题、样本边界、正式时间窗口、方法口径。
   - 阶段 B：统一 Go/Python/DuckDB/Parquet 的职责边界。
   - 阶段 C：把论文交付要求和 Baostock 抓取层改造原则正式纳入任务树。

2. 里程碑 2：完成抓取层公共能力收口
   - 阶段 A：抽出 `baostock_common.py`。
   - 阶段 B：把登录、重试、resume、代码规范化和 append/progress 统一收口。
   - 阶段 C：定义 dataset 规格与输入校验边界。

3. 里程碑 3：完成 Baostock 扩展最小闭环
   - 阶段 A：实现 `adjust_factor`、`dividend` raw 抓取与 progress/resume。
   - 阶段 B：更新 README、manifest、DuckDB raw/coverage views。
   - 阶段 C：补齐最小自动化测试。

4. 里程碑 4：把 raw 提升为解释层与分析层资产
   - 阶段 A：构建 `adjust_factor_daily.csv`。
   - 阶段 B：构建 `dividend_events.csv`。
   - 阶段 C：将这些结果接入 formal 查询与下游分析。

5. 里程碑 5：扩展后续能力但保持主线不漂移
   - 阶段 A：设计 `macro`、财务 PIT、macro aligned panel 的后续接口。
   - 阶段 B：视需要扩展 `full_master` / factor panel supplement。
   - 阶段 C：把新增数据能力纳入 Go 查询读路径。

6. 里程碑 6：完成实验沉淀与论文交付
   - 阶段 A：运行正式实验，产出指标、图表、案例和解释结果。
   - 阶段 B：使用 Typst 完成论文正文、文献综述、外文翻译与附录整理。
   - 阶段 C：导出 PDF/Word，整理附件与答辩材料。

## Task Breakdown

每个任务仅保留一个路由标记：
- `coding`: 需要直接落代码或落文档
- `analyze`: 需要先做研究、对照或结构设计

| Task ID | Description | Target AC | Tag (`coding`/`analyze`) | Depends On |
|---------|-------------|-----------|---------------------------|------------|
| task-01 | 将研究主问题、样本边界、时间窗口、系统边界整理成正式主计划口径 | AC-1, AC-2, AC-3, AC-11 | coding | - |
| task-02 | 固化外部参考的吸收/放弃边界，形成抓取层硬约束清单 | AC-6, AC-7, AC-11 | analyze | task-01 |
| task-03 | 审核 formal 数据目录、DuckDB 设计和当前 manifest 语义，整理 aux 扩展影响面 | AC-3, AC-6, AC-9 | analyze | task-01 |
| task-04 | 实现 `code/data/baostock_common.py`，统一 session、relogin、代码规范化、resume 语义 | AC-6, AC-9, AC-10 | coding | task-02 |
| task-05 | 设计 `adjust_factor / dividend / macro` 的 dataset 规格与输入校验规则 | AC-7, AC-9 | analyze | task-04 |
| task-06 | 实现 `code/data/fetch_baostock_adjust_factor.py` 及其输出目录和 progress 文件 | AC-6, AC-9, AC-10 | coding | task-05 |
| task-07 | 实现 `code/data/fetch_baostock_dividend.py` 及 report/operate/dividend 三类输出 | AC-6, AC-9, AC-10 | coding | task-05 |
| task-08 | 实现 `code/data/fetch_baostock_macro.py` 的首批 dataset 抓取框架与延期边界 | AC-6, AC-8, AC-9 | coding | task-05 |
| task-09 | 扩展 `code/data/register_formal_duckdb_catalog.py` 与 aux raw/coverage views | AC-6, AC-10 | coding | task-06 |
| task-10 | 更新 canonical root 文档与 manifest，包括 `README.md`、Baostock README 和统计语义 | AC-6, AC-9, AC-11 | coding | task-09 |
| task-11 | 实现 `code/data/build_adjust_factor_panel.py` 并输出 `adjust_factor_daily.csv` | AC-8, AC-10 | coding | task-06 |
| task-12 | 实现 `code/data/build_dividend_event_panel.py` 并输出 `dividend_events.csv` | AC-8, AC-10 | coding | task-07 |
| task-13 | 设计 `macro`、财务 PIT、macro aligned panel 的后续接口与延期边界 | AC-8, AC-11 | analyze | task-12 |
| task-14 | 将新增数据产物纳入实验输入/输出和 Go 查询读路径 | AC-3, AC-5, AC-8 | coding | task-11 |
| task-15 | 补齐测试：common、fetch、catalog、panel 构建 | AC-10 | coding | task-14 |
| task-16 | 设计论文 Typst 工程骨架、章节映射、图表落位和导出流程 | AC-12 | analyze | task-01 |
| task-17 | 基于正式实验结果完成论文写作、文献综述、翻译、附录和提交物整理 | AC-12 | coding | task-16 |

## Planned Scripts and Outputs

### 必须纳入近期实现的脚本

- `code/data/baostock_common.py`
- `code/data/fetch_baostock_adjust_factor.py`
- `code/data/fetch_baostock_dividend.py`
- `code/data/fetch_baostock_macro.py`
- `code/data/build_adjust_factor_panel.py`
- `code/data/build_dividend_event_panel.py`
- `code/data/register_formal_duckdb_catalog.py`
- `code/data/run_baostock_stage2_aux_dataset_year.sh`
- `code/data/run_baostock_stage3_aux.sh`

### 必须纳入近期测试的文件

- `code/tests/test_baostock_common.py`
- `code/tests/test_fetch_baostock_adjust_factor.py`
- `code/tests/test_fetch_baostock_dividend.py`
- `code/tests/test_fetch_baostock_macro.py`
- `code/tests/test_register_formal_duckdb_catalog_aux.py`
- `code/tests/test_build_adjust_factor_panel.py`
- `code/tests/test_build_dividend_event_panel.py`

### 必须约束清楚的输出目录

- `code/data/formal/baostock/adjust_factor/<year>.csv`
- `code/data/formal/baostock/adjust_factor/_progress.json`
- `code/data/formal/baostock/dividend/report/<year>.csv`
- `code/data/formal/baostock/dividend/operate/<year>.csv`
- `code/data/formal/baostock/dividend/dividend/<year>.csv`
- `code/data/formal/baostock/dividend/_progress.json`
- `code/data/formal/baostock/macro/<dataset>/<year>.csv`
- `code/data/formal/baostock/macro/_progress.json`
- `code/data/formal/master/adjust_factor_daily.csv`
- `code/data/formal/reports/dividend_events.csv`
- `code/data/formal/master/macro_daily.csv`
- `code/data/formal/master/macro_monthly.csv`

### 必须纳入 DuckDB catalog 的视图

- `vw_baostock_adjust_factor_raw`
- `vw_baostock_dividend_raw`
- `vw_baostock_macro_raw`
- `vw_formal_adjust_factor_coverage`
- `vw_formal_dividend_coverage`
- `vw_formal_macro_coverage`

## 必做 / 可选 / 暂缓

### 必做

- 固定研究主问题、样本边界、时间窗口、系统边界和实验主线。
- 把 Baostock 外部参考的吸收/放弃边界写成正式硬约束。
- 抽出 `baostock_common.py`，统一 session、relogin、resume、append/progress 语义。
- 建立 `adjust_factor / dividend / macro` 的 dataset 规格与输入校验。
- 完成 `adjust_factor` raw 抓取与年级别恢复。
- 完成 `dividend` raw 抓取与 `code|year|year_type` 级别恢复。
- 更新 `README.md`、`code/data/formal/baostock/README.md`、`manifest.json`。
- 扩展 DuckDB raw/coverage views。
- 构建 `adjust_factor_daily.csv`。
- 构建 `dividend_events.csv`。
- 补齐对应测试。
- 将项目完成后的实验、论文、Typst 写作与提交物整理纳入主计划。

### 可选

- 构建 `build_financial_point_in_time.py`。
- 构建 `build_macro_aligned_panel.py`，输出 `macro_daily.csv` / `macro_monthly.csv`。
- 将部分复权因子、分红事件标记和少量共享宏观特征纳入 `full_master` supplement。
- 在财务 PIT 稳定后，将一部分稳定基本面特征并入 factor panel。
- 新增 aux stage 批处理入口脚本。
- 在 Go / 前端中展示 aux formal coverage 信息。

### 暂缓

- 引入 MySQL 或双存储主链。
- 直接套用外部项目的数据库结构或全套 pipeline。
- 一开始就把所有宏观字段并入 `full_master`。
- 一开始就把所有新增 raw 字段并入张量输入。
- 为新增 Baostock 数据另起一套平行工程结构。
- 在数据主链未稳定前过早做复杂前端页面。
- 在论文主线未稳定前扩张新的正式研究主题。
- 把 `Triton` 提前用于数据层，而不是保持在模型服务层。

## Claude-Codex Deliberation

### Agreements

- 当前 `draft.md` 与仓库现状高度相关，可以直接生成正式计划，不需要先回退到更早的 brainstorm 阶段。
- 本次计划必须把 Baostock 扩展、抓取层改造原则和论文交付同时纳入，不能只写代码实现路线。
- 当前最合理的主线是先闭环 formal 数据与实验，再沉淀论文，而不是先做展示层扩张。
- 当前仓库已有 Baostock 主链比外部参考更适合作为继续演化的基础，不应被外部参考骨架替代。

### Resolved Disagreements

- 是否把 `macro` 放进近期必做：
  - 草案中给出了 `macro` 抓取需求，但优先级说明也明确 `adjust_factor` 与 `dividend` 更贴近当前主线。
  - 结论：`macro` 保留在计划中，但不与 `adjust_factor/dividend` 争抢第一阶段资源。
- 是否把论文写作放到主计划之外：
  - 用户已明确要求项目写完后继续做实验并完成论文。
  - 结论：论文、实验和交付物整理必须成为主计划的一部分，不再视为计划外事项。
- 是否直接吸收外部参考仓库骨架：
  - `draft.md` 已明确外部项目只用于吸收优点，不作为运行依赖。
  - 结论：只吸收接口覆盖、入参校验、字段裁剪和轻量标准化，不吸收其数据库和系统边界。

### Convergence Status

- Final Status: `converged`

## Pending User Decisions

- 当前无阻塞性待决策项。
- 若后续学校强制提供 LaTeX 模板且 Typst 无法满足版式要求，再单独做 Typst/LaTeX 回退判断；在此之前默认以 Typst 为主。

## Implementation Notes

### Code Style Requirements

- 生产代码与正式注释中不要直接写入 `AC-`、`Milestone`、`Task` 等计划术语。
- 代码标识符保持英文，用户可见文档、注释、计划、提交信息保持简体中文。
- 新增脚本、测试和文档统一使用 UTF-8 无 BOM。
- 关键逻辑要写中文注释，重点解释“为什么这样做”和与论文主线、formal 主链的关系。

### Verification Notes

- 本轮属于计划文档生成，不涉及代码逻辑改动，因此不运行项目测试。
- 后续进入代码实现轮次时，每个新增脚本、dataset 规格、DuckDB 注册逻辑都必须执行对应最小充分验证。

### Anti-Patterns

- 不要把当前计划重新写回“普通网站开发计划”。
- 不要在 formal 主链未稳定前引入新数据库或复杂中间件。
- 不要先堆页面再回头补数据底座。
- 不要让论文写作与实验结果脱节。
- 不要让外部参考项目反向改写当前仓库的 canonical root、manifest 和 DuckDB 主链。
