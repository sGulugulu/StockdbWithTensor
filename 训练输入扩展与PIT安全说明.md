# 训练输入扩展与 PIT 安全说明

## 目的

本文档用于说明当前论文正式实验训练输入的边界、尚未并入训练的扩展特征类别，以及后续扩展时必须遵守的 point-in-time（PIT）安全原则。该文档与《论文不足与完善计划》中的“不足一”对应，主要服务于论文正文补写、实验扩展和数据链路收口。

## 当前正式训练输入边界

当前进入训练张量的核心输入仍以正式因子面板为主，主要特征包括：

1. 由共享 K 线数据衍生的价格、收益率、波动率相关因子。
2. 基于正式样本池构造的核心风格因子，如价值、质量、动量、波动率等。
3. 由指数成分历史限定后的股票池横截面特征。

这些特征的共同特点是：

1. 数据底座已经形成相对稳定的 formal 落盘路径，但“数据底座窗口”和“当前已提交正式实验窗口”仍需严格区分。
2. 当前仓库提交、直接供 formal profile 与论文复现实验使用的 factor panel 快照和 formal 输出已统一到 `2026-03-02` 至 `2026-03-30`。
3. canonical formal 原始数据链仍可继续覆盖到更长窗口，但必须与“提交版实验快照”显式区分，避免不同时间口径混用。

## 当前已接入与尚未接入的扩展特征

当前已经进入 extended 训练张量的扩展特征包括：

1. 市场级代理变量：指数日收益、5 日/20 日动量、20 日波动率、20 日回撤、成交额变化率和成交额 20 日 z-score。
2. 财务 PIT 特征：基于 `profit_data` 的盈利能力与 EPS 指标。
3. 外部宏观特征：以 `external/macro_interest_rate.csv` 和 `external/macro_monthly_indicator.csv` 为底座，纳入政策利率、LPR、CPI、M2、工业增加值、出口增速和进口增速等字段。
4. 分红与公司行为特征：以 `events/dividend_event.csv` 为底座，纳入现金分红、送股、转增、分红年龄和分红标记。
5. 事件型特征：业绩快报与业绩预告的方向、变化区间、事件新鲜度、区间不确定性和事件强度标记。
6. 公告事件字典：以 `events/major_event_notice.csv` 和 `events/announcement_text.csv` 为底座，纳入近 30 日重大事项条数、严重度、公告标题关键词得分、标题长度均值和公告标记。

当前仍未系统进入训练张量、但已经在数据链中存在或具备扩展价值的特征包括：

1. 更完整的外部宏观变量：当前已纳入政策利率、LPR、CPI、M2、工业增加值、出口与进口增速；仍未覆盖利率期限结构、地产销售、就业、社融分项等更完整的宏观月度表。
2. 更广泛的公告正文与事件细分：当前已纳入公告标题文本、网址索引与重大事项分类，但尚未抓取公告正文全文、附件文本与更细粒度事项标签。
3. 更细粒度的市场微观结构特征：如盘口、成交明细、分钟级时序特征（当前链路尚未纳入）。

## 为什么这些特征不能直接并入训练

这些扩展特征并不是“有数据就能直接使用”，原因主要在于 PIT 安全问题：

1. 财务报表本身属于滞后披露数据，如果只按报告期对齐而不按“公告日后的首个交易日”对齐，会把未来信息提前暴露给模型。
2. 更完整的宏观变量存在公布频率差异与发布时间滞后，若简单向前填充，可能把未在当时可见的信息提前写入。
3. 事件型特征若没有明确“发生时间”和“最早可交易时间”，也会在回测或训练时产生未来泄露。

因此，扩展训练输入的前提不是“特征越多越好”，而是“每一个特征都必须能回答在某个交易日是否已可用”。

## PIT 安全扩展规则

后续若要把上述特征并入训练张量，建议按以下顺序执行：

### 第一步：建立特征字典

每类扩展特征都应有独立的数据字典，至少包含：

1. 特征名称
2. 原始来源表
3. 披露时间字段
4. 实际可用时间字段
5. 更新频率
6. 缺失值处理规则
7. 是否允许向前填充

### 第二步：建立可用时点映射

针对每条记录，明确：

1. 数据对应的报告期或统计期
2. 市场公告日
3. 实际可进入模型的最早交易日

只有当“最早可用交易日”被清楚定义后，该特征才具备并入训练的资格。

### 第三步：在预处理阶段显式区分主线输入与扩展输入

建议将训练输入拆成两层：

1. 主线输入：已稳定验证、口径固定的正式因子面板
2. 扩展输入：通过 PIT 安全校验后，按开关逐步并入的补充特征

这样可以保证：

1. 核心实验结果具有稳定基线
2. 扩展实验能明确观察“新增特征带来了什么变化”
3. 不会因为临时并入新特征而破坏原有正式实验的可复现性

### 第四步：扩展实验与主线实验分开对照

建议至少保留以下对照：

1. 主线因子面板实验
2. 主线 + 市场级代理变量实验
3. 主线 + 财务 PIT 特征实验
4. 主线 + 事件特征实验
5. 主线 + 全部通过校验的扩展输入实验

对每组实验分别比较：

1. 最优秩或最优多线性秩是否变化
2. 解释方差、Rank IC、IR 是否提升
3. 滚动稳定性是否受影响
4. 低维潜在表示的金融解释是否更清晰

## 对论文正文的直接支撑

该说明文档可以直接支撑论文中的三类内容：

1. 第三章“数据来源与样本说明”：说明为什么当前正式训练输入仍以主线因子面板为核心。
2. 第五章“局限性分析”：解释为什么当前只接入了第一版市场代理变量、财务 PIT 和事件特征，而更完整扩展输入仍需继续做 PIT 安全校验。
3. 第六章“创新点与不足/后续展望”：明确下一步扩展方向与执行顺序。

## 当前建议的优先执行顺序

1. 先补齐当前已接入字段的数据字典、公告日与最早可交易日规则。
2. 再继续扩展外部宏观变量的种类与频率对齐规则。
3. 然后继续扩展公告正文、附件文本和更细粒度事件标签。
4. 最后做更长窗口、更广输入集合的扩展实验，并把结果补回论文正文和图表。

## 本轮已落地的统一训练接口字段

扩展版 formal factor panel 现在以 baseline panel 为稳定主线，并在同一个 `factor_columns` 接口中追加以下通过 PIT 校验或市场状态校验的字段：

1. 市场宏观代理层：`market_return_1d`、`market_momentum_5d`、`market_momentum_20d`、`market_volatility_20d`、`market_drawdown_20d`、`market_amount_change_5d`、`market_amount_zscore_20d`、`macro_proxy_risk_score`、`macro_proxy_liquidity_score`。
2. 外部宏观层：`macro_policy_rate`、`macro_lpr_1y`、`macro_lpr_5y`、`macro_cpi_mom`、`macro_m2_yoy`、`macro_industrial_production_yoy`、`macro_exports_yoy`、`macro_imports_yoy`。
3. 财务 PIT 层：`pit_roe_avg`、`pit_np_margin`、`pit_gp_margin`、`pit_eps_ttm`、`pit_data_age_days`。
4. 分红与公司行为层：`dividend_cash_ratio`、`dividend_bonus_ratio`、`dividend_transfer_ratio`、`dividend_age_days`、`dividend_flag`。
5. 业绩与公告事件层：`perf_express_eps_chg_pct`、`perf_express_roe_wa`、`perf_express_gryoy`、`perf_express_opyoy`、`perf_express_age_days`、`perf_express_flag`、`forecast_direction`、`forecast_chg_pct_up`、`forecast_chg_pct_dwn`、`forecast_change_midpoint`、`forecast_change_width`、`forecast_age_days`、`event_positive_flag`、`event_negative_flag`、`event_uncertainty_score`、`event_age_decay_score`、`event_intensity_score`、`major_event_count_30d`、`major_event_severity_score_30d`、`major_event_age_days`、`major_event_flag`、`announcement_count_30d`、`announcement_keyword_score_30d`、`announcement_title_length_mean_30d`、`announcement_flag`、`forecast_flag`。

这些字段已写入 `code/configs/formal_hs300_extended.yaml`、`code/configs/formal_sz50_extended.yaml` 和 `code/configs/formal_zz500_extended.yaml`。复现时先运行：

```powershell
python3 code/data/refresh_formal_factor_panels.py `
  --formal-root code/data/formal `
  --max-trade-date 2026-03-30
```

然后分别运行三份 extended 配置，与对应 baseline 配置比较 Rank IC、IR、解释方差和组合层指标。本轮已新增 `code/data/build_formal_extended_sources.py`，把外部利率、宏观月度指标、分红、重大事项和公告标题文本落盘到 `code/data/formal/external/` 与 `code/data/formal/events/`，并统一映射为 `available_date <= trade_date` 的训练输入。后续若继续扩展到公告正文全文、附件文本、更多宏观品种或更长历史窗口，应沿用同样的 PIT 安全原则，不允许用报告期或自然日期直接前填。
