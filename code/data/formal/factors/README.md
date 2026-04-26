# Factors

这个目录保存三个正式股票池的因子面板：

- `hs300_factor_panel.csv`
- `sz50_factor_panel.csv`
- `zz500_factor_panel.csv`
- `hs300_factor_panel_extended.csv`
- `sz50_factor_panel_extended.csv`
- `zz500_factor_panel_extended.csv`

## 文件格式

当前因子面板字段包括：

- `stock_code`
- `trade_date`
- `industry`
- `value_factor`
- `momentum_factor`
- `quality_factor`
- `volatility_factor`
- `turn_factor`
- `ps_ttm`
- `future_return`

扩展版因子面板在此基础上新增：

- `pit_roe_avg`
- `pit_np_margin`
- `pit_gp_margin`
- `pit_eps_ttm`
- `perf_express_eps_chg_pct`
- `perf_express_roe_wa`
- `perf_express_gryoy`
- `perf_express_opyoy`
- `perf_express_flag`

其中：

- `stock_code` 使用项目统一格式，如 `600000.SH`
- `trade_date` 使用 `YYYY-MM-DD`

## 生成命令

### HS300

```powershell
python code/data/build_formal_factor_panel.py `
  --kline-path code/data/formal/master/shared_kline_panel.csv `
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv `
  --membership-path code/data/formal/universes/hs300_history.csv `
  --output-path code/data/formal/factors/hs300_factor_panel.csv
```

### SZ50

```powershell
python code/data/build_formal_factor_panel.py `
  --kline-path code/data/formal/master/shared_kline_panel.csv `
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv `
  --membership-path code/data/formal/universes/sz50_history.csv `
  --output-path code/data/formal/factors/sz50_factor_panel.csv
```

### ZZ500

```powershell
python code/data/build_formal_factor_panel.py `
  --kline-path code/data/formal/master/shared_kline_panel.csv `
  --industry-path code/data/formal/baostock/metadata/stock_industry.csv `
  --membership-path code/data/formal/universes/zz500_history.csv `
  --output-path code/data/formal/factors/zz500_factor_panel.csv
```

## 扩展版生成命令

### HS300 Extended

```powershell
python code/data/build_extended_factor_panel.py `
  --base-panel-path code/data/formal/factors/hs300_factor_panel.csv `
  --profit-data-path code/data/formal/baostock/financial/profit_data.csv `
  --performance-express-path code/data/formal/baostock/reports/performance_express_report `
  --output-path code/data/formal/factors/hs300_factor_panel_extended.csv
```

### SZ50 Extended

```powershell
python code/data/build_extended_factor_panel.py `
  --base-panel-path code/data/formal/factors/sz50_factor_panel.csv `
  --profit-data-path code/data/formal/baostock/financial/profit_data.csv `
  --performance-express-path code/data/formal/baostock/reports/performance_express_report `
  --output-path code/data/formal/factors/sz50_factor_panel_extended.csv
```

### ZZ500 Extended

```powershell
python code/data/build_extended_factor_panel.py `
  --base-panel-path code/data/formal/factors/zz500_factor_panel.csv `
  --profit-data-path code/data/formal/baostock/financial/profit_data.csv `
  --performance-express-path code/data/formal/baostock/reports/performance_express_report `
  --output-path code/data/formal/factors/zz500_factor_panel_extended.csv
```

## 注意

- 这里的 factor panel 是否覆盖 2015，取决于：
  - `shared_kline_panel.csv` 是否覆盖 2015
  - 对应 `universe history` 是否覆盖 2015
- 如果未来 `full_master.csv` 已经具备完整价格量 + 估值 / 状态字段，则应优先从 `full master` 而不是短窗口 `shared_kline_panel.csv` 重建 factor panel
- 当前如果 `HS300/SZ50/ZZ500` 成员历史还只有 2026 窗口，那么 2015 的 factor panel 还无法正确重建
- 扩展版 panel 当前只接入“财务 PIT + 业绩快报”第一版特征，尚未纳入宏观变量与更广泛事件特征
