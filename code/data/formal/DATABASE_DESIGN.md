# 毕设数据库设计

## 1. 设计目标

本项目不是面向高并发交易写入的业务系统，而是面向单机研究、批量分析、张量建模和 Web 只读查询的实验平台。因此数据库设计不采用传统 `MySQL/PostgreSQL` 作为唯一主库，而采用三层结构：

1. `CSV` 作为正式数据的标准落盘层
2. `Parquet` 作为高性能列式存储层
3. `DuckDB` 作为本地分析型数据库与统一查询目录

对应 `README.md` 与 `plan.md` 中已经确定的路线，正式查询层优先采用 `Parquet + DuckDB`。

## 2. 总体架构

### 2.1 分层架构

正式数据库架构分为三层：

#### 第一层：源数据与标准文件层

路径：`code/data/formal/`

职责：

- 保存正式 `CSV` 数据
- 保留原始抓取结果与中间构建结果
- 作为人工抽样核验与字段合同检查的基准层

包含目录：

- `universes/`
- `master/`
- `factors/`
- `financial/`
- `reports/`
- `baostock/`

#### 第二层：列式镜像层

路径：`code/data/formal/parquet/`

职责：

- 将已经校验通过的 `CSV` 转换为 `Parquet`
- 为 DuckDB、训练和统计分析提供高性能读路径
- 保持与 CSV 一一对应的数据集边界

#### 第三层：DuckDB 查询层

路径：`code/data/formal/catalog.duckdb`

职责：

- 统一注册 `CSV/Parquet` 外部表与视图
- 向研究分析和 Web 后端提供稳定对象名
- 屏蔽底层字段命名差异和文件位置差异

## 3. 数据库选型理由

选择 `DuckDB` 的原因如下：

1. 本项目核心负载是批量读取、统计聚合、覆盖率检查和回测查询，属于典型 OLAP 场景。
2. 正式数据天然以文件形式存在，`DuckDB` 可直接查询 `Parquet/CSV`，不需要额外导入到服务型数据库。
3. 项目当前是单机研究和毕业设计场景，不存在高并发事务写入需求。
4. `DuckDB` 与 `Parquet` 结合后，能够在不复制大体量历史数据的前提下提供稳定 SQL 查询能力。

因此本设计明确规定：

- 不把全部历史主数据直接塞入传统 OLTP 数据库
- 不按指数重复存储完整市场主数据
- 通过 `全A主数据 + universe历史过滤 + DuckDB视图` 完成查询与回测支撑

## 4. 概念结构设计

### 4.1 核心实体

本系统的核心实体包括：

1. 股票基础信息实体
2. 股票池历史实体
3. 全 A 股主数据实体
4. 因子面板实体
5. 财务数据实体
6. 公告/报告数据实体
7. 实验运行结果实体

### 4.2 实体关系

实体之间的关系如下：

1. 一只股票可以在多个股票池历史中出现，因此“股票”与“股票池历史”是多对多关系，通过 `stock_code + universe_id + 时间区间` 表示。
2. 一只股票在每个交易日最多对应一条主数据记录，因此“股票”与“全 A 主数据”是一对多关系。
3. 一只股票在每个交易日、每个股票池下最多对应一条因子面板记录，因此“股票”与“因子面板”是一对多关系。
4. 一只股票在不同报告期、公告日下对应多条财务或报告数据，因此“股票”与“财务/报告数据”是一对多关系。
5. 一次实验运行会生成多条候选股记录，因此“实验运行”与“候选池结果”是一对多关系。

## 5. 逻辑结构设计

### 5.1 Schema 设计

DuckDB 中至少定义以下逻辑 schema：

1. `universes`
2. `master`
3. `factors`
4. `financial`
5. `reports`
6. `full_master`

说明：

- 这 6 个 schema 已在 `plan.md` 中明确提出
- `runs` 相关结果目前仍以 `code/outputs/` 下 JSON/CSV 文件为主，后续如需统一查询，可再扩展为独立 schema

### 5.2 `universes` 模式

职责：

- 保存股票池历史成员关系
- 支持“某日属于哪个股票池”的查询

核心对象：

- `universes.all_a_tradable_history`
- `universes.hs300_history`
- `universes.sz50_history`
- `universes.zz500_history`
- `universes.vw_all_a_tradable_on_date`
- `universes.vw_hs300_on_date`
- `universes.vw_sz50_on_date`
- `universes.vw_zz500_on_date`

建议字段：

- `market_id`
- `universe_id`
- `stock_code`
- `start_date`
- `end_date`

建议主键/唯一键：

- `(universe_id, stock_code, start_date)`

### 5.3 `master` 模式

职责：

- 统一管理全 A 股共享市场主数据
- 支撑估值、状态与价格量查询

核心对象：

- `master.shared_kline_panel`
- `master.tdx_full_master_base_<year>`
- `master.full_master_<year>`
- `master.vw_shared_master_coverage`

建议标准字段：

- `trade_date`
- `stock_code`
- `open`
- `high`
- `low`
- `close`
- `preclose`
- `volume`
- `amount`
- `adjustflag`
- `pct_chg`
- `turn`
- `trade_status`
- `is_st`
- `pe_ttm`
- `pb_mrq`
- `ps_ttm`
- `pcf_ncf_ttm`

建议主键/唯一键：

- `(trade_date, stock_code)`

说明：

- 原始 `full_master` 文件当前采用 baostock 风格字段，如 `date`、`code`、`pctChg`、`tradestatus`、`isST`、`peTTM`
- 在 DuckDB 视图中统一映射为 snake_case，避免跨层字段不一致

### 5.4 `factors` 模式

职责：

- 保存正式股票池因子面板
- 为张量构建和回测筛选提供直接输入

核心对象：

- `factors.hs300_factor_panel`
- `factors.sz50_factor_panel`
- `factors.zz500_factor_panel`
- `factors.vw_factor_panel_coverage`

建议字段：

- `trade_date`
- `stock_code`
- `market_id`
- `universe_id`
- `industry`
- `future_return`
- `value_factor`
- `momentum_factor`
- `quality_factor`
- `volatility_factor`

建议主键/唯一键：

- `(trade_date, stock_code, universe_id)`

### 5.5 `financial` 模式

职责：

- 按表类型保存 baostock 财务数据
- 保持来源表语义，不强制并成一个超宽表

核心对象：

- `financial.profit_data`
- `financial.operation_data`
- `financial.growth_data`
- `financial.balance_data`
- `financial.cash_flow_data`
- `financial.dupont_data`
- `financial.vw_financial_dataset_coverage`

建议公共字段：

- `stock_code`
- `report_date`
- `pub_date`
- `stat_date`
- `source_year`
- `source_path`

说明：

- 原始列保留 baostock 命名
- 只在 DuckDB 视图层做公共字段归一化

### 5.6 `reports` 模式

职责：

- 保存业绩快报与业绩预告等公告类数据

核心对象：

- `reports.performance_express_report`
- `reports.forecast_report`

建议公共字段：

- `stock_code`
- `report_date`
- `pub_date`
- `source_year`
- `source_path`

### 5.7 `full_master` 模式

职责：

- 面向正式实验暴露统一的“共享主表”视图
- 屏蔽年度拆分文件与底层补字段过程

建议对象：

- `full_master.daily`
- `full_master.coverage_summary`

说明：

- 该 schema 可以由 `master.full_master_<year>` 聚合得到
- 研究代码与 Web 查询优先依赖统一视图，不直接依赖每年单独文件

## 6. 物理存储设计

### 6.1 目录与文件组织

正式数据目录采用以下物理组织：

```text
code/data/formal/
├─ universes/
├─ master/
├─ factors/
├─ financial/
├─ reports/
├─ parquet/
└─ baostock/
```

其中：

- `baostock/` 保存抓取阶段原始产物与清单
- `universes/` 保存股票池历史文件
- `master/` 保存共享行情、过渡版主表与正式 full master
- `factors/` 保存正式股票池因子面板
- `financial/` 与 `reports/` 保存按类型拆分的数据表
- `parquet/` 保存与 CSV 对应的列式镜像

### 6.2 分区策略

本项目不优先采用数据库内部分区，而优先采用“文件级分区”：

1. `financial/` 与 `reports/` 按 `dataset/year.csv` 组织
2. `master/` 中的 `full_master` 按年份组织
3. DuckDB 通过通配符或视图聚合分年文件

原因：

- 更符合抓取与增量补数流程
- 方便按年份重建
- 便于人工检查和局部修复

## 7. 关键约束设计

### 7.1 数据一致性约束

1. formal profile 的三元组必须一致：
   - `market.universe_id`
   - `market.universe_path`
   - `data.path`
2. 股票池过滤必须基于历史成员，而不是静态成分名单。
3. 全 A 主数据只能保存一份共享底座，不能按 `HS300/SZ50/ZZ500` 重复存储。
4. `CSV` 与 `Parquet` 的字段合同、时间范围、命名必须一致。

### 7.2 唯一性约束

1. `universes`：`(universe_id, stock_code, start_date)` 唯一
2. `master`：`(trade_date, stock_code)` 唯一
3. `factors`：`(trade_date, stock_code, universe_id)` 唯一
4. `selection_candidates`：单次运行内 `(trade_date, stock_code)` 唯一

### 7.3 命名约束

统一要求：

- schema 名、视图名、规范化字段名全部使用 `snake_case`
- 原始数据文件保留来源字段名
- 在 DuckDB 视图中完成字段重命名和标准化

## 8. Web 查询层设计

当前 Web 后端已经稳定依赖以下结果文件：

- `run_manifest.json`
- `metrics.json`
- `selection_candidates.json`
- `factor_summary_*.json`
- `factor_association_*.json`
- `time_regimes_*.json`

因此数据库设计中的 Web 边界应分为两部分：

1. 实验结果层：
   - 继续由 `code/outputs/<run_id>/` 下结构化 JSON/CSV 提供
2. 正式数据查询层：
   - 由 DuckDB 提供覆盖率、股票池成员、主数据摘要和财务数据摘要

这意味着：

- Web 后端不直接扫描大型原始 CSV
- Web 后端优先调用 DuckDB 视图或稳定 JSON 结果文件

## 9. 推荐 DuckDB 对象命名

推荐至少注册以下对象：

```sql
CREATE SCHEMA IF NOT EXISTS universes;
CREATE SCHEMA IF NOT EXISTS master;
CREATE SCHEMA IF NOT EXISTS factors;
CREATE SCHEMA IF NOT EXISTS financial;
CREATE SCHEMA IF NOT EXISTS reports;
CREATE SCHEMA IF NOT EXISTS full_master;
```

推荐视图名：

- `universes.vw_all_a_tradable_on_date`
- `universes.vw_hs300_on_date`
- `universes.vw_sz50_on_date`
- `universes.vw_zz500_on_date`
- `master.vw_shared_master_coverage`
- `factors.vw_factor_panel_coverage`
- `financial.vw_financial_dataset_coverage`
- `full_master.daily`

## 10. 本设计对应的仓库落点

本数据库设计与以下文件保持一致：

- `README.md`
- `plan.md`
- `code/data/formal/README.md`
- `code/data/formal/master/FULL_MASTER_CONTRACT.md`
- `web/backend/app.py`
- `code/configs/formal_hs300.yaml`
- `code/configs/formal_sz50.yaml`
- `code/configs/formal_zz500.yaml`

## 11. 结论

本毕设的数据库设计采用“文件型正式数据底座 + DuckDB 查询目录”的分析型架构。其核心思想是：

1. 用 `CSV` 保证正式数据可检查、可追溯
2. 用 `Parquet` 提升大规模读性能
3. 用 `DuckDB` 统一组织查询对象与 Web 读取边界
4. 用“全 A 主数据 + 股票池历史过滤”替代“按指数重复存市场数据”的低效模式

该设计既满足当前毕业设计的实验需求，也为后续扩展 `us_equity`、统一 Web 查询层和增加更多模型结果视图保留了空间。
