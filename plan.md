# 基于张量分解的多指数股票因子降维、选股与 GPU 加速实施计划

## Goal Description
将当前样例级实验管线升级为面向真实实证、选股应用与后续产品化的研究平台。正式 A 股实验范围不再以中证 A500 为目标，而是以以下三类核心指数股票池为主：

1. 沪深300（`HS300`）
2. 上证50（`SZ50`）
3. 中证500（`ZZ500`）

在此基础上，项目需要同时完成四条主线：

1. 使用 baostock API 将全 A 股行情、全 A 股财务/报告数据、三类指数成分股历史和全 A 可交易股票池历史抓取到本地，形成正式数据底座。
2. 在正式数据之上构建“股票 × 因子 × 时间”的张量实验管线，完成 CP/Tucker/PCA 对比、模式发现和选股输出。
3. 在数据层同时保留轻量样例数据，作为后续 smoke test、接口联调和前端演示输入；正式全量数据使用独立文件和独立目录保存。
4. 为大规模计算加入 GPU 计算能力，优先采用 `PyTorch` 作为统一计算后端，在 CUDA 可用时走 GPU 路径，并对热点算子预留 `Triton` 或原生 `CUDA` 优化路径。

说明：
今天是 `2026-04-04`，本阶段正式全量数据窗口固定解释为 `2015-01-01` 到 `2026-04-01`。其中：

1. 全 A 股行情数据统一保存为正式主数据。
2. 全 A 股财务/报告数据统一保存，并按表类型拆分保存。
3. `HS300`、`SZ50`、`ZZ500` 的成分股历史，以及全 A 可交易股票池历史各自单独保存。
4. 正式数据先落盘为 `CSV`，再转换为 `Parquet`；原有样例文件继续保留，仅用于 smoke test 和轻量验证。
5. 正式数据查询与 Web 服务优先采用 `Parquet + DuckDB` 的本地分析型架构，而不是把全部历史主数据直接塞进传统 OLTP 数据库。

## Acceptance Criteria

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

### Upper Bound
- 完成全 A 股正式本地数据底座接入。
- 完成 `HS300`、`SZ50`、`ZZ500` 及全 A 可交易股票池历史文件构建。
- 完成 `Parquet + DuckDB` 的正式查询层，支持本地 SQL 检索、研究统计与 Web 数据读取。
- 支持 `cn_a` 与 `us_equity` 两类市场配置。
- 提供 FastAPI 后端与 React 前端。
- 默认计算后端支持 `PyTorch + CUDA`，并为 `Triton/CUDA` 热点算子优化预留接口。
- 对热点算子提供 `Triton` 或原生 `CUDA` 的优化预留。
- 支持单次实验运行、历史实验查看、指定日期选股、因子解释展示。
- 正式数据同时提供 `CSV` 与 `Parquet` 两种存储形态。

### Lower Bound
- 先完成全 A 股正式主数据目录和至少一类正式股票池的全链路跑通。
- baostock 抓取工具、正式配置、张量实验、统一候选池、Web API 和前端基本页面都必须存在。
- 至少完成一组 `CSV -> Parquet -> DuckDB` 端到端样例，使 Web 和研究统计能直接从 DuckDB 读取。
- GPU 路径最低要求是：
  - 可检测 CUDA 是否可用
  - 在可用时使用 `PyTorch` 张量在 GPU 上运行主要数值计算
  - 在不可用时安全回退 CPU
- 正式 `CSV` 数据与 `Parquet` 数据至少保证一组主流程可验证可读。

### Allowed Choices
- 后端固定为 Python，优先 `FastAPI`。
- 前端固定为 `React + Vite`。
- GPU 计算优先使用 `PyTorch`。
- `Triton` 或 `CUDA` 可先用于热点算子和批量评分路径，不要求一开始全量重写算法。
- 正式历史主数据优先采用 `CSV + Parquet` 文件层落盘。
- 正式查询 / 服务层优先采用 `DuckDB`，而不是先引入 `MySQL/PostgreSQL`。
- 不在这一版加入登录鉴权、多人协作、交易下单或生产部署编排。

## Feasibility Hints and Suggestions
- baostock 抓取应分阶段执行：
  - Stage 1：全 A 股股票基础资料、行业信息、全 A 可交易股票池历史、三类指数成分股快照与变更记录
  - Stage 2：全 A 股财务数据、报告数据
  - Stage 3：全 A 股前复权日线/估值面板抓取与本地因子面板构建
  - Stage 4：正式 `CSV` 转换为 `Parquet`，并补齐 manifest
  - Stage 5：将结构化正式数据注册到 `DuckDB` catalog，并产出统一查询视图
- 三个正式股票池应各自拥有独立 universe 历史文件和独立正式配置，不共享模糊的“formal_cn_a”语义。
- 正式配置必须保持“股票池标识、成员文件路径、因子面板路径”三者一致，不能只改 `universe_id` 文本而读取别的指数数据。
- 全 A 股行情和全 A 股财务数据不应按指数重复保存；指数回测通过“全 A 主数据 + universe 历史过滤”完成。
- 不要把全部历史主数据直接作为传统关系型数据库唯一底座；`DuckDB` 更适合当前单机研究、批量分析、Parquet 直查与 Web 查询聚合场景。
- 原有样例数据目录必须保留，但要与正式全量目录完全隔离，避免 smoke 数据污染正式回测结果。
- 选股逻辑不要绑定单一分解方法。统一从 `ModelResult` 生成候选池，并对不同模型结果做聚合或一致化输出。
- GPU 计算不要一开始就拆成三套完全独立实现：
  - 先把数值核心改成 `PyTorch`
  - CUDA 通过 `torch` 设备路径优先落地
  - 再根据 profiling 决定哪些热点算子值得下沉到 `Triton/CUDA`
- Web 端优先读取结构化产物，例如：
  - `run_manifest.json`
  - `selection_candidates.json`
  - `factor_summary_*.json`
  - `factor_association_*.json`

## Dependencies and Sequence

1. 先完成正式数据目录重构，区分样例数据与正式全量数据。
2. 再完成全 A 股主数据抓取链路，包括行情、财务、报告和 manifest。
3. 再完成 `HS300`、`SZ50`、`ZZ500` 及全 A 可交易股票池历史文件生成。
4. 在正式数据之上构建因子面板、张量实验输入和正式 profile。
5. 将结构化 CSV 转为 Parquet，并完成 parity 校验。
6. 将正式 CSV / Parquet 数据注册到 DuckDB catalog，补齐统一查询视图。
7. 将数值计算主路径迁移到 `PyTorch`，加入 CUDA/CPU 双路径，并为 `Triton/CUDA` 热点实现留口。
8. 完成统一候选池输出和实验结果结构化。
9. 再做 Web API 和前端页面整合。
10. 最后保留 `us_equity` 接口作为后续扩展入口。

### External Dependencies
- baostock API
- 本地网络可访问 baostock 服务
- Python 依赖：`baostock`、`numpy`、`PyYAML`、`fastapi`、`uvicorn`、`httpx`
- GPU 依赖：`torch`
- 列式存储依赖：`pyarrow` 或 `fastparquet`
- 本地分析数据库依赖：`duckdb`
- 可选性能增强：`triton` 或 CUDA toolchain
- 前端依赖：`node`、`vite`、`react`

## Task Breakdown

### 1. 正式数据目录与历史样例保留
- 保留现有样例数据、样例配置和样例输出，继续作为 smoke test 输入。
- 新建独立正式数据目录，用于保存 `2015-01-01` 到 `2026-04-01` 的全量数据。
- 正式目录中区分：
  - 全 A 股主数据
  - universe 历史文件
  - 中间构建结果
  - `CSV` 与 `Parquet` 两种落盘形态

### 2. 全 A 股主数据抓取与本地落盘
- 使用 baostock 抓取全 A 股股票基础资料、行业信息和全 A 可交易股票池历史。
- 使用 baostock 抓取全 A 股前复权行情数据，统一保存，不按指数重复保存。
- 使用 baostock 抓取全 A 股财务/报告数据，并按表类型分别落盘：
  - `profit_data`
  - `operation_data`
  - `growth_data`
  - `balance_data`
  - `cash_flow_data`
  - `dupont_data`
  - `performance_express_report`
  - `forecast_report`
- 财务/报告数据抓取截止日期固定为 `2026-04-01`。
- 生成 `manifest.json` 记录抓取范围、股票数量、数据规模、截止日期和执行阶段。

### 3. universe 历史文件
- 使用 baostock 抓取并构建：
  - `HS300` 成分股快照与变更记录
  - `SZ50` 成分股快照与变更记录
  - `ZZ500` 成分股快照与变更记录
  - 全 A 可交易股票池历史
- 为三类指数与全 A 分别生成独立历史文件，不再依赖“三指数并集公司”作为正式底座。

### 4. 正式股票池入口与因子面板
- 为三类正式股票池分别维护配置：
  - `formal_hs300.yaml`
  - `formal_sz50.yaml`
  - `formal_zz500.yaml`
- 各配置通过 universe 历史文件从全 A 股主数据中过滤出对应股票池。
- 基于全 A 股主数据生成正式因子面板。
- 因子面板至少包含：
  - 价格与收益率相关字段
  - 技术类因子
  - 估值类字段
  - 行业信息
  - 未来收益标签
- 使用历史成员口径过滤股票池后，再构建 `stock × factor × time` 张量。

### 5. CSV 与 Parquet 双形态落盘
- 正式数据先落盘为 `CSV`，确保抓取、检查和手工抽样验证方便。
- 在 `CSV` 稳定后生成对应 `Parquet` 文件，用于后续高性能读取和大规模训练。
- `CSV` 与 `Parquet` 的文件命名、时间范围、字段合同和 manifest 保持一致。

### 6. DuckDB 查询层
- 建立本地 `DuckDB` catalog，例如：
  - `code/data/formal/catalog.duckdb`
- 至少注册以下逻辑对象：
  - `universes.*`
  - `master.*`
  - `factors.*`
  - `financial.*`
  - `reports.*`
  - `full_master.*`
- `DuckDB` 层优先读取 `Parquet`，必要时兼容直接读取 `CSV`。
- 为常见研究和服务查询提供稳定视图，例如：
  - `vw_all_a_tradable_on_date`
  - `vw_hs300_on_date`
  - `vw_shared_master_coverage`
  - `vw_factor_panel_coverage`
  - `vw_financial_dataset_coverage`
- 记录 DuckDB 中每个对象与其底层 CSV/Parquet 文件的映射关系，并纳入 manifest。

### 7. GPU 计算后端
- 将主要数值计算路径统一迁移到 `PyTorch`。
- 增加运行时设备配置：
  - `device=cpu`
  - `device=cuda`
  - `device=auto`
- 在 `device=auto` 下优先使用 CUDA。
- 将以下计算优先迁移到 GPU 张量：
  - 张量重构误差计算
  - 因子贡献计算
  - 相似度与聚类前的矩阵运算
  - 大规模候选池评分计算
- 对性能热点预留 `Triton` 或 `CUDA` 实现接口，优先落在批量评分、矩阵规约和候选池聚合等热点路径。

### 8. 选股输出与结果合同
- 保持统一候选池输出：
  - `selection_candidates.csv`
  - `selection_candidates.json`
- 每条候选记录至少包含：
  - `trade_date`
  - `stock_code`
  - `market_id`
  - `universe_id`
  - `total_score`
  - `selection_signal`
  - `time_regime_score`
  - `cluster_label`
  - Top3 因子及其贡献值
- 候选池必须保证 `trade_date + stock_code` 唯一

### 9. Web 后端与前端
- 后端保留并完善：
  - `POST /api/runs`
  - `GET /api/runs`
  - `GET /api/runs/{run_id}`
  - `GET /api/runs/{run_id}/metrics`
  - `GET /api/runs/{run_id}/selection`
  - `GET /api/markets`
- `/api/markets` 返回唯一 `option_id`
- formal profile 由后端作为唯一真源，不允许 profile 与底层文件路径失配
- Web 查询层优先从 `DuckDB` 读取统计、覆盖率、主数据摘要与选股辅助信息，而不是直接扫描大型 CSV。
- 前端配置页支持切换：
  - `formal_hs300`
  - `formal_sz50`
  - `formal_zz500`
  - `sample_cn_smoke`
  - `sample_us_equity`

### 10. 测试与验证
- 单元测试：
  - 正式配置解析
  - 历史成员过滤
  - baostock 快照变更推导
  - 全 A 主数据与 universe 历史的联动一致性
  - `CSV` / `Parquet` 字段合同一致性
  - `DuckDB` 对 CSV/Parquet 的对象注册与查询一致性
  - `DuckDB` 视图的日期范围、行数与底层数据一致性
  - 统一候选池唯一性
  - profile 与数据路径一致性
- 集成测试：
  - baostock smoke 抓取落盘
  - `CSV -> Parquet -> DuckDB` 链路可运行
  - 后端 API 返回结构
  - formal profile 提交后生成的 `submitted_config.yaml` 一致性
- 运行验证：
  - `.venv/bin/python -m unittest discover -s code/tests`
  - `cd web/frontend && npm run build`
  - 至少一个正式股票池配置的真实实跑
  - GPU 可用性探测与 CPU 回退验证

## Claude-Codex Deliberation
- 当前用户已明确不再以 `CSI_A500` 作为正式实验主目标，因此正式 A 股目标必须切换到 `HS300 / SZ50 / ZZ500`，而旧样例数据只保留为 smoke test 输入。
- 用户已经明确希望正式底座采用“全 A 股主数据 + 各 universe 历史”的结构，而不是“三指数并集公司”作为主存储范围；这能避免重复存储，也更利于后续扩展美股。
- baostock 已经成为当前明确的数据来源，因此计划必须围绕“先抓本地数据，再做实验”来组织，而不是继续等待外部手工数据提供。
- 用户已经明确要求正式全量窗口为 `2015-01-01` 到 `2026-04-01`，因此财务和报告数据的截止日期不再保持开放式“到当天”，而应固定到该日期。
- GPU 能力应先通过 `PyTorch` 统一接入，这样最容易在现有 Python 代码基础上落地，也最容易做 CPU 回退；`Triton/CUDA` 适合在 profiling 之后用于热点算子，不应在初版就取代全部数值实现。

## Pending User Decisions
- 美股后续默认股票池暂定为外部传入列表，不先指定 `S&P 500` 或 `NASDAQ 100`。
- `Parquet` 转换层优先采用 `pyarrow` 还是 `fastparquet`。
- `Triton/CUDA` 首个热点算子优先落在哪条路径：批量评分、张量重构、还是相似度矩阵计算。

## Implementation Notes
- 不要把 `HS300`、`SZ50`、`ZZ500` 的逻辑散落硬编码在模型层；应集中在配置和适配层。
- 不要让 formal profile 和 `universe_id`、`universe_path`、`data.path` 出现失配。
- 不要把正式全量数据按指数重复保存成多套完整行情/财务文件；应使用“全 A 主数据 + universe 历史过滤”。
- 不要把 GPU 逻辑写死在唯一设备上；必须保留 CPU 回退。
- 不要把样例数据和正式全量数据混在一个目录或同一 manifest 下。
- 正式数据窗口当前固定为 `2015-01-01` 到 `2026-04-01`；如果后续扩展日期区间，应通过显式数据版本升级完成，而不是静默覆盖。
- 正式数据目录和 smoke 数据目录必须分离。
