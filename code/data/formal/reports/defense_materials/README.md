# 答辩材料素材包

本文档用于收口第五章结果页和答辩展示页素材，避免图表、组合结果和训练输入说明分散在不同目录中。

## 素材清单

| 模块 | 文件 | 用途 |
|------|------|------|
| 训练输入扩展 | `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md` | 说明 baseline 与 extended factor panel 的字段边界、PIT 规则和可用时点 |
| 跨样本组合闭环 | `code/data/formal/reports/boundary_portfolio/README.md` | 汇总 Rank IC、Top-N、分组价差、多空、成本后收益、超额收益、回撤、换手、波动、Sharpe 和暴露 |
| 组合闭环机器结果 | `code/data/formal/reports/boundary_portfolio/boundary_portfolio_summary.json` | 支撑答辩页数值复核和表格二次加工 |
| 长窗口复跑入口 | `code/data/formal/reports/long_window_plan/README.md` | 提供全 A、行业分层和市值分层按年度扩展的复跑命令与派生配置 |
| 长窗口组合汇总 | `code/data/formal/reports/long_window_portfolio/README.md` | 汇总 2015-2026 全部年度、全 A / 行业分层 / 市值分层下的跨边界组合、Rank IC 与暴露差异 |
| 长窗口模式发现图组 | `code/data/formal/reports/pattern_discovery_long_window/README.md` | 作为 2015-2026 各年度长窗口模式发现图组的索引入口 |
| 股票潜在结构 | `code/data/formal/reports/pattern_discovery/stock_latent_structure_formal_all_a_run_tucker.svg` | 展示全 A 样本中的股票相似关系 |
| 行业聚类关系 | `code/data/formal/reports/pattern_discovery/cluster_vs_industry_formal_all_a_run_tucker.svg` | 展示潜在聚类与行业标签的对应关系 |
| 样本边界对比 | `code/data/formal/reports/pattern_discovery/boundary_comparison_tucker.svg` | 展示指数、全 A、行业和市值边界下的表现差异 |
| 时间状态切换 | `code/data/formal/reports/defense_materials/long_window_assets/README.md` | 汇总 2015-2026 全部年度的 `formal_all_a_<year>_time_regime_timeline.svg` |
| 因子重要性 | `code/data/formal/reports/defense_materials/long_window_assets/README.md` | 汇总 2015-2026 全部年度的 `formal_all_a_<year>_factor_importance_heatmap.svg` |

## 推荐答辩页顺序

1. 先展示 extended 输入合同，解释为什么所有新增特征必须有 PIT 可用时点。
2. 再展示跨样本组合闭环表，说明排序指标如何转换为组合表现和风险暴露。
3. 接着展示长窗口组合汇总表，说明 2015-2026 全部年度下最优模型如何随市场阶段变化。
4. 再展示长窗口时间状态切换和因子重要性热力图，说明不同年份下潜在结构如何迁移。
5. 然后展示按年度组织的长窗口模式发现图组，回答“模式发现发现了什么”。
6. 最后展示样本边界对比，说明结论在哪些边界上稳定、在哪些边界上需要谨慎外推。

## 复现命令

```powershell
python3 code/data/summarize_boundary_portfolio.py `
  --output-dir code/outputs/formal_hs300_run `
  --output-dir code/outputs/formal_sz50_run `
  --output-dir code/outputs/formal_zz500_run `
  --output-dir code/outputs/formal_all_a_run `
  --output-dir code/outputs/formal_industry_c27_run `
  --output-dir code/outputs/formal_industry_c35_run `
  --output-dir code/outputs/formal_industry_c39_run `
  --output-dir code/outputs/formal_size_small_run `
  --output-dir code/outputs/formal_size_mid_run `
  --output-dir code/outputs/formal_size_large_run `
  --report-dir code/data/formal/reports/boundary_portfolio `
  --exposure-limit 3
```

当前素材包已经同时覆盖短窗口正式快照与 2015-2026 全部 long-window 年度结果；如后续继续补跑新的边界或追加 extended long-window 试验，可在不改变当前叙事结构的前提下继续扩展年度图表。
