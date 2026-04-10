# Canonical Baostock Root

这个目录保存 baostock 的 canonical 原始层数据。这里的文件主要服务于：

- Stage 1：指数成分、变更、元数据
- Stage 2：财务 / 报告原始表
- 最终 `manifest.json`

## 主要文件

- `index_memberships/<index>_snapshots.csv`
- `index_memberships/<index>_changes.csv`
- `metadata/stock_basic.csv`
- `metadata/stock_industry.csv`
- `metadata/selected_codes.csv`
- `metadata/all_a_codes.csv`
- `financial/<dataset>/<year>.csv`
- `reports/<dataset>/<year>.csv`
- `manifest.json`

## 直接抓全 A 元数据

```powershell
python code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-01 `
  --indices hs300,sz50,zz500 `
  --metadata-scope all_a `
  --all-a-history-output code/data/formal/universes/all_a_tradable_history.csv `
  --skip-financials `
  --skip-reports
```

## 只跑某个 dataset + 某个年份

示例：只跑 `profit_data` 的 `2015` 年

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh profit_data 2015
```

示例：只跑 `forecast_report` 的 `2015` 年

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh forecast_report 2015
```

## 检查某一年 8 个 dataset 是否已经完整导入

如果你只给年份参数，脚本不会执行抓取，而是检查：

- 这一年的 8 个 dataset 是否都已完成
- 已完成 `code|year` 数量 / 总 code 数量
- 对应 `dataset/year.csv` 是否存在
- 当前文件行数

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh 2015
```

## 常用参数说明

`fetch_baostock_data.py`

- `--output-root`
  - canonical 输出根目录
- `--start-date`
  - 报告类查询的起始日期
- `--end-date`
  - 报告类查询结束日期，同时也是 metadata / all-A-history 的 horizon
- `--indices`
  - 当前仍用于指数成员抓取和 selected union 生成
- `--metadata-scope selected|all_a`
  - `selected`：只抓三指数并集元数据
  - `all_a`：抓全 A 元数据，并允许生成 `all_a_codes.csv`
- `--stage2-scope selected|all_a`
  - `selected`：财务 / 报告只对 selected union 抓
  - `all_a`：财务 / 报告对全 A 代码表抓
- `--financial-datasets`
  - 逗号分隔的数据集名，只跑指定财务表
- `--report-datasets`
  - 逗号分隔的数据集名，只跑指定报告表
- `--all-a-history-output`
  - 只有在 `--metadata-scope all_a` 下才允许设置
- `--no-resume`
  - 禁用进度恢复

`run_baostock_stage2_dataset_year.sh`

- `bash code/data/run_baostock_stage2_dataset_year.sh <dataset> <year>`
  - 执行某张表某一年的抓取
- `bash code/data/run_baostock_stage2_dataset_year.sh <year>`
  - 检查这一年的 8 个 dataset 是否完整导入

## 当前 dataset 名

财务表：

- `profit_data`
- `operation_data`
- `growth_data`
- `balance_data`
- `cash_flow_data`
- `dupont_data`

报告表：

- `performance_express_report`
- `forecast_report`

## 文件格式

### `metadata/stock_basic.csv`

来自 baostock 的股票基础表，常见字段：

- `code`
- `code_name`
- `ipoDate`
- `outDate`
- `type`
- `status`

代码格式是 baostock 原生格式，例如：

- `sh.600000`
- `sz.000001`

### `metadata/all_a_codes.csv`

字段：

- `code`

内容是用于 live baostock 查询的全 A 原生代码列表。

当前 `master/shared_kline_panel.csv` 或未来的 `master/baostock_fields/<year>.csv` 都可以作为 full master 的 baostock supplement source。

### `financial/<dataset>/<year>.csv`

每行都保留：

- 原始 baostock 字段
- `dataset`
- `query_year`
- `query_quarter`

### `reports/<dataset>/<year>.csv`

每行都保留：

- 原始 baostock 字段
- `dataset`
- `query_year`

## 注意

- 如果你要严格控制请求风险，优先使用 `run_baostock_stage2_dataset_year.sh`，一次只跑一张表的一年。
- 不要同时高并发开很多 dataset。建议一次只跑 1 个，最多 2 个。
- 长任务现在具备两层恢复能力：
  - 如果 baostock 返回 `10001001 用户未登录`，脚本会自动重新 `login` 并重试当前请求
  - 如果某个 `dataset/year.csv` 已经非空，再次运行同一条命令时，脚本会先读取已有文件内容，推断已完成的 `code|year` 单元，再从剩余部分继续写，而不是从头整轮重写
- 如果只给年份参数，脚本进入检查模式，不执行抓取
