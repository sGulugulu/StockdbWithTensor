# 基于张量分解的股票因子降维与模式发现

本仓库用于支撑毕业设计《基于张量分解的股票因子降维与模式发现》的实验、数据与系统实现。当前代码主线位于 `code/` 目录下，目标不是构建通用量化平台，而是围绕以下研究主线收敛：

1. 以 `股票-因子-时间` 三维张量作为统一研究对象。
2. 以 `CP` / `Tucker` 作为核心方法路径。
3. 在正式样本范围内验证因子降维、模式发现与后续选股有效性。
4. 将实验系统、结果产物和 Web 查询能力统一到同一条论文叙事之下。

## 正式范围

当前正式 A 股研究样本固定为：

- `HS300`
- `SZ50`
- `ZZ500`

当前正式全量时间窗口固定为：

- `2015-01-01` 到 `2026-04-01`

长期股票覆盖范围保留更广的全 A 股，不将系统长期边界写死为上述三个指数样本。

## 实验协议

正式实验默认采用按时间切分，但系统层必须保留可配置切分能力，至少支持：

- 按时间切分
- 按股票切分
- 混合切分

在构造 `股票-因子-时间` 三维张量之前，预处理阶段必须独立存在，且至少包括：

- 样本筛选
- 时间对齐
- 缺失值处理
- 异常值处理
- 因子方向统一
- 截面标准化
- 标签与元信息拆分

其中有两条硬约束：

- 未来收益标签只用于评估，不得进入输入张量
- 不允许未来信息穿越训练 / 预测边界

## 评估框架

正式评估框架固定为三层：

1. 分解质量  
   关注重构误差、秩选择行为与结果稳定性。
2. 模式发现与解释  
   关注股票结构、因子贡献和时间模式的可解释性。
3. 预测或决策有效性  
   关注后续窗口中的排序效果、候选股票输出和泛化表现。

这三层评估同时服务于论文结果章节、系统结果页和 API 输出契约。

## 系统边界

当前项目的长期系统边界固定为：

- `Go` 负责 HTTP 接口、运行状态、结果查询与 formal 查询聚合
- `Python` 负责数据处理、实验执行与结果落盘
- `DuckDB` 负责 formal 数据查询与稳定 catalog 视图
- `code/outputs` 负责运行结果产物

这意味着：

- `web/backend/` 下的 Python 服务仅保留为兼容入口或过渡实现
- 长期正式网关仍然是 `web/backend-go/`
- 不将 Python 实验执行逻辑重新混入 Go 网关

## API 与运行契约

当前 Go 网关的**现状**是直接返回数组或对象，错误响应采用 `{detail: ...}` 结构；下面的统一响应包裹结构是**长期目标契约**，用于约束后续正式网关设计：

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "req_xxx",
  "timestamp": "2026-04-09T00:00:00Z"
}
```

`POST /api/runs` 默认采用异步提交流程：

1. 校验请求与实验配置；
2. 分配 `run_id`；
3. 写入运行态；
4. 当前实现返回 `200 OK` 和 `run_id`；长期目标是显式返回 `202 Accepted`；
5. 异步启动 Python runner；
6. 前端轮询状态或详情接口获取结果。

实验配置模型至少需要覆盖：

- `config_profile`
- 训练/预测样本配置
- 切分策略
- 模型设置
- 输出设置

状态真源采用双层结构：

- 运行态 JSON
- DuckDB 归档与查询视图

Python 不反向覆盖 Go 持有的状态真源。

## formal 数据主链

当前 formal 数据主链固定为：

1. `baostock` 原始层
2. `universes` 股票池历史层
3. `master` 主市场数据层
4. `financial` 财务分表层
5. `reports` 报告分表层
6. `factors` 因子面板层
7. `parquet` 列式镜像层
8. `DuckDB` catalog 查询层
9. `code/outputs` 实验输入与输出层

对应职责如下：

- `code/data/formal/baostock/`
  - canonical baostock root，保存共享 metadata、index memberships、shared kline 和 manifest
- `code/data/formal/universes/`
  - 保存 `HS300`、`SZ50`、`ZZ500` 和全 A 可交易股票池历史
- `code/data/formal/master/`
  - 保存共享主市场数据、shared kline 与 `full master`
- `code/data/formal/financial/`
  - 按表类型保存财务数据
- `code/data/formal/reports/`
  - 按表类型保存报告数据
- `code/data/formal/factors/`
  - 保存正式股票池因子面板
- `code/data/formal/parquet/`
  - 保存已验证 CSV 的 Parquet 镜像
- `code/data/formal/catalog.duckdb`
  - 提供稳定 DuckDB 查询目录
- `code/outputs/`
  - 保存实验运行产物

该主链的核心原则是：

- 使用共享全 A 主数据 + universe 历史过滤，不按指数重复存储完整市场主数据
- 使用 `CSV -> Parquet -> DuckDB` 形成稳定、可检查、可查询的正式路线

## 总体任务树

总体路线稳定拆分为四个一级分支：

1. **研究数据与实验底座**
2. **系统实现与演示**
3. **论文交付与答辩材料**
4. **后续扩展与长期演进**

其排序同时就是依赖顺序：

1. 先完成研究数据与实验底座；
2. 再完成系统实现与演示；
3. 再完成论文交付与答辩材料；
4. 最后再进入后续扩展与长期演进。

其中依赖关系需要显式明确：

- 系统线依赖实验底座；
- 论文线依赖实验结果与稳定合同；
- 长期扩展线依赖前三条主线基本稳定。

## 历史复盘框架

当前项目的历史问题至少分为四类：

1. 研究边界漂移  
   例如正式样本范围、主问题定义和时间窗口曾多次摇摆。
2. 数据底座不稳定  
   例如 shared kline、full master 与 formal 长期目标一度并行且边界不清。
3. 系统边界反复调整  
   例如 Python backend 与长期 Go gateway 目标曾并存且边界模糊。
4. 论文与工程脱节  
   例如工程结果先出现，而学术叙事和正式合同后补。

## 运行方式

先创建本地虚拟环境并安装依赖：

```powershell
python -m venv .venv
python -m pip install -r requirements.txt
```

当前运行时支持：

- `device=cpu`
- `device=cuda`
- `device=auto`

当 CUDA 可用时，数值后处理优先走 GPU；否则自动回退到 CPU。当前 GPU 主路径是 `PyTorch`，后续热点优化再考虑 `Triton` 或原生 `CUDA`。

### Stage 1：抓取 universe-history 与 metadata

```powershell
python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-01 `
  --indices hs300,sz50,zz500 `
  --skip-financials `
  --skip-reports
```

formal 日频面板默认采用 **前复权**（`adjustflag=2`）口径抓取 baostock kline 数据。

### Stage 2：抓取 formal 财务与报告数据

```powershell
python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-01 `
  --indices hs300,sz50,zz500 `
  --skip-index-memberships `
  --skip-metadata
```

### Stage 3：构建 formal 市场面板与因子面板

从 canonical formal root 构建或刷新日频市场面板、因子面板和实验输入。

### Stage 4：生成 Parquet

将验证通过的 formal `CSV` 输出转换为对应的 `Parquet` 文件，用于后续大规模训练和更快读写。

### Stage 5：注册 DuckDB catalog

```powershell
python code/data/register_formal_duckdb_catalog.py `
  --formal-root code/data/formal `
  --catalog-path code/data/formal/catalog.duckdb
```

## 配置文件

正式 A 股 profile：

- `code/configs/formal_hs300.yaml`
- `code/configs/formal_sz50.yaml`
- `code/configs/formal_zz500.yaml`

样例 profile：

- `code/configs/sample_cn_smoke.yaml`
- `code/configs/sample_us_equity.yaml`

正式 profile 应基于共享全 A 主数据与 universe-history 过滤，不再依赖按指数重复存储的完整市场数据。

## 运行实验

轻量联调用 smoke 配置：

```powershell
python code/main.py --config code/configs/sample_cn_smoke.yaml
```

正式实验优先使用 formal profile：

```powershell
python code/main.py --config code/configs/formal_hs300.yaml
```

## 测试

Python 测试：

```powershell
python -m unittest discover -s code/tests
```

Go 后端测试：

```powershell
cd web/backend-go
go test ./internal/backend
```

前端测试：

```powershell
cd web/frontend
npm test -- --run
```

## Web API

Go 网关长期负责以下接口：

- `GET /api/formal/coverage`
- `GET /api/formal/universes/{universe_id}?trade_date=YYYY-MM-DD`
- `GET /api/runs`
- `GET /api/runs/{run_id}`
- `GET /api/runs/{run_id}/metrics`
- `GET /api/runs/{run_id}/selection`
- `POST /api/runs`

启动 Go 后端：

```powershell
go run ./web/backend-go/cmd/server
```

前端默认指向：

```text
http://127.0.0.1:8080
```

如果需要对比遗留 Python 后端，可临时设置：

```powershell
$env:VITE_API_BASE="http://127.0.0.1:8000"
```

遗留 Python scaffold 仅作兼容参考：

```powershell
python -m uvicorn web.backend.app:create_app --factory --reload
```

## 输出产物

每次运行会在 `code/outputs/` 下生成独立实验目录，至少包含：

- `run_manifest.json`
- `config_snapshot.yaml`
- `metrics.csv` 与 `metrics.json`
- `selection_*.csv` 与 `selection_*.json`
- `factor_summary_*.csv` 与 `factor_summary_*.json`
- `stock_similarity_*.csv`
- `factor_association_*.csv`
- `time_regimes_*.csv`
- `summary.md` 与配套图表

## 目录结构

- `code/configs/`：实验配置
- `code/data/formal/`：formal 正式数据根目录
- `code/data/register_formal_duckdb_catalog.py`：DuckDB catalog 注册脚本
- `code/stock_tensor/`：预处理、张量构建、模型、评估与输出逻辑
- `code/tests/`：自动化测试
- `web/backend-go/`：长期正式 Go 网关
- `web/backend/`：遗留 Python 后端兼容层
- `web/frontend/`：React + Vite 前端
- `code/outputs/`：实验结果产物
