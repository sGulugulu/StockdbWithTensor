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

### Plan Version: 3 (Updated: Round 2)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | - | - |
| 0 | 将正式研究口径固定为“全 A 主数据 + `HS300` / `SZ50` / `ZZ500` / 全 A universe 历史”，并把正式时间窗固定为 `2015-01-01` 到 `2026-04-01` | 用户已明确要求放弃 `CSI_A500` 作为正式目标，并要求正式全量数据与样例数据分离 | 直接收敛 AC-1、AC-2、AC-3、AC-4、AC-5、AC-6 的范围定义，避免后续实现继续围绕旧计划漂移 |
| 0 | 第一批实现优先落在“正式数据目录骨架 + 全 A 可交易股票池历史生成 + 测试可离线导入” | 这三项可以在不等待长时间联网抓数的前提下直接落地，并为后续全 A 正式抓取链路提供稳定接口 | 直接推进 AC-1、AC-2、AC-3、AC-4、AC-5、AC-6、AC-12 |
| 1 | 正式 profile 配置路径已切到 `code/data/formal/universes/` 与 `code/data/formal/factors/`，后端市场目录也已移除废弃的 `formal_cn_a` / `CSI_A500` 入口 | 这一部分实现与 Round 0 的正式研究口径一致，避免后端继续暴露已废弃的正式 A500 入口 | 直接推进 AC-1、AC-4、AC-7、AC-10，但不改变 AC-2、AC-3、AC-5 仍未完成的事实 |
| 2 | all-A Stage 2 代码列表改为输出 baostock 原生代码格式，canonical refresh 默认源不再指向旧 `baostock_fg_test` / `baostock_sz50_fg` / `baostock_zz500_fg`，并新增可执行的 `CSV -> Parquet` 转换脚本 | Round 1 review 指出的两个正确性缺陷已在代码层被修复，同时 `Parquet` 不再只是 README 意图，而是具备了实际入口脚本 | 直接推进 AC-2、AC-3、AC-5、AC-7、AC-12，但不代表正式全量产物和 manifest parity 已完成 |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| 重构正式数据目录，明确区分样例目录、正式全量目录、universe 历史目录以及 `CSV/Parquet` 双形态输出 | AC-1, AC-5, AC-6 | in_progress | coding | claude | structured `universes/`、`factors/`、`master/` 已在使用，且 all-A metadata / history 已有真实落盘；但 `financial/`、`reports/`、`parquet/` 仍未形成正式全量产物，manifest 也还没有 CSV/Parquet 对应关系 |
| 完成全 A 股基础资料、行业信息和全 A 可交易股票池历史的本地落盘与 manifest 记录 | AC-1, AC-2, AC-4 | in_progress | coding | claude | canonical formal root 下已真实落盘 `stock_basic.csv`、`stock_industry.csv`、`all_a_codes.csv`、`all_a_tradable_history.csv`；但 canonical manifest 仍引用旧窗口阶段信息，尚未成为可信的正式基座记录 |
| 完成 `HS300` / `SZ50` / `ZZ500` 指数成分股快照、变更记录与成员历史文件构建 | AC-2, AC-4 | pending | coding | claude | 回测必须按历史时点成员过滤，不能退化为静态股票名单 |
| 完成全 A 股前复权行情抓取与统一主数据落盘，并为正式 profile 提供共享输入 | AC-1, AC-2, AC-4 | pending | coding | claude | batch 脚本已切到 `metadata/all_a_codes.csv` 作为 shared kline 输入，但仓库中已提交的 `shared_kline_panel.csv` 与 factor panels 仍是 `572` 只股票、`2026-03-02` 到 `2026-04-03` 的短窗口夹具，不是计划要求的全 A 正式主数据 |
| 完成全 A 股财务与报告数据按表类型的正式落盘，并补齐 canonical `financial/` 与 `reports/` 目录 | AC-1, AC-3, AC-12 | pending | coding | claude | 这是当前已知最大数据缺口，必须支持恢复执行 |
| 生成正式因子面板与张量输入，确保 `formal_hs300` / `formal_sz50` / `formal_zz500` 都引用真实正式数据 | AC-4, AC-7, AC-9, AC-13 | pending | coding | claude | formal profile 不能回退样例数据，也不能出现 `universe_id` 与文件路径失配 |
| 将正式数据从 `CSV` 转换为 `Parquet`，并保证字段合同、日期区间与 manifest 一致 | AC-5, AC-12 | pending | coding | claude | `convert_formal_csv_to_parquet.py` 已存在，但 batch 流程尚未调用它，`code/data/formal/parquet/` 仍为空，manifest 也没有记录 CSV/Parquet 一一对应与 parity 校验结果 |
| 保持并补强 Web 后端 / 前端对正式 profile 的支持，保证市场列表、运行配置和结果展示与新正式数据结构一致 | AC-9, AC-10, AC-13 | pending | coding | claude | 前端构建与后端 API 合同都要持续回归 |
| 继续推进 `PyTorch` 设备层、CUDA 优先路径和 `Triton/CUDA` 热点接口预留，并保留 CPU 回退 | AC-11, AC-12 | pending | coding | claude | CUDA 验证需要真实可用环境；在此之前只能完成接口与 CPU fallback 的可验证部分 |
| 保持 `sample_cn_smoke` / `sample_us_equity` 样例路径可用，作为 smoke test 和接口联调夹具 | AC-6, AC-8, AC-12 | pending | coding | claude | 样例数据要保留，但必须和正式全量目录严格隔离 |

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
| 当前 `fetch_baostock_data.py` 直到本轮之前都在模块导入时强依赖 `baostock`，导致 Windows 侧未安装 `baostock` 时连纯辅助测试都无法导入 | 0 | AC-12 | 已改为按需导入 `baostock`；后续保持纯数据整理函数不依赖 live API 环境 |
| canonical formal root 下已真实落盘 `stock_basic.csv`、`stock_industry.csv`、`all_a_codes.csv` 与 `all_a_tradable_history.csv`，但 `financial/` / `reports/` 仍为空目录 | 0 | AC-1, AC-2, AC-3 | 在同一 canonical root 下完成 all-A Stage 2 正式抓取，并让 manifest 直接记录这些真实输出而不是继续沿用旧窗口元数据 |
| 新建的 `code/data/formal/universes/`、`code/data/formal/factors/`、`code/data/formal/master/` 目前承载的仍是短窗口迁移夹具，而 `financial/`、`reports/`、`parquet/` 目录仍是占位状态，不是计划要求的 `2015-01-01` 到 `2026-04-01` 正式全量数据 | 1 | AC-1, AC-2, AC-3, AC-5 | 必须在真实全量 baostock 抓取完成后重建 structured 目录产物，并让 manifest、CSV 和 Parquet 一起指向正式全量版本 |
| `refresh_formal_baostock_manifest.py` 已不再默认复制旧 fixture 树，但在默认参数下仍会把当前 canonical `manifest.json` 自身当作 `hs300` / `sz50` / `zz500` 三个 committed source 反向读入，导致 `stage_1_stage_2_committed_sources` 与窗口信息继续失真 | 2 | AC-1, AC-2, AC-3, AC-4 | refresh 必须改为读取独立的阶段源 manifest，或直接根据当前 canonical Stage 1/2 真实输出重建 source stats，不能再把 canonical manifest 自己当作三份来源元数据 |
| `CSV -> Parquet` 转换脚本已添加，但 `.venv` 当前仍缺少 parquet engine，且 canonical full-range CSV 数据本身尚未补齐，所以 `code/data/formal/parquet/` 仍为空且没有任何 manifest parity 记录 | 2 | AC-5, AC-12 | 在 `.venv` 安装 `pyarrow` 或 `fastparquet` 后，以真实 full-range CSV 产物运行转换，补充 schema / row-count / date-range parity 校验并把映射写入 manifest |
