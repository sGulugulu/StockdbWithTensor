# Full Master Contract

## Goal

构建一个适合正式选股与后续张量建模的 `full master` 主表。

它的作用是：

- 作为全 A 共享市场主数据
- 为 `HS300` / `SZ50` / `ZZ500` 因子面板提供统一底座
- 保持与后续美股扩展相同的数据组织思路

## Standard Fields

最终 `full master` 建议至少包含以下字段：

### Price / Volume Core

- `date`
- `code`
- `open`
- `high`
- `low`
- `close`
- `preclose`
- `volume`
- `amount`
- `adjustflag`
- `pctChg`

### Market / Status Supplement

- `turn`
- `tradestatus`
- `isST`

### Valuation Supplement

- `peTTM`
- `pbMRQ`
- `psTTM`
- `pcfNcfTTM`

### Provenance

- `source_price_vendor`
- `source_file`

## Source Ownership

### Provided by Tongdaxin

这些字段可以直接由通达信日线主数据提供：

- `date` from `trade_date`
- `code` from `stock_code` after format conversion
- `open`
- `high`
- `low`
- `close`
- `volume`
- `amount`
- `source_file`

### Derived from Tongdaxin

这些字段可以通过通达信价格量数据派生：

- `preclose`
  - 上一交易日 `close`
- `pctChg`
  - `(close / preclose - 1) * 100`
- `adjustflag`
  - 当前正式约定直接写 `2`，表示前复权来源
- `source_price_vendor`
  - 固定写 `tongdaxin`

### Must Be Supplemented by Baostock

这些字段当前不能从现有通达信导出直接获得，必须由 baostock 补齐：

- `turn`
- `tradestatus`
- `isST`
- `peTTM`
- `pbMRQ`
- `psTTM`
- `pcfNcfTTM`

## Current Project Constraint

当前 `build_formal_factor_panel.py` 实际依赖至少这些字段：

- `close`
- `turn`
- `peTTM`
- `pbMRQ`
- `psTTM`

因此：

- 通达信可以直接承担价格量主干
- 但不能单独承担完整 `full master`
- 要想正式用于选股，必须再合并 baostock 的估值 / 状态字段

## Pipeline

### Step 1

通达信原始日线 -> TDX Base Master

```powershell
.venv/bin/python code/data/build_tdx_full_master_base.py `
  --input-path code/data/formal/tdx_daily_raw.csv `
  --output-path code/data/formal/master/tdx_full_master_base.csv `
  --adjustflag-value 2
```

### Step 2

用 baostock shared master 补齐估值 / 状态字段

```powershell
.venv/bin/python code/data/merge_baostock_master_fields.py `
  --tdx-base-path code/data/formal/master/tdx_full_master_base.csv `
  --baostock-path code/data/formal/master/shared_kline_panel.csv `
  --output-path code/data/formal/master/full_master.csv
```

## Code Format

`full master` 使用 baostock 风格代码：

- `sh.600000`
- `sz.000001`

这样与当前 baostock shared master 和 live query 补字段逻辑更一致。
