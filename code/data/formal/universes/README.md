# Universes

这个目录保存“股票池历史文件”。这些文件会被 formal profile 直接读取。

## 文件

- `all_a_tradable_history.csv`
- `hs300_history.csv`
- `sz50_history.csv`
- `zz500_history.csv`

## 文件格式

统一字段：

- `market_id`
- `universe_id`
- `stock_code`
- `start_date`
- `end_date`

其中：

- `stock_code` 使用项目内部统一格式，例如：
  - `600000.SH`
  - `000001.SZ`
- `start_date` / `end_date` 使用 `YYYY-MM-DD`

## 生成全 A 可交易股票池历史

前提：先有 `code/data/formal/baostock/metadata/stock_basic.csv`

```powershell
python code/data/build_all_a_tradable_history.py `
  --stock-basic-path code/data/formal/baostock/metadata/stock_basic.csv `
  --output-path code/data/formal/universes/all_a_tradable_history.csv `
  --horizon-date 2026-04-01
```

## 生成指数成员历史

### HS300

```powershell
python code/data/build_baostock_member_history.py `
  --snapshot code/data/formal/baostock/index_memberships/hs300_snapshots.csv `
  --output code/data/formal/universes/hs300_history.csv `
  --horizon-date 2026-04-01
```

### SZ50

```powershell
python code/data/build_baostock_member_history.py `
  --snapshot code/data/formal/baostock/index_memberships/sz50_snapshots.csv `
  --output code/data/formal/universes/sz50_history.csv `
  --horizon-date 2026-04-01
```

### ZZ500

```powershell
python code/data/build_baostock_member_history.py `
  --snapshot code/data/formal/baostock/index_memberships/zz500_snapshots.csv `
  --output code/data/formal/universes/zz500_history.csv `
  --horizon-date 2026-04-01
```

## 参数说明

`build_baostock_member_history.py`

- `--snapshot`
  - 指数快照文件
- `--output`
  - 输出历史文件
- `--horizon-date`
  - 最后一个开放区间的结束日期

`build_all_a_tradable_history.py`

- `--stock-basic-path`
  - 全 A `stock_basic.csv`
- `--output-path`
  - 输出 `all_a_tradable_history.csv`
- `--horizon-date`
  - 没有 `outDate` 的股票，用这个日期补结束时间
