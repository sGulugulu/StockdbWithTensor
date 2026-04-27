# EXTENDED_FACTOR_CONTRACT

## 目的

本文档定义扩展版 formal factor panel 中新增字段的来源、披露时点和最早可用交易日规则，用于支撑“训练输入扩展与 PIT 安全”链路的实际落地。

## 新增字段

### 一、市场级宏观/风格代理变量

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `market_return_1d` | `index_daily/*.csv` | `close` | `trade_date` | 交易日收盘后形成，下一交易日训练样本直接使用同日已知指数收盘序列 | 无记录时填 `0.0` |
| `market_momentum_5d` | `index_daily/*.csv` | `close` | `trade_date` | 同上，按指数 5 日滚动收益构造 | 无记录时填 `0.0` |
| `market_momentum_20d` | `index_daily/*.csv` | `close` | `trade_date` | 同上，按指数 20 日滚动收益构造，用作月度市场状态代理 | 无记录时填 `0.0` |
| `market_volatility_20d` | `index_daily/*.csv` | `close` | `trade_date` | 同上，按指数近 20 日收益波动率构造 | 无记录时填 `0.0` |
| `market_drawdown_20d` | `index_daily/*.csv` | `close` | `trade_date` | 同上，按近 20 日高点回撤构造，用于刻画市场压力状态 | 无记录时填 `0.0` |
| `market_amount_change_5d` | `index_daily/*.csv` | `amount` | `trade_date` | 同上，按指数成交额 5 日变化率构造 | 无记录时填 `0.0` |
| `market_amount_zscore_20d` | `index_daily/*.csv` | `amount` | `trade_date` | 同上，按指数成交额近 20 日滚动 z-score 构造，用于刻画流动性冲击 | 无记录时填 `0.0` |
| `macro_proxy_risk_score` | `index_daily/*.csv` | `close` | `trade_date` | 在外部宏观源表尚未具备 PIT 可用时点前，使用指数 20 日波动率与回撤合成市场风险代理 | 无记录时填 `0.0` |
| `macro_proxy_liquidity_score` | `index_daily/*.csv` | `amount` | `trade_date` | 使用指数成交额变化率与成交额 z-score 合成流动性代理，作为宏观流动性层的可复核占位 | 无记录时填 `0.0` |
| `macro_policy_rate` | `external/macro_interest_rate.csv` | `value` | `pub_date` | 以 `available_date <= trade_date` 的最新政策利率记录为准 | 无可用记录时填 `0.0` |
| `macro_lpr_1y` | `external/macro_interest_rate.csv` | `value` | `pub_date` | 同上，取 `metric_id=lpr_1y` 的最新记录 | 无可用记录时填 `0.0` |
| `macro_lpr_5y` | `external/macro_interest_rate.csv` | `value` | `pub_date` | 同上，取 `metric_id=lpr_5y` 的最新记录 | 无可用记录时填 `0.0` |
| `macro_cpi_mom` | `external/macro_monthly_indicator.csv` | `value` | `pub_date` | 同上，取 `metric_id=cpi_mom` 的最新记录 | 无可用记录时填 `0.0` |
| `macro_m2_yoy` | `external/macro_monthly_indicator.csv` | `value` | `pub_date` | 同上，取 `metric_id=m2_yoy` 的最新记录 | 无可用记录时填 `0.0` |
| `macro_industrial_production_yoy` | `external/macro_monthly_indicator.csv` | `value` | `pub_date` | 同上，取 `metric_id=industrial_production_yoy` 的最新记录 | 无可用记录时填 `0.0` |
| `macro_exports_yoy` | `external/macro_monthly_indicator.csv` | `value` | `pub_date` | 同上，取 `metric_id=exports_yoy` 的最新记录 | 无可用记录时填 `0.0` |
| `macro_imports_yoy` | `external/macro_monthly_indicator.csv` | `value` | `pub_date` | 同上，取 `metric_id=imports_yoy` 的最新记录 | 无可用记录时填 `0.0` |

### 二、财务 PIT 特征

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `pit_roe_avg` | `financial/profit_data.csv` | `roeAvg` | `pubDate` | 公告日之后的首个交易日开始可用；每个交易日选取 `available_date <= trade_date` 的最新记录 | 无可用记录时填 `0.0` |
| `pit_np_margin` | `financial/profit_data.csv` | `npMargin` | `pubDate` | 同上 | 无可用记录时填 `0.0` |
| `pit_gp_margin` | `financial/profit_data.csv` | `gpMargin` | `pubDate` | 同上 | 无可用记录时填 `0.0` |
| `pit_eps_ttm` | `financial/profit_data.csv` | `epsTTM` | `pubDate` | 同上 | 无可用记录时填 `0.0` |
| `pit_data_age_days` | `financial/profit_data.csv` | 公告日至交易日间隔 | `pubDate` | 仅在记录达到最早可用交易日后计算，用于衡量财务 PIT 信息新鲜度 | 无可用记录时填 `0` |

### 三、分红与公司行为特征

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `dividend_cash_ratio` | `events/dividend_event.csv` | `cash_ratio` | `pub_date` | 以实施方案公告日后的首个交易日为准，选取 `available_date <= trade_date` 的最新分红记录 | 无可用记录时填 `0.0` |
| `dividend_bonus_ratio` | `events/dividend_event.csv` | `bonus_ratio` | `pub_date` | 同上 | 无可用记录时填 `0.0` |
| `dividend_transfer_ratio` | `events/dividend_event.csv` | `transfer_ratio` | `pub_date` | 同上 | 无可用记录时填 `0.0` |
| `dividend_age_days` | `events/dividend_event.csv` | 公告日至交易日间隔 | `pub_date` | 仅在记录达到最早可用交易日后计算 | 无可用记录时填 `0` |
| `dividend_flag` | `events/dividend_event.csv` | 是否存在有效分红记录 | `pub_date` | 若存在 `available_date <= trade_date` 的分红记录则置 `1` | 默认 `0` |

### 四、业绩快报/预告事件特征

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `perf_express_eps_chg_pct` | `reports/performance_express_report/*.csv` | `performanceExpressEPSChgPct` | `performanceExpPubDate` | 公告日之后的首个交易日开始可用；每个交易日选取 `available_date <= trade_date` 的最新记录 | 无可用记录时填 `0.0` |
| `perf_express_roe_wa` | `reports/performance_express_report/*.csv` | `performanceExpressROEWa` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_gryoy` | `reports/performance_express_report/*.csv` | `performanceExpressGRYOY` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_opyoy` | `reports/performance_express_report/*.csv` | `performanceExpressOPYOY` | `performanceExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `perf_express_age_days` | `reports/performance_express_report/*.csv` | 公告日至交易日间隔 | `performanceExpPubDate` | 仅在记录达到最早可用交易日后计算，表示事件新鲜度 | 无可用记录时填 `0` |
| `perf_express_flag` | `reports/performance_express_report/*.csv` | 是否存在有效记录 | `performanceExpPubDate` | 若存在 `available_date <= trade_date` 的记录则置 `1`，否则置 `0` | 默认 `0` |
| `forecast_direction` | `reports/forecast_report/*.csv` | `profitForcastType` | `profitForcastExpPubDate` | 公告日之后的首个交易日开始可用；将预增/略增/续盈/扭亏映射为 `1`，预减/略减/首亏/续亏映射为 `-1` | 无可用记录时填 `0.0` |
| `forecast_chg_pct_up` | `reports/forecast_report/*.csv` | `profitForcastChgPctUp` | `profitForcastExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `forecast_chg_pct_dwn` | `reports/forecast_report/*.csv` | `profitForcastChgPctDwn` | `profitForcastExpPubDate` | 同上 | 无可用记录时填 `0.0` |
| `forecast_change_midpoint` | `reports/forecast_report/*.csv` | `profitForcastChgPctUp`、`profitForcastChgPctDwn` | `profitForcastExpPubDate` | 同上，取预告上下界均值刻画事件中枢 | 无可用记录时填 `0.0` |
| `forecast_change_width` | `reports/forecast_report/*.csv` | `profitForcastChgPctUp`、`profitForcastChgPctDwn` | `profitForcastExpPubDate` | 同上，取预告区间宽度刻画不确定性 | 无可用记录时填 `0.0` |
| `forecast_age_days` | `reports/forecast_report/*.csv` | 公告日至交易日间隔 | `profitForcastExpPubDate` | 仅在记录达到最早可用交易日后计算，表示事件新鲜度 | 无可用记录时填 `0` |
| `event_positive_flag` | `reports/performance_express_report/*.csv`、`reports/forecast_report/*.csv` | 快报 EPS 变化率、预告方向 | 对应公告日 | 任一可用事件显示正向变化时置 `1`，用于统一事件字典的方向层 | 默认 `0` |
| `event_negative_flag` | `reports/performance_express_report/*.csv`、`reports/forecast_report/*.csv` | 快报 EPS 变化率、预告方向 | 对应公告日 | 任一可用事件显示负向变化时置 `1`，用于统一事件字典的方向层 | 默认 `0` |
| `event_uncertainty_score` | `reports/forecast_report/*.csv` | `profitForcastChgPctUp`、`profitForcastChgPctDwn` | `profitForcastExpPubDate` | 预告上下界宽度，仅在事件可用后生效，用于刻画公告不确定性 | 无可用记录时填 `0.0` |
| `event_age_decay_score` | `reports/performance_express_report/*.csv`、`reports/forecast_report/*.csv` | 公告日至交易日间隔 | 对应公告日 | 对可用事件按 `1 / (1 + age_days)` 衰减求和，避免陈旧事件与新公告等权 | 无可用记录时填 `0.0` |
| `event_intensity_score` | `reports/performance_express_report/*.csv`、`reports/forecast_report/*.csv` | 业绩快报 EPS 变化率、业绩预告区间中枢 | 对应公告日 | 同上，取可用事件强度绝对值合计，避免方向抵消 | 无可用记录时填 `0.0` |
| `forecast_flag` | `reports/forecast_report/*.csv` | 是否存在有效记录 | `profitForcastExpPubDate` | 若存在 `available_date <= trade_date` 的记录则置 `1`，否则置 `0` | 默认 `0` |

### 五、重大事项与公告文本特征

| 字段名 | 来源表 | 原始字段 | 披露字段 | 最早可用规则 | 缺失处理 |
|--------|--------|----------|----------|--------------|----------|
| `major_event_count_30d` | `events/major_event_notice.csv` | 近 30 日重大事项条数 | `pub_date` | 仅统计 `available_date <= trade_date` 且距交易日不超过 30 天的重大事项公告 | 无可用记录时填 `0` |
| `major_event_severity_score_30d` | `events/major_event_notice.csv` | `severity_score` | `pub_date` | 同上，按近 30 日重大事项严重度求和 | 无可用记录时填 `0.0` |
| `major_event_age_days` | `events/major_event_notice.csv` | 公告日至交易日间隔 | `pub_date` | 对最新一条有效重大事项记录计算年龄 | 无可用记录时填 `0` |
| `major_event_flag` | `events/major_event_notice.csv` | 是否存在近 30 日重大事项 | `pub_date` | 若近 30 日存在有效重大事项则置 `1` | 默认 `0` |
| `announcement_count_30d` | `events/announcement_text.csv` | 近 30 日公告条数 | `pub_date` | 仅统计 `available_date <= trade_date` 且距交易日不超过 30 天的公告标题记录 | 无可用记录时填 `0` |
| `announcement_keyword_score_30d` | `events/announcement_text.csv` | `keyword_score` | `pub_date` | 同上，按标题关键词得分求和 | 无可用记录时填 `0.0` |
| `announcement_title_length_mean_30d` | `events/announcement_text.csv` | `title_length` | `pub_date` | 同上，取近 30 日公告标题长度均值 | 无可用记录时填 `0.0` |
| `announcement_flag` | `events/announcement_text.csv` | 是否存在近 30 日公告 | `pub_date` | 若近 30 日存在有效公告记录则置 `1` | 默认 `0` |

## 约束

1. 所有 PIT / 事件特征都必须先把公告日映射到“公告日之后的首个交易日”，不允许公告当日直接生效。
2. 不允许按 `statDate` 直接前填，否则会引入未来信息泄露。
3. 市场级代理变量只进入 extended panel，不回写 baseline panel。
4. 扩展版 panel 作为 baseline panel 的超集存在，便于后续做 baseline/extended 对照实验。
5. 当前外部宏观与公告文本输入基于 `code/data/build_formal_extended_sources.py` 生成的 committed snapshot 表；对 `2026-03-02` 至 `2026-03-30` 提交版实验窗口已具备可审计 `available_date`，如后续要扩展到更长窗口，应同步扩展这些源表的抓取范围。
