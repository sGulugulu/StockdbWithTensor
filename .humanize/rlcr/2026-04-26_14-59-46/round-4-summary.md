# Round 4 Summary

## 本轮完成内容

1. 将增强版 `output.py` 从已验证工作树移植回根仓库，使根仓库正式输出现在真实生成以下图组：
   - `model_metrics_overview.svg`
   - `time_regime_timeline.svg`
   - `factor_importance_heatmap.svg`
   - 修正后的 `model_explained_variance.svg`
   - 修正后的 `model_rank_ic.svg`
2. 重新运行三组 formal 实验：
   - `formal_hs300`
   - `formal_sz50`
   - `formal_zz500`
   使增强图组真正落盘到正式输出目录。
3. 修正论文中的时间状态表述：
   - 把原先不符合当前根仓库结果的 2024/2025 跳变说法改成基于当前正式 `time_regimes_tucker.json` 的 2026 年 3 月区间描述。
4. 修复 LaTeX 编译错误：
   - 将正文中直接书写的带下划线文件名改为 `\texttt{time\_regimes\_tucker.json}`，避免 XeLaTeX 把它解释成数学下标。
5. 落地 AC1 的第一版“真实扩展输入合同”：
   - 新增 `code/data/build_extended_factor_panel.py`
   - 新增 `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`
   - 新增三份 extended formal 配置：
     - `formal_hs300_extended.yaml`
     - `formal_sz50_extended.yaml`
     - `formal_zz500_extended.yaml`
   - 把一类真实财务 PIT 特征和一类业绩快报事件特征接入扩展版 factor panel：
     - `pit_roe_avg`
     - `pit_np_margin`
     - `pit_gp_margin`
     - `pit_eps_ttm`
     - `perf_express_eps_chg_pct`
     - `perf_express_roe_wa`
     - `perf_express_gryoy`
     - `perf_express_opyoy`
     - `perf_express_flag`
6. 生成并运行三组 extended 对照实验：
   - `formal_hs300_extended_run`
   - `formal_sz50_extended_run`
   - `formal_zz500_extended_run`
   并新增一份对照结果文档 `扩展特征对照实验结果.md`。
7. 继续收口 AC1 / AC4：
   - 重写第五章中的解释方差、Rank IC 与稳定性手工数值，使其与当前 committed formal `metrics.json` 一致。
   - 在“扩展特征对照分析”一节中补入 baseline / extended 的样本池差异说明。
   - 更新 `code/data/formal/factors/README.md`，把 extended panel 的字段与标准构建命令纳入正式说明。
   - 补强 `test_extended_factor_panel.py`，新增公告日前后 `perf_express_flag` 与事件值生效边界断言。
8. 继续推进 AC2 的组合层闭环：
   - 在 `evaluation.py` 中新增组合层回测汇总逻辑，输出 Top-N 日收益、累计净值、回撤、换手率、行业/风格暴露。
   - 在 `output.py` 中新增 `portfolio_metrics.*`、`group_returns_*.*`、`drawdown_*.*`、`exposure_*.*` 产物落盘。
   - 重跑三组 baseline formal 和三组 extended formal，使这些组合层文件真实写入正式输出目录。
   - 在第五章“选股有效性分析”中补入“排序指标与组合结果并不完全同步”的分析段落。

## 修改文件

- `code/stock_tensor/output.py`
- `paper_body.tex`
- `code/data/build_extended_factor_panel.py`
- `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`
- `code/configs/formal_hs300_extended.yaml`
- `code/configs/formal_sz50_extended.yaml`
- `code/configs/formal_zz500_extended.yaml`
- `code/tests/test_extended_factor_panel.py`
- `code/tests/test_config_profiles.py`
- `扩展特征对照实验结果.md`
- `code/data/formal/factors/README.md`
- `code/stock_tensor/evaluation.py`
- `code/stock_tensor/output.py`
- `code/stock_tensor/pipeline.py`
- `code/tests/test_pipeline.py`
- `code/outputs/formal_hs300_run/*`
- `code/outputs/formal_sz50_run/*`
- `code/outputs/formal_zz500_run/*`
- `code/outputs/formal_hs300_extended_run/*`
- `code/outputs/formal_sz50_extended_run/*`
- `code/outputs/formal_zz500_extended_run/*`
- `.humanize/rlcr/2026-04-26_14-59-46/round-4-summary.md`

## 测试与验证

- 已通过：
  - `python -m unittest discover -s code/tests -p test_pipeline.py`
  - `python -m unittest discover -s code/tests -p test_config.py`
  - `python -m unittest discover -s code/tests -p test_extended_factor_panel.py`
  - `python -m unittest discover -s code/tests -p test_config_profiles.py`
  - `python -m unittest discover -s code/tests -p test_pipeline.py`
  - `python code/main.py --config code/configs/formal_hs300.yaml`
  - `python code/main.py --config code/configs/formal_sz50.yaml`
  - `python code/main.py --config code/configs/formal_zz500.yaml`
  - `python code/main.py --config code/configs/formal_hs300_extended.yaml`
  - `python code/main.py --config code/configs/formal_sz50_extended.yaml`
  - `python code/main.py --config code/configs/formal_zz500_extended.yaml`
  - `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error -outdir=.latex-build template.tex`

- 验证结果：
  - 三个 formal 输出目录都已包含增强图组文件。
  - 三个 extended formal 输出目录已成功生成，可用于 baseline / extended 对照。
  - 论文可继续编译。
  - 时间状态描述已与当前正式 `time_regimes_tucker.json` 结果一致。
  - 第一版扩展特征已经真实进入训练接口，而不再只停留在说明文档。
  - PIT 边界测试已锁定“公告日前不生效、公告日及之后才生效”的核心约束。
  - baseline 与 extended 的 formal 输出目录都已真实生成 `portfolio_metrics`、`group_returns`、`drawdown` 与 `exposure` 文件。
  - 第五章已经开始使用组合层结果解释“Rank IC 与组合表现不完全同步”的现象。

## 当前未完成项

1. AC1：虽然扩展版 factor panel 与 extended 配置已落地，但扩展特征仍只覆盖财务 PIT 与业绩快报，宏观变量和更多事件特征尚未接入；论文正文也还未系统吸收 baseline/extended 对照结果。
2. AC2：组合层产物已进入正式输出，但收益分组、回撤、换手与暴露结果尚未进一步扩展成完整图表和更系统的论文章节比较。
3. AC3：全 A / 行业分层 / 市值分层实验仍未落地。
4. AC5：参考文献最终条目规范化仍未完成。

## Goal Tracker Update Request

### Requested Changes:
- 将 “实现模式发现增强图与图文解释” 状态从 `pending` 更新为 `in_progress`，备注改为：增强图组已落地到 formal 输出目录，正文中的时间状态描述已开始按真实产物修正，但股票潜在结构图和样本边界对比图仍待继续补齐。
- 在 Open Issues 中删除或弱化“正文对时间状态图和热力图的引用仍没有对应产物”这一项，因为增强图组已经真实写出。
- 保留 AC4 未完成状态，因为当前只完成了增强图组中的一部分真实输出与正文收口。
- 将 AC1 中与“扩展特征接入训练接口并生成扩展版 factor panel”相关任务状态提升为 `in_progress`，并增加备注：第一版 PIT/业绩快报扩展列已接入，三组 extended formal 配置和输出已生成，但宏观变量与更完整事件特征尚未并入。
- 在 Open Issues 中新增：扩展特征目前仅覆盖财务 PIT 与业绩快报，baseline/extended 对照结果显示不同样本池表现差异较大，仍需进一步做特征筛选与口径扩展。
- 将 AC2 中与“组合回测闭环”相关任务状态提升为 `in_progress`，备注改为：组合层结构化产物已落盘，但进一步的图表扩展和章节化分析仍未完成。

### Justification:
本轮工作不仅将模式发现增强图从“论文声明”推进为“正式产物已落盘”，还把第一版真实扩展特征接入了训练接口，并生成了三组 extended 对照输出，同时把组合层结构化回测产物落入 formal 输出目录。Tracker 需要反映 AC1、AC2 与 AC4 的真实推进状态，但由于扩展特征范围、组合结果图表化和样本边界扩展都还没收口，因此仍不能把这些 AC 标为完成。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: 当前 `.humanize/bitlesson.md` 仍为空知识库；本轮增强图组移植任务未匹配到既有 lesson。
