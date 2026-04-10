# Parquet

这个目录保存 structured CSV 的 parquet 镜像。

当前镜像范围包括：

- `parquet/universes/*.parquet`
- `parquet/factors/*.parquet`
- `parquet/master/*.parquet`

后续应扩展到：

- `parquet/financial/...`
- `parquet/reports/...`

## 转换命令

```powershell
python code/data/convert_formal_csv_to_parquet.py `
  --formal-root code/data/formal `
  --overwrite
```

## 输入目录

脚本会扫描：

- `code/data/formal/universes/`
- `code/data/formal/factors/`
- `code/data/formal/master/`
- `code/data/formal/financial/`
- `code/data/formal/reports/`

## 输出格式

对于每个 CSV，会生成一个同名 parquet：

- `universes/hs300_history.csv`
  -> `parquet/universes/hs300_history.parquet`
- `master/shared_kline_panel.csv`
  -> `parquet/master/shared_kline_panel.parquet`

## 当前依赖

需要：

- `pandas`
- `pyarrow` 或 `fastparquet`

## 注意

- 当前 parquet 已经能真实生成
- 但是否是“正式全量 parquet”，取决于上游 CSV 是否已经是正式全量数据
