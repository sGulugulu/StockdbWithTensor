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
5. 回写论文正文：
   - 第四章实验设置改为明确说明 formal profile、factor panel 快照与输出目录统一到 `2026-03-30`。
   - “选股有效性分析”补入基于组合净值/回撤图的 baseline 与 extended 数值比较。
   - 局限性分析与结论部分改为：当前已具备 Top-N 组合净值、回撤与暴露基础证据，但仍缺分位数组、交易成本与超额收益闭环。
6. 新增与补强测试：
   - `test_formal_factor_panel.py` 新增 baseline panel 截断日期测试。
   - `test_extended_factor_panel.py` 新增 extended panel 截断日期测试。
   - 新增 `test_refresh_formal_factor_panels.py`，验证统一刷新入口能同时生成 baseline/extended 六个 panel，并按 `max_trade_date` 截断。

## 修改文件

- `README.md`
- `paper_body.tex`
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

- 额外核实：
  - 六个 baseline/extended factor panel 的最大 `trade_date` 均为 `2026-03-30`。
  - 六组 formal 输出目录均已存在 `group_returns_overview.svg` 与 `drawdown_overview.svg`。
  - 六组 formal 输出目录的 `run_manifest.json` 中，`requested_end_date` 与 `actual_end_date` 均为 `2026-03-30`。

- 未完成但已定位：
  - `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error -outdir=.latex-build template.tex`
    当前调用因 `latexmk` 的 `-outdir` 参数在此环境下被拆分为独立 token 而失败，属于命令行参数传递问题，不是 `template.tex` 本身的 XeLaTeX 语法错误；需要在下一轮改用兼容此环境的调用方式重新验证。

## 当前未完成项

1. AC1：扩展特征仍只覆盖财务 PIT 与业绩快报，宏观变量与更完整事件字典尚未接入。
2. AC2：组合层已经具备净值曲线、回撤曲线和基础暴露，但严格分位数组、交易成本、超额收益和更系统的暴露比较仍未完成。
3. AC3：全 A / 行业分层 / 市值分层实验仍未落地。
4. AC4：股票潜在结构图、行业聚类图和样本边界对比图仍未完成。
5. AC5：参考文献条目级元数据补齐与最终格式统一仍未完成。

## Goal Tracker Update Request

### Requested Changes:
- 将 `修复 formal 因子面板与正式输出实际窗口仅覆盖 2026-03 的口径错位` 标记为 `completed`。
- 将 `将 baseline/extended 对照结果回写第三章与局限性分析` 从 `pending` 提升为 `in_progress`。
- 将 AC2 中 `实现 Top-N/分组收益/回撤/风险暴露计算` 的备注更新为：结构化产物与净值/回撤 SVG 已落盘，但严格分位数组收益与交易成本场景仍未完成。
- 删除 Open Issues 中“formal 因子面板与正式输出时间窗口不一致”和“组合层图形化产物仍未生成”两项旧问题。
- 新增 Open Issue：组合层仍缺分位数组、交易成本和超额收益等更完整回测合同。

### Justification:
本轮已经把 AC1 的窗口口径和 extended 刷新入口收口成可复现合同，并把 AC2 从“只有结构化 JSON”推进到“结构化 JSON + SVG 图形产物 + 论文数值分析”阶段。Tracker 需要准确反映这些真实进展，同时保留尚未完成的更深层组合回测和扩展特征任务。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes:
  - 已按 RLCR 提示读取 `.humanize/bitlesson.md`。
  - 两次调用 `bitlesson-select.sh` 时都因本地 selector 流式请求断开而失败，且当前知识库无任何条目，因此本轮按 `NONE` 执行；后续若知识库增加内容，可重新尝试 selector。
