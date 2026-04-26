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

## 修改文件

- `code/stock_tensor/output.py`
- `paper_body.tex`
- `code/outputs/formal_hs300_run/*`
- `code/outputs/formal_sz50_run/*`
- `code/outputs/formal_zz500_run/*`
- `.humanize/rlcr/2026-04-26_14-59-46/round-4-summary.md`

## 测试与验证

- 已通过：
  - `python -m unittest discover -s code/tests -p test_pipeline.py`
  - `python -m unittest discover -s code/tests -p test_config.py`
  - `python code/main.py --config code/configs/formal_hs300.yaml`
  - `python code/main.py --config code/configs/formal_sz50.yaml`
  - `python code/main.py --config code/configs/formal_zz500.yaml`
  - `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error -outdir=.latex-build template.tex`

- 验证结果：
  - 三个 formal 输出目录都已包含增强图组文件。
  - 论文可继续编译。
  - 时间状态描述已与当前正式 `time_regimes_tucker.json` 结果一致。

## 当前未完成项

1. AC1：扩展特征真实接入训练接口、扩展版 factor panel 和 baseline/extended 对照实验仍未完成。
2. AC2：组合回测闭环仍未落地，当前仍停留在候选池与排序指标层。
3. AC3：全 A / 行业分层 / 市值分层实验仍未落地。
4. AC5：参考文献最终条目规范化仍未完成。

## Goal Tracker Update Request

### Requested Changes:
- 将 “实现模式发现增强图与图文解释” 状态从 `pending` 更新为 `in_progress`，备注改为：增强图组已落地到 formal 输出目录，正文中的时间状态描述已开始按真实产物修正，但股票潜在结构图和样本边界对比图仍待继续补齐。
- 在 Open Issues 中删除或弱化“正文对时间状态图和热力图的引用仍没有对应产物”这一项，因为增强图组已经真实写出。
- 保留 AC4 未完成状态，因为当前只完成了增强图组中的一部分真实输出与正文收口。

### Justification:
本轮工作已将模式发现增强图从“论文声明”推进为“正式产物已落盘”，这是真实代码与输出进展，不应继续按“完全未开始”描述；但由于 AC4 仍缺股票潜在结构图与样本边界对比图，所以不能标为完成。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: 当前 `.humanize/bitlesson.md` 仍为空知识库；本轮增强图组移植任务未匹配到既有 lesson。
