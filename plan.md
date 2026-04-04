# 基于张量分解的多指数股票因子降维、选股与 GPU 加速实施计划

## Goal Description
将当前样例级实验管线升级为面向真实实证、选股应用与后续产品化的研究平台，正式 A 股实验范围不再以中证 A500 为唯一目标，而是以以下三类核心指数股票池为主：

1. 沪深300（`HS300`）
2. 上证50（`SZ50`）
3. 中证500（`ZZ500`）

在此基础上，项目需要同时完成三条主线：

1. 使用 baostock API 将指数成分股、变更记录、基础资料、行业信息、财务数据和必要的日线/估值数据抓取到本地，形成正式数据入口。
2. 在本地数据之上构建“股票 × 因子 × 时间”的张量实验管线，完成 CP/Tucker/PCA 对比、模式发现和选股输出。
3. 为大规模计算加入 GPU 计算能力，优先采用 `PyTorch` 作为统一 GPU 计算后端，后续对热点算子预留 `Triton` 或原生 `CUDA` 优化路径。

说明：
今天是 `2026-04-04`，所以“2015 到 2026”在执行层面解释为“`2015-01-01` 到 2026 年本地数据中最后一个可用交易日”；配置可以写到 `2026-12-31`，但实际运行必须自动截断到真实可用日期。

## Acceptance Criteria

- AC-1: A 股正式实验配置支持 `HS300`、`SZ50`、`ZZ500` 三类股票池，并可显式指定 `start_date=2015-01-01`、`end_date=2026-12-31`，实际运行时自动截断到本地数据最后一个可用交易日。
- AC-2: baostock 数据抓取链路可将三类指数的成分股快照、变更记录、股票基础资料、行业信息、财务数据和报告数据保存到本地目录，并生成可复用的 manifest。
- AC-3: A 股数据层按“历史时点成分股”口径处理 `HS300`、`SZ50`、`ZZ500`，不能使用单一静态名单覆盖整个回测期。
- AC-4: 核心实验管线不依赖某个单一股票池或 A 股特有代码格式；股票池、交易日历、符号规范化和数据源都通过适配层提供。
- AC-5: 新增 `us_equity` 市场适配接口后，不修改 CP/Tucker/PCA 核心模型代码即可接入美股数据。
- AC-6: 选股层可基于模型结果产出指定日期的候选股票列表，至少包含股票代码、综合评分、主要贡献因子、所属市场与所属股票池。
- AC-7: Web 后端提供实验运行、结果查询、选股查询三个基本能力；前端可完成配置提交、结果展示、候选股浏览，并能在三类正式股票池之间切换。
- AC-8: 计算后端支持 GPU 执行。默认使用 `PyTorch` 在 CUDA 可用时运行大规模张量/矩阵计算；CPU 路径仍可回退；对热点算子预留 `Triton/CUDA` 优化接口。
- AC-9: 自动化测试覆盖正式配置解析、历史成分过滤、baostock 数据处理、统一候选池输出、核心 API 返回格式，以及 GPU 可用性探测与 CPU 回退逻辑。
- AC-10: 输出目录中除实验指标外，新增可供 Web 端直接读取的结构化结果文件，不要求前端解析日志文本。

## Path Boundaries

### Upper Bound
- 完成三类 A 股指数股票池的正式本地数据接入。
- 支持 `cn_a` 与 `us_equity` 两类市场配置。
- 提供 FastAPI 后端与 React 前端。
- 默认计算后端支持 `PyTorch + CUDA`。
- 对热点算子提供 `Triton` 或原生 `CUDA` 的优化预留。
- 支持单次实验运行、历史实验查看、指定日期选股、因子解释展示。

### Lower Bound
- 先完成 `HS300`、`SZ50`、`ZZ500` 三类正式入口中的至少一类全链路跑通。
- baostock 抓取工具、正式配置、张量实验、统一候选池、Web API 和前端基本页面都必须存在。
- GPU 路径最低要求是：
  - 可检测 CUDA 是否可用
  - 在可用时使用 `PyTorch` 张量在 GPU 上运行主要数值计算
  - 在不可用时安全回退 CPU

### Allowed Choices
- 后端固定为 Python，优先 `FastAPI`。
- 前端固定为 `React + Vite`。
- GPU 计算优先使用 `PyTorch`。
- `Triton` 或 `CUDA` 仅用于后续性能增强，不要求一开始全量重写算法。
- 实验结果持久化先用文件系统和轻量元数据文件。
- 不在这一版加入登录鉴权、多人协作、交易下单或生产部署编排。

## Feasibility Hints and Suggestions
- baostock 抓取应分阶段执行：
  - Stage 1：指数成分股快照、变更记录、股票基础资料、行业信息
  - Stage 2：财务数据、报告数据
  - Stage 3：日线/估值面板抓取与本地因子面板构建
- 三个正式股票池应各自拥有独立配置和独立数据入口，不共享模糊的“formal_cn_a”语义。
- 正式配置必须保持“股票池标识、成员文件路径、因子面板路径”三者一致，不能只改 `universe_id` 文本而读取别的指数数据。
- 选股逻辑不要绑定单一分解方法。统一从 `ModelResult` 生成候选池，并对不同模型结果做聚合或一致化输出。
- GPU 计算不要一开始就拆成三套实现：
  - 先把数值核心改成 `PyTorch`
  - 再根据 profiling 决定哪些热点算子值得下沉到 `Triton/CUDA`
- Web 端优先读取结构化产物，例如：
  - `run_manifest.json`
  - `selection_candidates.json`
  - `factor_summary_*.json`
  - `factor_association_*.json`

## Dependencies and Sequence

1. 先完成 baostock 本地数据抓取链路和正式数据目录结构。
2. 再完成三类正式股票池配置与历史成员文件生成。
3. 在正式数据之上构建因子面板和张量实验输入。
4. 将数值计算主路径迁移到 `PyTorch`，加入 GPU/CPU 双路径。
5. 完成统一候选池输出和实验结果结构化。
6. 再做 Web API 和前端页面整合。
7. 最后保留 `us_equity` 接口作为后续扩展入口。

### External Dependencies
- baostock API
- 本地网络可访问 baostock 服务
- Python 依赖：`baostock`、`numpy`、`PyYAML`、`fastapi`、`uvicorn`、`httpx`
- GPU 依赖：`torch`
- 可选性能增强：`triton` 或 CUDA toolchain
- 前端依赖：`node`、`vite`、`react`

## Task Breakdown

### 1. baostock 数据抓取与本地落盘
- 使用 baostock 抓取：
  - `HS300`
  - `SZ50`
  - `ZZ500`
  三类指数的成分股快照
- 基于快照推导成分变更记录
- 抓取股票基础资料、行业信息、财务数据、报告数据
- 将输出落盘到 `code/data/formal/baostock/`
- 生成 `manifest.json` 记录抓取范围、股票数量、数据规模和执行阶段

### 2. 正式股票池入口
- 为三类正式股票池分别维护配置：
  - `formal_hs300.yaml`
  - `formal_sz50.yaml`
  - `formal_zz500.yaml`
- 各配置必须分别指向：
  - 对应成员历史文件
  - 对应因子面板文件
- 默认正式入口不再依赖 `CSI_A500`
- 若保留 `CSI_A500`，仅作为兼容入口，不再是主实验基线

### 3. 因子面板与张量实验
- 基于 baostock 本地数据生成正式因子面板
- 因子面板至少包含：
  - 价格与收益率相关字段
  - 技术类因子
  - 估值类字段
  - 行业信息
  - 未来收益标签
- 使用历史成员口径过滤股票池后，再构建 `stock × factor × time` 张量

### 4. GPU 计算后端
- 将主要数值计算路径统一迁移到 `PyTorch`
- 增加运行时设备配置：
  - `device=cpu`
  - `device=cuda`
  - `device=auto`
- 在 `device=auto` 下优先使用 CUDA
- 将以下计算优先迁移到 GPU 张量：
  - 张量重构误差计算
  - 因子贡献计算
  - 相似度与聚类前的矩阵运算
  - 大规模候选池评分计算
- 对性能热点预留 `Triton` 或 `CUDA` 实现接口，但不要求初版全部启用

### 5. 选股输出与结果合同
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

### 6. Web 后端与前端
- 后端保留并完善：
  - `POST /api/runs`
  - `GET /api/runs`
  - `GET /api/runs/{run_id}`
  - `GET /api/runs/{run_id}/metrics`
  - `GET /api/runs/{run_id}/selection`
  - `GET /api/markets`
- `/api/markets` 返回唯一 `option_id`
- formal profile 由后端作为唯一真源，不允许 profile 与底层文件路径失配
- 前端配置页支持切换：
  - `formal_hs300`
  - `formal_sz50`
  - `formal_zz500`
  - `sample_cn_smoke`
  - `sample_us_equity`

### 7. 测试与验证
- 单元测试：
  - 正式配置解析
  - 历史成员过滤
  - baostock 快照变更推导
  - 统一候选池唯一性
  - profile 与数据路径一致性
- 集成测试：
  - baostock smoke 抓取落盘
  - 后端 API 返回结构
  - formal profile 提交后生成的 `submitted_config.yaml` 一致性
- 运行验证：
  - `.venv/bin/python -m unittest discover -s code/tests`
  - `cd web/frontend && npm run build`
  - 至少一个正式股票池配置的真实实跑
  - GPU 可用性探测与 CPU 回退验证

## Claude-Codex Deliberation
- 当前用户已明确不再以 `CSI_A500` 作为正式实验主目标，因此正式 A 股目标必须切换到 `HS300 / SZ50 / ZZ500`。
- baostock 已经成为当前明确的数据来源，因此计划必须围绕“先抓本地数据，再做实验”来组织，而不是继续等待外部手工数据提供。
- GPU 能力应先通过 `PyTorch` 统一接入，这样最容易在现有 Python 代码基础上落地，也最容易做 CPU 回退。
- `Triton/CUDA` 适合在 profiling 之后用于热点算子，不应在初版就取代全部数值实现。

## Pending User Decisions
- 是否需要保留 `CSI_A500` 兼容配置但不作为正式主入口；当前默认保留兼容但不再优先使用。
- 美股后续默认股票池暂定为外部传入列表，不先指定 `S&P 500` 或 `NASDAQ 100`。
- GPU 首版默认采用 `PyTorch`，是否要求后续强制加入 `Triton` 或原生 `CUDA`；当前默认仅预留接口。

## Implementation Notes
- 不要把 `HS300`、`SZ50`、`ZZ500` 的逻辑散落硬编码在模型层；应集中在配置和适配层。
- 不要让 formal profile 和 `universe_id`、`universe_path`、`data.path` 出现失配。
- 不要把 GPU 逻辑写死在唯一设备上；必须保留 CPU 回退。
- 不要默认 2026 全年数据已经存在；所有日期必须按本地真实可用数据截断。
- 正式数据目录和 smoke 数据目录必须分离。
