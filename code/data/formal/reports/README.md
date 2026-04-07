# Reports

这个目录保存正式报告表。推荐结构是：

- `reports/performance_express_report/2015.csv`
- `reports/forecast_report/2015.csv`

## 当前 dataset

- `performance_express_report`
- `forecast_report`

## 推荐执行方式

一次只跑：

- 一张表
- 一年

### 示例：跑 `performance_express_report 2015`

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh performance_express_report 2015
```

### 示例：跑 `forecast_report 2016`

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh forecast_report 2016
```

### 示例：检查 `2015` 年所有 dataset 完成情况

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh 2015
```

## 输出格式

每行建议保留：

- 原始 baostock 报告字段
- `dataset`
- `query_year`

## 注意

- 报告类现在也正式按“表 + 年份”分拆写入
- 不建议直接把 `2015-2026` 一次性打给同一张表
- 如果只传一个年份参数，脚本进入检查模式，不执行抓取
- 现在支持中断恢复：
  - 如果 baostock 登录态失效，脚本会自动重新登录并重试当前请求
  - 如果 `reports/<dataset>/<year>.csv` 已经存在且非空，再次运行同一条命令时，会先读取已有文件，推断已完成的 `code|year`，从剩余部分继续写
