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
将当前样例级实验管线升级为面向真实实证、选股应用与后续产品化的研究平台。正式 A 股实验范围不再以中证 A500 为目标，而是以以下三类核心指数股票池为主：

1. 沪深300（`HS300`）
2. 上证50（`SZ50`）
3. 中证500（`ZZ500`）

在此基础上，项目需要同时完成四条主线：

1. 使用 baostock API 将全 A 股行情、全 A 股财务/报告数据、三类指数成分股历史和全 A 可交易股票池历史抓取到本地，形成正式数据底座。
2. 在正式数据之上构建“股票 × 因子 × 时间”的张量实验管线，完成 CP/Tucker/PCA 对比、模式发现和选股输出。
3. 在数据层同时保留轻量样例数据，作为后续 smoke test、接口联调和前端演示输入；正式全量数据使用独立文件和独立目录保存。
4. 为大规模计算加入 GPU 计算能力，优先采用 `PyTorch` 作为统一计算后端，在 CUDA 可用时走 GPU 路径，并对热点算子预留 `Triton` 或原生 `CUDA` 优化路径。

### Acceptance Criteria
<!-- Each criterion must be independently verifiable -->
<!-- Claude must extract or define these in Round 0 -->


- AC-1: A 股正式数据底座覆盖固定窗口 `2015-01-01` 到 `2026-04-01`，不再使用模糊的“到 2026 年某个可用交易日”为主口径。
- AC-2: baostock 数据抓取链路可将全 A 股行情数据统一保存到正式目录，并生成可复用 manifest。
- AC-3: baostock 数据抓取链路可将全 A 股财务/报告数据统一保存到正式目录，并按表类型分别落盘，例如盈利能力、营运能力、成长能力、偿债能力、现金流、杜邦指标、业绩快报、业绩预告。
- AC-4: `HS300`、`SZ50`、`ZZ500` 的成分股历史，以及全 A 可交易股票池历史，必须分别作为独立文件保存；回测时按“历史时点成分股”口径过滤，不能用静态名单覆盖整个回测期。
- AC-5: 正式数据先提供 `CSV` 版本，再生成与之对应的 `Parquet` 版本；二者目录、命名和 manifest 必须一一对应。
- AC-5.1: 结构化正式数据需进一步注册到本地 `DuckDB` catalog 中，支持直接查询 `universes`、`master`、`factors`、`financial`、`reports` 与 `full_master`。
- AC-5.2: `DuckDB` catalog 至少应提供 CSV/Parquet 外部表或视图、常用统计视图，以及供 Web 查询层直接调用的稳定对象名。
- AC-6: 原有样例数据、样例配置和样例输出继续保留，仅作为 smoke test 和轻量验证输入，不与正式全量数据混用。
- AC-7: 核心实验管线不依赖某个单一股票池或 A 股特有代码格式；股票池、交易日历、符号规范化和数据源都通过适配层提供。
- AC-8: 新增 `us_equity` 市场适配接口后，不修改 CP/Tucker/PCA 核心模型代码即可接入美股数据；A 股与美股共用同一套“市场主数据 + universe 历史”抽象。
- AC-9: 选股层可基于模型结果产出指定日期的候选股票列表，至少包含股票代码、综合评分、主要贡献因子、所属市场与所属股票池。
- AC-10: Web 后端提供实验运行、结果查询、选股查询三个基本能力；前端可完成配置提交、结果展示、候选股浏览，并能在三类正式股票池之间切换。
- AC-11: 计算后端支持 `PyTorch` 主路径，在 CUDA 可用时执行 GPU 计算；对热点算子预留 `Triton/CUDA` 优化接口；CPU 路径仍可回退。
- AC-12: 自动化测试覆盖正式配置解析、历史成分过滤、baostock 数据处理、统一候选池输出、核心 API 返回格式，以及 GPU 可用性探测与 CPU 回退逻辑。
- AC-13: 输出目录中除实验指标外，新增可供 Web 端直接读取的结构化结果文件，不要求前端解析日志文本。

## Path Boundaries

---

## MUTABLE SECTION
<!-- Update each round with justification for changes -->

### Plan Version: 1 (Updated: Round 0)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | - | - |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| 重构正式数据目录，明确区分样例目录、正式全量目录、universe 历史目录以及 `CSV/Parquet` 双形态输出 | AC-1, AC-5, AC-6 | pending | coding | claude | 先保证样例与正式目录完全隔离，再推进 formal 主链路 |
| 完成全 A 股基础资料、行业信息和全 A 可交易股票池历史的本地落盘与 manifest 记录 | AC-1, AC-2, AC-4 | pending | coding | claude | Stage 1 元数据和全 A tradable history 是 formal 底座入口 |
| 完成 `HS300` / `SZ50` / `ZZ500` 指数成分股快照、变更记录与成员历史文件构建 | AC-2, AC-4 | pending | coding | claude | 回测必须按历史时点成员过滤，不能退化为静态名单 |
| 完成全 A 股前复权行情抓取与统一主数据落盘，并为正式 profile 提供共享输入 | AC-1, AC-2, AC-4 | pending | coding | claude | 共享行情主表应服务三类正式股票池，而不是按指数重复存储 |
| 完成全 A 股财务与报告数据按表类型的正式落盘，并补齐 canonical `financial/` 与 `reports/` 目录 | AC-1, AC-3, AC-12 | pending | coding | claude | Stage 2 数据需按表拆分并保持可恢复执行 |
| 生成正式因子面板与张量输入，确保 `formal_hs300` / `formal_sz50` / `formal_zz500` 都引用真实正式数据 | AC-4, AC-7, AC-9, AC-13 | pending | coding | claude | formal profile 不能回退到样例数据，也不能出现路径失配 |
| 将正式数据从 `CSV` 转换为 `Parquet`，并注册 DuckDB catalog 与稳定查询视图 | AC-5, AC-5.1, AC-5.2, AC-12 | pending | coding | claude | 包含 parity 校验、catalog 注册、coverage / on-date 视图 |
| 保持并补强 Web 后端 / 前端对正式 profile 的支持，保证市场列表、运行配置和结果展示与新正式数据结构一致 | AC-9, AC-10, AC-13 | pending | coding | claude | Web 查询层优先读取 DuckDB，而不是直接扫描大型 CSV |
| 继续推进 `PyTorch` 设备层、CUDA 优先路径和 `Triton/CUDA` 热点接口预留，并保留 CPU 回退 | AC-11, AC-12 | pending | coding | claude | 先保证 `cpu/cuda/auto` 行为稳定，再谈热点优化 |
| 保持 `sample_cn_smoke` / `sample_us_equity` 样例路径可用，作为 smoke test 和接口联调夹具 | AC-6, AC-8, AC-12 | pending | coding | claude | 样例路径要保留，但必须与正式全量目录严格隔离 |

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
| Committed formal universes, factor panels, and shared kline outputs only cover a short `2026-03-02` to `2026-04-03` slice instead of the required fixed window `2015-01-01` to `2026-04-01`. | 0 | AC-1, AC-2, AC-4, AC-5 | Rebuild the formal baostock/formal output chain for the full fixed window, clamp all generated files to `2026-04-01`, and refresh manifest date ranges. |
| `code/data/formal/baostock/manifest.json` reports empty `stage_2_formal_outputs` even though year-partitioned financial/report exports already exist on disk. | 0 | AC-2, AC-3, AC-5, AC-12 | Refresh manifest generation so Stage 2 enumerates committed financial/report files and add a regression check against the committed-style tree. |
| DuckDB-specific tests and runtime routes are not locally verified in the current `.venv` because `duckdb` is not installed. | 0 | AC-5.1, AC-5.2, AC-12 | Install `duckdb` into the project environment, rerun the skipped catalog/API tests, and verify `/api/formal/*` endpoints against a rebuilt catalog. |
| Round 0 did not create Trellis task-system entries for the implementation slices even though the round prompt explicitly required `TaskCreate/TaskUpdate/TaskList` tracking for all tasks. | 0-review | All AC | Create one Trellis task per active implementation slice before further coding, then keep task state aligned with Goal Tracker state. |
| Formal universe / factor / shared-kline artifacts recorded in `code/data/formal/baostock/manifest.json` only cover roughly `2026-03-02` to `2026-03-30` or `2026-04-03`, so the committed formal profile outputs do not satisfy the fixed `2015-01-01` to `2026-04-01` window. | 0-review | AC-1, AC-4, AC-5 | Rebuild the formal universe histories, factor panels, shared kline panel, and derived manifests from the full window, then clamp all outputs to the `2026-04-01` cutoff. |
| Canonical `code/data/formal/financial/` and `code/data/formal/reports/` outputs are not populated, and the canonical manifest records empty Stage 2 file lists. | 0-review | AC-3, AC-5.1, AC-12 | Materialize the table-split financial/report outputs into the canonical formal directories and refresh the manifest from those canonical paths. |
| DuckDB registration currently prefers transitional `code/data/formal/baostock/financial/*` and `code/data/formal/baostock/reports/*` sources ahead of the canonical `financial/` and `reports/` directories defined by the formal layout. | 0-review | AC-3, AC-5.1, AC-5.2 | Change catalog registration to bind canonical formal datasets first, using transitional baostock trees only as an explicit backfill path during migration. |
| Full-master coverage is not cleanly validated: `full_master_2020.csv` is absent from the committed tree while `full_master_2020_check.json` claims it exists, and the reconcile summary still records `UNKNOWN` / `ISSUES` statuses across 2019-2026. | 0-review | AC-1, AC-5.1, AC-12 | Regenerate the missing year file, rerun reconciliation, and fail the verification path when yearly full-master coverage or supplement completeness is below threshold. |
| The frontend selection view defaults to `2026-01-09`, but the committed formal run manifests start at `2026-03-02`, so formal runs initially render an empty candidate list. | 0-review | AC-10, AC-13 | Drive the default selection date from the selected run manifest or the first available trade date returned by the backend. |
