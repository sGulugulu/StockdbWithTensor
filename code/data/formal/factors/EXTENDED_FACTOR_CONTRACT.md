# EXTENDED_FACTOR_CONTRACT

## 目的

本文档定义扩展版 formal factor panel 中新增字段的来源、披露时点和最早可用交易日规则，用于支撑“训练输入扩展与 PIT 安全”链路的实际落地。

## 新增字段

### 一、市场级宏观/风格代理变量

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `market_return_1d` | `index_daily/*.csv` | `close` | `trade_date` | 交易日收盘后形成，下一交易日训练样本直接使用同日已知指数收盘序列 | 无记录时填 `0.0` |
| `market_momentum_5d` | `index_daily/*.csv` | `close` | `trade_date` | 同上，按指数 5 日滚动收益构造 | 无记录时填 `0.0` |
| `market_volatility_20d` | `index_daily/*.csv` | `close` | `trade_date` | 同上，按指数近 20 日收益波动率构造 | 无记录时填 `0.0` |
| `market_amount_change_5d` | `index_daily/*.csv` | `amount` | `trade_date` | 同上，按指数成交额 5 日变化率构造 | 无记录时填 `0.0` |

### 二、财务 PIT 特征

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `pit_roe_avg` | `financial/profit_data.csv` | `roeAvg` | `pubDate` | 公告日之后的首个交易日开始可用；每个交易日选取 `available_date <= trade_date` 的最新记录 | 无可用记录时填 `0.0` |
| `pit_np_margin` | `financial/profit_data.csv` | `npMargin` | `pubDate` | 同上 | 无可用记录时填 `0.0` |
| `pit_gp_margin` | `financial/profit_data.csv` | `gpMargin` | `pubDate` | 同上 | 无可用记录时填 `0.0` |
| `pit_eps_ttm` | `financial/profit_data.csv` | `epsTTM` | `pubDate` | 同上 | 无可用记录时填 `0.0` |

### 三、事件型特征

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `perf_express_eps_chg_pct` | `reports/performance_express_report/*.csv` | `performanceExpressEPSChgPct` | `performanceExpPubDate` | 公告日之后的首个交易日开始可用；每个交易日选取 `available_date <= trade_date` 的最新记录 | 无可用记录时填 `0.0` |
| `perf_express_roe_wa` | `reports/performance_express_report/*.csv` | `performanceExpressROEWa` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_gryoy` | `reports/performance_express_report/*.csv` | `performanceExpressGRYOY` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_opyoy` | `reports/performance_express_report/*.csv` | `performanceExpressOPYOY` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_flag` | `reports/performance_express_report/*.csv` | 是否存在有效记录 | `performanceExpPubDate` | 若存在 `available_date <= trade_date` 的记录则置 `1`，否则置 `0` | 默认 `0` |
| `forecast_direction` | `reports/forecast_report/*.csv` | `profitForcastType` | `profitForcastExpPubDate` | 公告日之后的首个交易日开始可用；将预增/略增/续盈/扭亏映射为 `1`，预减/略减/首亏/续亏映射为 `-1` | 无可用记录时填 `0.0` |
| `forecast_chg_pct_up` | `reports/forecast_report/*.csv` | `profitForcastChgPctUp` | `profitForcastExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `forecast_chg_pct_dwn` | `reports/forecast_report/*.csv` | `profitForcastChgPctDwn` | `profitForcastExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `forecast_flag` | `reports/forecast_report/*.csv` | 是否存在有效记录 | `profitForcastExpPubDate` | 若存在 `available_date <= trade_date` 的记录则置 `1`，否则置 `0` | 默认 `0` |

## 约束

1. 所有 PIT / 事件特征都必须先把公告日映射到“公告日之后的首个交易日”，不允许公告当日直接生效。
2. 不允许按 `statDate` 直接前填，否则会引入未来信息泄露。
3. 市场级代理变量只进入 extended panel，不回写 baseline panel。
4. 扩展版 panel 作为 baseline panel 的超集存在，便于后续做 baseline/extended 对照实验。
