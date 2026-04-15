# 基于张量分解的股票因子降维与模式发现 Draft

## 1. 文档目的

这份 `draft.md` 用来统一当前毕设项目的研究问题、实验主线、系统边界、数据路线与后续实施优先级。它是后续 `plan.md`、分阶段实现、RLCR 执行和论文写作的上游草案，不直接展开到底层实现细节，但必须把路线、范围、依赖关系和优先级讲清楚。

这份 draft 要回答的核心问题是：

1. 这个项目在论文层面到底要证明什么。
2. 当前系统、实验和论文之间如何保持统一叙事。
3. formal 数据层、实验样本层、展示系统层如何分层。
4. 接下来哪些任务是必做，哪些是可选扩展，哪些应该暂缓。

## 2. 项目定位

本项目不是一个普通的选股网站，也不是一个只停留在理论层面的论文原型。更准确地说，它是一个围绕论文主线构建的研究型实验系统，包含三层表达：

1. 论文层：回答“基于张量分解的股票因子降维与模式发现”这一研究问题。
2. 实验层：把方法落实为可重复运行、可评估、可比较的实验流程。
3. 系统层：把 formal 数据、实验配置、运行结果和查询接口组织成可展示、可调用、可复现的系统。

因此，论文、实验系统和 Web 系统不是彼此割裂的三条线，而是同一研究问题的三个表达层。

## 3. 研究核心对象与方法

### 3.1 统一研究对象

整个项目的统一研究对象是：

- `股票 - 因子 - 时间` 三维张量

三个维度分别表示：

1. 股票维
2. 因子维
3. 时间维

论文方法、实验配置、评估指标、结果解释和系统输出都围绕这一三维张量展开。

### 3.2 核心方法路径

当前论文与实验的核心方法固定为：

1. `CP` 分解
2. `Tucker` 分解

这两类方法的定位是：

1. 首先用于股票因子降维。
2. 其次用于潜在模式发现。
3. 最后再考察它们在后续窗口中的预测或决策价值。

项目主问题不是“做一个收益预测器”，而是研究：

1. 如何基于三维张量完成股票因子降维。
2. 如何从分解结果中发现股票、因子、时间之间的潜在结构。
3. 这些结构在后续窗口中是否仍具有解释价值或应用价值。

### 3.3 参考依据

方法方向主要参考 `./参考文献` 中的 PDF 文献，尤其是使用 `CP` / `Tucker` 对 `股票 - 因子 - 时间` 三维张量进行分解的研究。相关文献构成论文方法章节、实验设计章节和结果解释章节的重要理论依据。

## 4. 数据范围与样本边界

### 4.1 formal 时间窗口

当前 formal 数据与主实验的正式时间窗口固定为：

- `2015-01-01` 到 `2026-04-01`

这一窗口需要在文档、配置、DuckDB catalog、实验输出和前端展示中保持一致，不能继续漂移成“当前最新可用日期”。

### 4.2 长期股票覆盖范围

系统长期股票范围保留全 A 股，不因为当前实验样本较窄而把长期数据边界写死成三个指数。

系统层必须清楚区分三层范围：

1. 长期股票覆盖范围：全 A 股
2. 当前 formal 实验样本池：按实验配置选出的训练/预测股票集合
3. 当前重点实验指数：`HS300`、`SZ50`、`ZZ500`

### 4.3 当前主实验样本

当前主实验主要围绕以下三个指数分别开展：

1. `HS300`
2. `SZ50`
3. `ZZ500`

这三个指数是当前正式实验样本，不等于系统未来只支持这三个股票池。

### 4.4 切分策略

系统必须支持可配置切分策略，而不是只写死一种训练/预测划分方式。当前约束为：

1. 比例可配置
2. 维度可配置
3. 支持按时间切分、按股票切分和混合切分

论文主实验默认采用按时间切分，但系统要保留其他切分能力，供后续稳健性实验和扩展研究使用。

## 5. 统一叙事框架

### 5.1 当前验证目标

在当前代表性样本上，项目要验证三件事：

1. 张量分解是否能有效完成股票因子降维。
2. 张量分解是否能发现有解释力的结构模式。
3. 这些模式在后续窗口是否仍有预测、排序或决策价值。

### 5.2 长期扩展方向

系统长期保留更广股票覆盖范围，意味着方法一旦在当前样本池中被验证，就可以迁移到更广的股票集合和更丰富的任务上。但这种扩展必须建立在当前 formal 样本验证稳定的前提下。

因此，论文叙事应采用“双段式结构”：

1. 在当前 formal 样本上完成方法验证。
2. 在此基础上讨论更广股票范围与更强应用场景下的受控扩展。

## 6. 数据分层与系统边界

### 6.1 当前目标架构

长期目标架构固定为：

1. 纯 Go API 网关负责 HTTP 服务。
2. Python 负责数据处理与实验执行。
3. DuckDB 负责 formal 查询层与结构化数据视图。
4. `code/outputs` 负责实验产物落盘。
5. `Parquet + DuckDB` 作为主要数据层，不引入 MySQL。

### 6.2 Go 职责

Go 网关负责：

1. 提供 HTTP 接口。
2. 做请求校验与统一响应包装。
3. 读取 DuckDB 与 `code/outputs`。
4. 管理 run 生命周期与状态持久化。
5. 调用 Python runner 执行实验。

### 6.3 Python 职责

Python 负责：

1. 抓取与处理 formal 数据。
2. 构造张量输入。
3. 执行 `CP` / `Tucker` 分解实验。
4. 输出 `metrics`、`selection`、`factor_summary`、`time_regimes` 等结果文件。

### 6.4 数据层职责

数据层采用：

1. `CSV` 作为 canonical raw 和中间结果的可检查落盘格式。
2. `Parquet` 作为训练和分析的高效存储格式。
3. `DuckDB` 作为统一查询与 catalog 注册层。

这里已经明确放弃 `MySQL`。原因是本项目的主要 workload 是研究型分析、批量切片、张量构建与 GPU 训练，而不是高并发事务写入。

## 7. 预处理、泄漏控制与张量输入

数据预处理必须被视为独立阶段，而不是散落在实验脚本里的隐式逻辑。它至少包括：

1. 样本筛选
2. 时间对齐
3. 字段清洗
4. 缺失值处理
5. 异常值处理
6. 因子方向统一
7. 标准化
8. 标签与元信息分离

硬约束包括：

1. 不允许未来信息穿越训练 / 预测边界。
2. 未来收益标签只用于评估，不得进入输入张量。
3. split-aware 的训练、投影与评估逻辑必须保持一致。

## 8. 实验主线

实验主线分为三层：

### 8.1 张量构建

按当前实验样本与切分配置构建 `股票 - 因子 - 时间` 三维张量。

### 8.2 张量分解

对张量应用 `CP` 与 `Tucker` 分解，并产出可解释的股票、因子和时间结构。

### 8.3 评估与比较

比较以下三类结果：

1. 分解质量
2. 模式发现与解释能力
3. 后续窗口中的预测、排序与决策有效性

## 9. 评估框架

评估体系建议分为三层：

### 9.1 分解质量

例如：

1. 重构质量
2. rank 行为
3. 稳定性

### 9.2 模式发现与解释

例如：

1. 因子贡献
2. 股票结构
3. 时间模式
4. 不同方法之间的解释差异

### 9.3 预测或决策有效性

例如：

1. 训练阶段提取出的结构在后续窗口中是否仍有效
2. 不同实验样本上的泛化表现
3. 候选股票排序效果

这些评估同时服务于论文结果章节、系统结果页和 API 输出契约。

## 10. formal 数据主链

当前 formal 数据主链为：

1. `baostock` 原始层
2. universe history / metadata / shared kline / financial / reports
3. full master
4. factor panel
5. Parquet 镜像
6. DuckDB 注册
7. 实验输入与输出

这一主链已经形成项目的数据基础骨架。后续扩展必须继续沿着这条主链做增量增强，而不是另起 MySQL 或另起一套独立数据工程。

## 11. Baostock 扩展策略

### 11.1 基本决策

对同类项目的参考方式是：

1. 不调用它们的项目骨架和数据库设计。
2. 只吸收它们做得好的接口覆盖、封装习惯和抓取经验。
3. 所有新增数据都继续落在本项目的 canonical root 中。

### 11.2 参考项目

在后续 Baostock 扩展与代码指导中，需要明确参考以下几个同类项目，但参考方式仅限于学习其优点并融入本项目，不直接调用其脚本、数据库结构或整套工程骨架：

1. `shimencaiji/baostock`
   - 参考点：按接口拆脚本、按数据类型组织抓取逻辑
   - 仓库：`https://github.com/shimencaiji/baostock`

2. `HuggingAGI/mcp-baostock-server`
   - 参考点：统一 API 封装、股票代码规范化、输入校验
   - 仓库：`https://github.com/HuggingAGI/mcp-baostock-server`

3. `chenjt3533/BaoStockDemo`
   - 参考点：Baostock 官方式接口覆盖样例，尤其是 `adjust_factor`、`dividend`、`macro` 类接口
   - 仓库：`https://github.com/chenjt3533/BaoStockDemo`

4. `flytrap/vnpy_baostock`
   - 参考点：最小字段抓取、频率映射、按用途裁剪返回字段
   - 仓库：`https://github.com/flytrap/vnpy_baostock`

5. `zhaoxusun/stock-quant`
   - 参考点：轻量标准化、单次抓取后的统一整理与 ad hoc 数据处理习惯
   - 仓库：`https://github.com/zhaoxusun/stock-quant`

这些项目在本文档中的作用是“外部参考来源”，用于约束后续代码指导时应吸收哪些优点，而不是作为运行依赖。

### 11.3 吸收原则

从同类项目中吸收的重点包括：

1. `BaoStockDemo` 的接口覆盖清单
2. `mcp-baostock-server` 的统一 API 封装和股票代码规范化思路
3. `vnpy_baostock` 的最小字段与频率映射思路
4. `stock-quant` 的轻量标准化和 ad hoc 数据处理思路
5. `shimencaiji/baostock` 的按接口拆脚本思路

不吸收的内容包括：

1. MySQL 表结构
2. 单体总 pipeline
3. demo 式绝对路径输出
4. 每个函数独立 login/logout 的粗粒度方式

### 11.4 新增数据类别

后续要扩展的 Baostock 数据包括三类：

1. `adjust_factor`
2. `dividend`
3. `macro`

其中优先级明确为：

1. `adjust_factor`
2. `dividend`
3. `macro`

原因是 `adjust_factor` 和 `dividend` 更直接影响价格口径统一、事件解释与收益解释，和当前系统主线更贴近。

## 12. Baostock 扩展任务清单

### 12.1 必做

这些任务直接支撑 formal 数据能力扩展，且与论文主线、训练输入和系统展示都有较强关系，必须进入近期排期。

1. 抽出 Baostock 公共能力模块  
   建议新增：
   - `code/data/baostock_common.py`

   目标：
   - 统一 `login/logout`
   - 统一 `query_with_relogin`
   - 统一股票代码规范化
   - 统一 progress / append / resume 逻辑

2. 新增 `adjust_factor` 抓取脚本  
   建议新增：
   - `code/data/fetch_baostock_adjust_factor.py`

   输出目录：
   - `code/data/formal/baostock/adjust_factor/<year>.csv`
   - `code/data/formal/baostock/adjust_factor/_progress.json`

   恢复单元：
   - `code|year`

3. 新增 `dividend` 抓取脚本  
   建议新增：
   - `code/data/fetch_baostock_dividend.py`

   输出目录：
   - `code/data/formal/baostock/dividend/report/<year>.csv`
   - `code/data/formal/baostock/dividend/operate/<year>.csv`
   - `code/data/formal/baostock/dividend/dividend/<year>.csv`
   - `code/data/formal/baostock/dividend/_progress.json`

   恢复单元：
   - `code|year|year_type`

4. 新增 `macro` 抓取脚本  
   建议新增：
   - `code/data/fetch_baostock_macro.py`

   首批支持：
   - `deposit_rate`
   - `loan_rate`
   - `required_reserve_ratio`
   - `money_supply_month`
   - `money_supply_year`
   - `shibor`

   输出目录：
   - `code/data/formal/baostock/macro/<dataset>/<year>.csv`
   - `code/data/formal/baostock/macro/_progress.json`

   恢复单元：
   - `dataset|year`

5. 扩展 canonical root 文档与 manifest 语义  
   需要更新：
   - `README.md`
   - `code/data/formal/baostock/README.md`
   - `code/data/formal/baostock/manifest.json` 的统计与文件列表语义

6. 扩展 DuckDB catalog 注册  
   需要更新：
   - `code/data/register_formal_duckdb_catalog.py`

   新增 raw / coverage view：
   - `vw_baostock_adjust_factor_raw`
   - `vw_baostock_dividend_raw`
   - `vw_baostock_macro_raw`
   - `vw_formal_adjust_factor_coverage`
   - `vw_formal_dividend_coverage`
   - `vw_formal_macro_coverage`

7. 构建 `adjust_factor` 对齐面板  
   建议新增：
   - `code/data/build_adjust_factor_panel.py`

   输出：
   - `code/data/formal/master/adjust_factor_daily.csv`

   用途：
   - 补充 full master
   - 统一复权解释口径

8. 构建 `dividend` 事件面板  
   建议新增：
   - `code/data/build_dividend_event_panel.py`

   输出：
   - `code/data/formal/reports/dividend_events.csv`

   用途：
   - 事件解释层
   - 可视化和分析查询

9. 补齐对应测试  
   建议新增：
   - `code/tests/test_baostock_common.py`
   - `code/tests/test_fetch_baostock_adjust_factor.py`
   - `code/tests/test_fetch_baostock_dividend.py`
   - `code/tests/test_fetch_baostock_macro.py`
   - `code/tests/test_register_formal_duckdb_catalog_aux.py`
   - `code/tests/test_build_adjust_factor_panel.py`
   - `code/tests/test_build_dividend_event_panel.py`

### 12.2 可选

这些任务有价值，但可以在必做任务闭环后再推进。

1. 构建财务 point-in-time 中间层  
   建议新增：
   - `code/data/build_financial_point_in_time.py`

   目标：
   - 将财务 raw / report raw 转成按公告日生效的时点有效区间数据

2. 构建宏观对齐面板  
   建议新增：
   - `code/data/build_macro_aligned_panel.py`

   输出：
   - `code/data/formal/master/macro_daily.csv`
   - `code/data/formal/master/macro_monthly.csv`

3. 扩展 `full_master` supplement  
   将以下字段有选择地并入：
   - 复权因子
   - 分红事件标记
   - 少量共享宏观特征

4. 扩展 factor panel supplement  
   在财务 point-in-time 稳定后，把一部分稳定基本面特征并入 factor panel。

5. 新增 aux stage 批处理入口  
   建议新增：
   - `code/data/run_baostock_stage2_aux_dataset_year.sh`
   - `code/data/run_baostock_stage3_aux.sh`

6. 新增前端 / Go 侧 formal coverage 展示  
   把 `adjust_factor`、`dividend`、`macro` 覆盖情况直接暴露到 formal coverage API 和前端展示中。

### 12.3 暂缓

这些方向不是没有价值，而是当前阶段投入产出比不高，容易稀释主线，应明确暂缓。

1. 引入 MySQL 或双存储体系
2. 引入外部项目的整套 pipeline 或运行骨架
3. 一开始就把所有宏观字段并入 `full_master`
4. 一开始就把所有新增 raw 字段并入 tensor 输入
5. 为新增 Baostock 数据单独设计一套与主链平行的工程结构
6. 把 `Triton` 提前用于数据层，而不是保持在模型服务层
7. 为未稳定的数据能力过早设计复杂前端页面

## 13. 排期建议

### 13.1 第一阶段

目标：尽快形成可运行的 Baostock 扩展最小闭环。

任务：

1. `baostock_common.py`
2. `fetch_baostock_adjust_factor.py`
3. `fetch_baostock_dividend.py`
4. `register_formal_duckdb_catalog.py` 扩展 aux raw views
5. 文档更新
6. 对应最小测试

验收标准：

1. `adjust_factor`、`dividend` raw 数据能够按年落盘
2. 能 resume
3. 能注册到 DuckDB
4. coverage 可查

### 13.2 第二阶段

目标：把新增 raw 数据接到解释层和 supplement 层。

任务：

1. `build_adjust_factor_panel.py`
2. `build_dividend_event_panel.py`
3. `full_master` supplement 设计
4. 对应测试与 DuckDB view

验收标准：

1. `adjust_factor_daily` 可用
2. `dividend_events` 可用
3. 能被查询接口和后续分析直接读取

### 13.3 第三阶段

目标：扩展至财务 PIT 和宏观对齐层。

任务：

1. `build_financial_point_in_time.py`
2. `fetch_baostock_macro.py`
3. `build_macro_aligned_panel.py`
4. 视需要扩展 factor panel supplement

验收标准：

1. 财务原始表到时点有效区间的链路跑通
2. 宏观数据可以在 DuckDB 中查询
3. 能支持更细的解释层与稳健性实验

## 14. 历史问题复盘

当前项目历史上经历过几类反复调整的问题：

1. formal 样本范围曾经不够稳定
2. shared kline、full master、factor panel 的职责边界曾不够清晰
3. Python backend 和长期 Go gateway 目标曾并存且边界模糊
4. 论文主线与工程结果之间曾存在叙事脱节
5. 财务 / 报告数据与原始落盘、resume、catalog 注册之间曾不完全闭环

这次新增 Baostock 扩展时，必须避免重犯这些问题。新增能力必须继续服从：

1. canonical root 一致
2. manifest 一致
3. DuckDB 注册一致
4. resume 语义一致
5. 下游进入 full master / factor panel 的规则一致

## 15. 成功标准

如果这份新的 draft 是成功的，那么它应该让项目具备以下特征：

1. 论文叙事始终围绕 `股票 - 因子 - 时间` 张量和 `CP / Tucker` 方法展开。
2. 系统实现始终围绕 formal 数据主链、配置模型、结果契约和查询能力展开。
3. Baostock 扩展不是另起一套工程，而是自然并入当前 formal 数据架构。
4. 接下来的实现排期可以明确区分必做、可选与暂缓，不再混乱推进。
5. 数据扩展优先服务当前主线：formal 数据稳定、实验闭环、解释层增强，而不是盲目扩充数据种类。

## 16. 关于 Baostock 抓取速度的判断

新的 draft 本身不会直接让单次 Baostock API 调用变快，因为真正的网络返回速度和 Baostock 服务端响应时间并不会因为文档而改变。

但如果后续严格按这版 draft 实施，整体数据落地效率会明显提高，主要体现在：

1. 通过统一 session 管理和重登录机制减少无效重连。
2. 通过 `progress + resume` 避免重复抓取。
3. 通过 `dataset / year / yearType` 分片减小单次失败损失。
4. 通过 canonical root 统一落盘减少后续反复搬运和重构。
5. 通过 DuckDB catalog 注册让下游查询和验证更快，不需要反复扫原始 CSV。
6. 通过优先做 `adjust_factor` 和 `dividend`，先把高价值、低歧义的数据补齐，减少后续返工。

因此，答案是：

- 这版 draft 不能让 Baostock 服务端响应本身更快。
- 但它能让整个项目“从 Baostock 抓取、落盘、恢复、校验、注册、下游使用”的总吞吐更高，返工更少，重跑更快。

也就是说，它提升的是整条数据工程链路的效率，而不是单个 HTTP/Socket 请求的瞬时速度。
