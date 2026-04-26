# Round 5 Summary

## Work Completed

- 修复 `code/data/build_formal_factor_panel.py` 的 formal 标签生成顺序：
  - 不再先按 `max_trade_date` 和 universe history 裁掉 K 线再计算 `future_return`
  - 改为先按股票全量 K 线计算动量与未来 5 日收益，再在输出阶段按 universe history 和 `max_trade_date` 过滤提交版样本窗口
- 补充回归测试，防止组合层再次退化为平线：
  - `code/tests/test_formal_factor_panel.py`
  - `code/tests/test_refresh_formal_factor_panels.py`
  - `code/tests/test_formal_config.py`
- 重建 6 个 baseline/extended factor panel，并重跑 6 组 formal / extended 输出：
  - baseline：`formal_hs300_run`、`formal_sz50_run`、`formal_zz500_run`
  - extended：`formal_hs300_extended_run`、`formal_sz50_extended_run`、`formal_zz500_extended_run`
- 已恢复 committed formal 组合层证据的数值有效性：
  - 三个 baseline factor panel 在 `2026-03-25` 至 `2026-03-30` 的 tail 窗口已重新出现大量非零 `future_return`
  - 六组 formal 输出的 `portfolio_metrics.json` 不再是全零平线
- 按当前 committed outputs 回填文稿数值：
  - `paper_body.tex` 已同步解释方差、Rank IC、稳定性、累计收益和最大回撤
  - `扩展特征对照实验结果.md` 已同步 baseline/extended 对照表和结论
- 扩展 AC1 的第一版完整输入合同：
  - 在 `code/data/build_extended_factor_panel.py` 中新增市场级代理变量：
    - `market_return_1d`
    - `market_momentum_5d`
    - `market_volatility_20d`
    - `market_amount_change_5d`
  - 新增业绩预告事件特征：
    - `forecast_direction`
    - `forecast_chg_pct_up`
    - `forecast_chg_pct_dwn`
    - `forecast_flag`
  - 财务 PIT、业绩快报和业绩预告均改为“公告日后的首个交易日可用”规则，而不是公告当日直接生效
  - `code/data/refresh_formal_factor_panels.py` 已把 index daily 与 `forecast_report` 纳入 extended panel 的统一刷新入口
- 同步更新合同与说明文档：
  - `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`
  - `code/data/formal/factors/README.md`
  - `训练输入扩展与PIT安全说明.md`
- 已重建 3 个 extended factor panel 并重跑 3 组 extended formal 输出，确认新列真实进入训练，而不只是落到 CSV
- 已重新执行 LaTeX 编译验证，`template.tex` 可用 XeLaTeX 正常生成 PDF

## Files Changed

- `code/data/build_formal_factor_panel.py`
- `code/data/build_extended_factor_panel.py`
- `code/data/refresh_formal_factor_panels.py`
- `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`
- `code/data/formal/factors/README.md`
- `code/data/formal/factors/hs300_factor_panel.csv`
- `code/data/formal/factors/hs300_factor_panel_extended.csv`
- `code/data/formal/factors/sz50_factor_panel.csv`
- `code/data/formal/factors/sz50_factor_panel_extended.csv`
- `code/data/formal/factors/zz500_factor_panel.csv`
- `code/data/formal/factors/zz500_factor_panel_extended.csv`
- `code/configs/formal_hs300_extended.yaml`
- `code/configs/formal_sz50_extended.yaml`
- `code/configs/formal_zz500_extended.yaml`
- `code/tests/test_config_profiles.py`
- `code/tests/test_extended_factor_panel.py`
- `code/tests/test_formal_config.py`
- `code/tests/test_formal_factor_panel.py`
- `code/tests/test_refresh_formal_factor_panels.py`
- `paper_body.tex`
- `扩展特征对照实验结果.md`
- `训练输入扩展与PIT安全说明.md`
- `.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md`
- `.humanize/rlcr/2026-04-26_14-59-46/round-4-summary.md`
- `.humanize/rlcr/2026-04-26_14-59-46/round-5-summary.md`

## Validation

- `python -m unittest discover -s code/tests -p test_formal_factor_panel.py`：通过
- `python -m unittest discover -s code/tests -p test_refresh_formal_factor_panels.py`：通过
- `python -m unittest discover -s code/tests -p test_extended_factor_panel.py`：通过
- `python -m unittest discover -s code/tests -p test_pipeline.py`：通过
- `python -m unittest discover -s code/tests -p test_formal_config.py`：通过
- `python -m unittest discover -s code/tests -p test_config_profiles.py`：通过
- `python code/data/refresh_formal_factor_panels.py --formal-root code/data/formal --max-trade-date 2026-03-30`：通过
- `python code/main.py --config code/configs/formal_hs300.yaml`：通过
- `python code/main.py --config code/configs/formal_sz50.yaml`：通过
- `python code/main.py --config code/configs/formal_zz500.yaml`：通过
- `python code/main.py --config code/configs/formal_hs300_extended.yaml`：通过
- `python code/main.py --config code/configs/formal_sz50_extended.yaml`：通过
- `python code/main.py --config code/configs/formal_zz500_extended.yaml`：通过
- `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error "-outdir=.latex-build" template.tex`：通过

## Remaining Items

- AC1：扩展特征已经扩展到“市场级代理变量 + 财务 PIT + 快报 + 预告”，但更完整宏观变量与更广泛事件字典尚未接入
- AC2：组合层虽已恢复为有效非平线结果，但严格分位数组、交易成本、超额收益和更系统暴露比较仍未完成
- AC3：全 A / 行业分层 / 市值分层实验仍未落地
- AC4：股票潜在结构图、行业聚类图和样本边界对比图仍未完成
- AC5：参考文献条目级元数据补齐与最终格式统一仍未完成

## Goal Tracker Update Request

### Requested Changes:
- 将 `修复 factor panel 截断后测试窗口 future_return 全为 0 的标签退化` 标记为 `completed`
- 更新 AC2 组合层相关任务备注，说明六组 formal 输出已经恢复为非平线结果
- 删除 Open Issues 中“formal factor panel 标签退化为 0 平线”和“正文/对照文档数值未与 committed outputs 对齐”两项已解决问题
- 在 `Completed and Verified` 中新增“修复 formal factor panel 截断导致的组合层平线退化”
- 将 AC1 中 `将通过 PIT 校验的扩展特征接入统一训练接口并生成扩展版 factor panel` 的备注更新为：已接入市场级代理变量、财务 PIT、业绩快报和业绩预告四类第一版特征

### Justification:
Round 4 复审指出的最高优先级问题已经被真实修复：当前 committed formal 输出重新具备可用标签、非平线组合证据以及与产物一致的论文和对照文档。同时，AC1 已从“财务 PIT + 快报”进一步推进到“市场级代理变量 + 财务 PIT + 快报 + 预告”的第一版完整扩展输入。Tracker 需要同步这些进展，否则后续 review 会继续把已解决或已推进的问题当作当前阻塞。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes:
  - 已按流程读取 `.humanize/bitlesson.md`
  - `bitlesson-select.sh` 仍因本地 selector 流式请求断开不可用，且当前知识库无有效条目，因此本轮继续按 `NONE` 执行
