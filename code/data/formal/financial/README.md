# Financial

这个目录保存正式财务表。当前正式落盘目标是：

- `financial/profit_data/2015.csv`
- `financial/profit_data/2016.csv`
- `financial/operation_data/2015.csv`
- ...

## 当前 dataset

- `profit_data`
- `operation_data`
- `growth_data`
- `balance_data`
- `cash_flow_data`
- `dupont_data`

## 推荐执行方式

一次只跑：

- 一张表
- 一年

### 示例：跑 `profit_data 2015`

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh profit_data 2015
```

### 示例：跑 `cash_flow_data 2016`

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh cash_flow_data 2016
```

### 示例：检查 `2015` 年所有 dataset 完成情况

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh 2015
```

## 输出格式

每张表的每年文件建议保留：

- 原始 baostock 财务字段
- `dataset`
- `query_year`
- `query_quarter`

## 注意

- 当前正式落盘目标就是“按表 + 年份拆分写入”
- 你手动执行时，优先按 `dataset + year` 粒度运行
- 不建议同时高并发开很多表
- 如果只传一个年份参数，脚本进入检查模式，不执行抓取
- 现在支持中断恢复：
  - 如果 baostock 登录态失效，脚本会自动重新登录并重试当前请求
  - 如果 `financial/<dataset>/<year>.csv` 已经存在且非空，再次运行同一条命令时，会先读取已有文件内容，推断已完成的 `code|year`，继续写剩余部分
- 建议不要手动编辑正在写入的 `dataset/year.csv`，否则恢复判断会失真
