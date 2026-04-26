# EXTENDED_FACTOR_CONTRACT

## 目的

本文档定义扩展版 formal factor panel 中新增字段的来源、披露时点和最早可用交易日规则，用于支撑“训练输入扩展与 PIT 安全”链路的实际落地。

## 新增字段

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `pit_roe_avg` | `financial/profit_data.csv` | `roeAvg` | `pubDate` | 对每个交易日选取 `pubDate <= trade_date` 的最新一条记录 | 无可用记录时填 `0.0` |
| `pit_np_margin` | `financial/profit_data.csv` | `npMargin` | `pubDate` | 同上 | 无可用记录时填 `0.0` |
| `pit_gp_margin` | `financial/profit_data.csv` | `gpMargin` | `pubDate` | 同上 | 无可用记录时填 `0.0` |
| `pit_eps_ttm` | `financial/profit_data.csv` | `epsTTM` | `pubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_eps_chg_pct` | `reports/performance_express_report/*.csv` | `performanceExpressEPSChgPct` | `performanceExpPubDate` | 对每个交易日选取 `performanceExpPubDate <= trade_date` 的最新一条记录 | 无可用记录时填 `0.0` |
| `perf_express_roe_wa` | `reports/performance_express_report/*.csv` | `performanceExpressROEWa` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_gryoy` | `reports/performance_express_report/*.csv` | `performanceExpressGRYOY` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_opyoy` | `reports/performance_express_report/*.csv` | `performanceExpressOPYOY` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_flag` | `reports/performance_express_report/*.csv` | 是否存在有效记录 | `performanceExpPubDate` | 若存在 `performanceExpPubDate <= trade_date` 的记录则置 `1`，否则置 `0` | 默认 `0` |

## 约束

1. 所有 PIT 特征只允许使用 `pubDate` 或 `performanceExpPubDate` 不晚于交易日的记录。
2. 不允许按 `statDate` 直接前填，否则会引入未来信息泄露。
3. 当前扩展版 panel 先聚焦财务盈利能力与业绩快报事件，不在本轮引入宏观变量。
4. 扩展版 panel 作为 baseline panel 的超集存在，便于后续做 baseline/extended 对照实验。
