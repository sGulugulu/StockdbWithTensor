# 模式发现扩展图组

- 锚定样本：`formal_all_a_run`
- 锚定模型：`tucker`
- 股票潜在结构图：`stock_latent_structure_formal_all_a_run_tucker.svg`
- 聚类与行业交叉图：`cluster_vs_industry_formal_all_a_run_tucker.svg`
- 跨样本边界对比图：`boundary_comparison_tucker.svg`

这些图由 formal run 的 `selection_*.json`、`metrics.json`、`group_returns_*.json` 与因子面板行业字段生成，用于补足股票联动结构、行业聚类关系和样本边界差异的可视化证据。

## 答辩页素材映射

| 答辩页主题 | 直接素材 | 讲解要点 |
|------------|----------|----------|
| 潜在股票结构 | `stock_latent_structure_formal_all_a_run_tucker.svg` | 展示 Tucker 潜在表示中股票相似结构是否按行业或收益表现聚集 |
| 行业聚类关系 | `cluster_vs_industry_formal_all_a_run_tucker.svg` | 说明低维结构不是单纯复制行业标签，而是在行业内外形成相似性分组 |
| 样本边界对比 | `boundary_comparison_tucker.svg` | 对比指数样本、全 A、行业分层和市值分层下的 Rank IC 与组合表现差异 |
| 时间状态切换 | `code/data/formal/reports/defense_materials/long_window_assets/` 下的 `formal_all_a_<year>_time_regime_timeline.svg` | 用于解释各长窗口年份中的市场状态变化 |
| 因子重要性 | `code/data/formal/reports/defense_materials/long_window_assets/` 下的 `formal_all_a_<year>_factor_importance_heatmap.svg` | 用于说明不同年份下价值、动量、质量、波动率及扩展输入的贡献差异 |

若需要直接引用长窗口模式发现图组，优先使用 `code/data/formal/reports/pattern_discovery_long_window/README.md` 作为年度索引，再进入对应年份目录。面向最终答辩时，则优先使用 `code/data/formal/reports/defense_materials/README.md` 中的素材包清单，该清单把短窗口图组、长窗口组合汇总和 extended 输入合同放在同一条讲述路径下。
