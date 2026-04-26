# Round 4 Summary

## 本轮完成内容

1. 收口 AC1 的 formal 窗口口径：
   - 新增统一刷新入口 `code/data/refresh_formal_factor_panels.py`。
   - 为 `build_formal_factor_panel.py` 与 `build_extended_factor_panel.py` 增加 `max_trade_date` 截断能力。
   - 将 6 份 formal / extended 配置的 `market.end_date` 统一改为 `2026-03-30`。
   - 重建 6 个 baseline/extended factor panel，使最大 `trade_date` 全部收口到 `2026-03-30`。
   - 重跑 6 组 formal 输出，使 `run_manifest.json` 中的 `requested_end_date` 与 `actual_end_date` 全部统一为 `2026-03-30`。
2. 收口 AC1 的 extended 主构建链：
   - 在 `code/data/formal/factors/README.md` 中将 `refresh_formal_factor_panels.py` 明确为 baseline/extended 的统一刷新入口。
   - 在 `README.md` 与 `code/data/formal/README.md` 中补充“raw formal 数据窗口”和“提交版实验快照窗口”两层口径说明。
   - 更新《训练输入扩展与PIT安全说明》，把旧的 `2026-04-03` vs `2026-03-30` 失配表述改为已统一口径。
3. 推进 AC2 的组合层图形化证据链：
   - 在 `code/stock_tensor/output.py` 中新增多模型折线 SVG 生成逻辑。
   - 六组 baseline/extended formal 输出现在真实生成：
     - `group_returns_overview.svg`
     - `drawdown_overview.svg`
   - `summary.md` 产物清单已同步纳入这两类 SVG。
4. 扩展 AC2 的测试合同：
   - `test_pipeline.py` 新增对组合净值、回撤、首日换手、累计收益与最大回撤一致性的断言。
   - `test_formal_config.py` 新增对 `portfolio_metrics.json`、`group_returns_overview.svg`、`drawdown_overview.svg` 的存在性断言。
5. 修复 Round 4 复审暴露的 formal 标签退化问题：
   - `build_formal_factor_panel.py` 改为先按股票全量 K 线计算动量与 `future_return`，再按 universe history 与 `max_trade_date` 输出提交版样本窗口。
   - `test_formal_factor_panel.py` 补充“截断但保留非零未来收益标签”的单测。
   - `test_refresh_formal_factor_panels.py` 补充“刷新后的提交版 tail 窗口仍有非零 `future_return`”断言。
   - `test_formal_config.py` 补充“组合层结果不能全部退化为平线”的回归断言。
6. 重新生成 6 个 factor panel 和 6 组 formal / extended 输出后，组合层证据恢复为真实非平线结果：
   - baseline HS300：Tucker 组合累计收益 2.11\%，最大回撤 $-0.03\%$
   - baseline SZ50：Tucker 组合累计收益 $-0.33\%$，最大回撤 $-0.37\%$
   - extended ZZ500：PCA / Tucker 组合累计收益分别为 3.33\% / 3.30\%
7. 回写论文正文与对照文档：
   - `paper_body.tex` 已按当前 committed `metrics.json` / `portfolio_metrics.json` 重写解释方差、Rank IC、稳定性、累计收益和最大回撤的核心数值。
   - `扩展特征对照实验结果.md` 已按当前 committed outputs 更新 baseline/extended 对照表及观察结论。
8. LaTeX 验证已补齐：
   - `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error "-outdir=.latex-build" template.tex` 编译通过。

## 修改文件

- `README.md`
- `paper_body.tex`
- `扩展特征对照实验结果.md`
- `训练输入扩展与PIT安全说明.md`
- `code/configs/formal_hs300.yaml`
- `code/configs/formal_sz50.yaml`
- `code/configs/formal_zz500.yaml`
- `code/configs/formal_hs300_extended.yaml`
- `code/configs/formal_sz50_extended.yaml`
- `code/configs/formal_zz500_extended.yaml`
- `code/data/build_formal_factor_panel.py`
- `code/data/build_extended_factor_panel.py`
- `code/data/refresh_formal_factor_panels.py`
- `code/data/formal/README.md`
- `code/data/formal/factors/README.md`
- `code/data/formal/factors/hs300_factor_panel.csv`
- `code/data/formal/factors/hs300_factor_panel_extended.csv`
- `code/data/formal/factors/sz50_factor_panel.csv`
- `code/data/formal/factors/sz50_factor_panel_extended.csv`
- `code/data/formal/factors/zz500_factor_panel.csv`
- `code/data/formal/factors/zz500_factor_panel_extended.csv`
- `code/stock_tensor/output.py`
- `code/tests/test_backend.py`
- `code/tests/test_config_profiles.py`
- `code/tests/test_extended_factor_panel.py`
- `code/tests/test_formal_config.py`
- `code/tests/test_formal_factor_panel.py`
- `code/tests/test_pipeline.py`
- `code/tests/test_refresh_formal_factor_panels.py`
- `code/outputs/formal_hs300_run/*`
- `code/outputs/formal_sz50_run/*`
- `code/outputs/formal_zz500_run/*`
- `code/outputs/formal_hs300_extended_run/*`
- `code/outputs/formal_sz50_extended_run/*`
- `code/outputs/formal_zz500_extended_run/*`
- `.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md`
- `.humanize/rlcr/2026-04-26_14-59-46/round-4-summary.md`

## 测试与验证

- 已通过：
  - `python -m unittest discover -s code/tests -p test_formal_factor_panel.py`
  - `python -m unittest discover -s code/tests -p test_extended_factor_panel.py`
  - `python -m unittest discover -s code/tests -p test_refresh_formal_factor_panels.py`
  - `python -m unittest discover -s code/tests -p test_pipeline.py`
  - `python -m unittest discover -s code/tests -p test_config_profiles.py`
  - `python -m unittest discover -s code/tests -p test_formal_config.py`
  - `python -m unittest discover -s code/tests -p test_backend.py`
  - `python code/data/refresh_formal_factor_panels.py --formal-root code/data/formal --max-trade-date 2026-03-30`
  - `python code/main.py --config code/configs/formal_hs300.yaml`
  - `python code/main.py --config code/configs/formal_sz50.yaml`
  - `python code/main.py --config code/configs/formal_zz500.yaml`
  - `python code/main.py --config code/configs/formal_hs300_extended.yaml`
  - `python code/main.py --config code/configs/formal_sz50_extended.yaml`
  - `python code/main.py --config code/configs/formal_zz500_extended.yaml`
  - `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error "-outdir=.latex-build" template.tex`

- 额外核实：
  - 三个 baseline factor panel 在 `2026-03-25` 至 `2026-03-30` 的 tail 窗口已恢复大量非零 `future_return`。
  - 六组 formal 输出的 `portfolio_metrics.json` 已不再全部退化为零平线。
  - `paper_body.tex` 与 `扩展特征对照实验结果.md` 已按当前 committed `metrics.json` / `portfolio_metrics.json` 回填关键数值。

## 当前未完成项

1. AC1：扩展特征仍只覆盖财务 PIT 与业绩快报，宏观变量与更完整事件字典尚未接入。
2. AC2：组合层已经具备净值曲线、回撤曲线和基础暴露，但严格分位数组、交易成本、超额收益和更系统的暴露比较仍未完成。
3. AC3：全 A / 行业分层 / 市值分层实验仍未落地。
4. AC4：股票潜在结构图、行业聚类图和样本边界对比图仍未完成。
5. AC5：参考文献条目级元数据补齐与最终格式统一仍未完成。

## Goal Tracker Update Request

### Requested Changes:
- 将 `修复 factor panel 截断后测试窗口 future_return 全为 0 的标签退化` 标记为 `completed`。
- 更新 AC2 中组合层任务备注，说明六组 formal 输出已经恢复为非平线结果。
- 删除 Open Issues 中“formal factor panel 标签退化为 0 平线”和“正文/对照文档数值未与 committed outputs 对齐”两项已解决问题。
- 在 `Completed and Verified` 中新增“修复 formal factor panel 截断导致的组合层平线退化”。

### Justification:
Round 4 复审指出的问题已经被真实修复：组合层产物不再只是“图存在”，而是重新恢复为有数值信息的有效证据；论文正文和对照文档也已同步到当前 committed outputs。Tracker 需要反映这一步收口，否则后续 review 仍会把已修复的问题当成当前阻塞。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes:
  - 已按 RLCR 提示读取 `.humanize/bitlesson.md`。
  - `bitlesson-select.sh` 仍因本地 selector 流式请求断开而不可用，且当前知识库无有效条目，因此本轮继续按 `NONE` 执行。
