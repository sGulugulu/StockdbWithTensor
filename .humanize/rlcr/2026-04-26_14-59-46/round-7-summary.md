# Round 7 Summary

## Work Completed

- 按 Round 6 review 的 AC2 directive，扩展了组合回测闭环的第一版正式合同：
  - 在 `code/stock_tensor/config.py` 中为 `evaluation` 增加：
    - `quantile_count`
    - `transaction_cost_bps`
    - `benchmark_path`
  - 在 6 个 formal / extended 配置中显式写入分位数、交易成本和样本池基准指数路径
- 扩展 `code/stock_tensor/evaluation.py` 的 `build_portfolio_backtest`：
  - 新增分位数组收益与累计净值
  - 新增 `top-bottom` 多空组合
  - 新增扣除 `turnover * cost_bps` 后的成本净值
  - 新增相对样本池基准指数的超额收益与超额回撤
  - 保留原有 Top-N、回撤、换手率和行业/主导因子暴露结果
- 扩展 `code/stock_tensor/pipeline.py`：
  - 加载样本池 benchmark 日收益
  - 将 `quantile_count`、`transaction_cost_bps`、`benchmark_path` 写入 run manifest
  - 将新回测产物传递给输出层
- 扩展 `code/stock_tensor/output.py`：
  - 落盘 `quantile_returns_*`
  - 落盘 `long_short_*`
  - 落盘 `cost_adjusted_*`
  - 落盘 `excess_returns_*`
  - 新增：
    - `long_short_overview.svg`
    - `cost_adjusted_overview.svg`
    - `excess_returns_overview.svg`
- 更新 smoke / formal 测试：
  - `code/tests/test_pipeline.py`
  - `code/tests/test_formal_config.py`
- 重跑 6 组 committed formal / extended 输出，确认新产物真实落盘
- 回写论文：
  - `paper_body.tex` 已将分位数组、多空、成本后净值和超额收益结果纳入第五章与局限性分析

## Files Changed

- `code/stock_tensor/config.py`
- `code/stock_tensor/evaluation.py`
- `code/stock_tensor/pipeline.py`
- `code/stock_tensor/output.py`
- `code/configs/formal_hs300.yaml`
- `code/configs/formal_sz50.yaml`
- `code/configs/formal_zz500.yaml`
- `code/configs/formal_hs300_extended.yaml`
- `code/configs/formal_sz50_extended.yaml`
- `code/configs/formal_zz500_extended.yaml`
- `code/tests/test_pipeline.py`
- `code/tests/test_formal_config.py`
- `code/outputs/formal_hs300_run/*`
- `code/outputs/formal_sz50_run/*`
- `code/outputs/formal_zz500_run/*`
- `code/outputs/formal_hs300_extended_run/*`
- `code/outputs/formal_sz50_extended_run/*`
- `code/outputs/formal_zz500_extended_run/*`
- `paper_body.tex`
- `.humanize/rlcr/2026-04-26_14-59-46/round-7-summary.md`

## Validation

以下验证均在当前 Windows 主机 PowerShell 环境中执行：

- `python -m unittest discover -s code/tests -p test_pipeline.py`：通过
- `python -m unittest discover -s code/tests -p test_config_profiles.py`：通过
- `python -m unittest discover -s code/tests -p test_formal_config.py`：通过
- `python code/main.py --config code/configs/formal_hs300.yaml`：通过
- `python code/main.py --config code/configs/formal_sz50.yaml`：通过
- `python code/main.py --config code/configs/formal_zz500.yaml`：通过
- `python code/main.py --config code/configs/formal_hs300_extended.yaml`：通过
- `python code/main.py --config code/configs/formal_sz50_extended.yaml`：通过
- `python code/main.py --config code/configs/formal_zz500_extended.yaml`：通过

额外核实：

- `formal_hs300_run` 已真实包含：
  - `quantile_returns_cp.json`
  - `long_short_cp.json`
  - `cost_adjusted_cp.json`
  - `excess_returns_cp.json`
  - `long_short_overview.svg`
  - `cost_adjusted_overview.svg`
  - `excess_returns_overview.svg`
- 六组 formal / extended 输出目录都已包含上述新产物
- `paper_body.tex` 已使用新的多空、成本后净值和超额收益结果补写第五章

## Remaining Items

- AC1：第一版完整扩展输入合同已落地，但更完整宏观变量与更广泛事件字典仍未完成
- AC2：已补齐分位数组、多空、成本和超额收益基础合同，但更长窗口稳健性检验与更系统暴露比较仍未完成
- AC3：全 A / 行业分层 / 市值分层实验仍未落地
- AC4：股票潜在结构图、行业聚类图和样本边界对比图仍未完成
- AC5：参考文献条目级元数据补齐与最终格式统一仍未完成
- 仓库验证入口说明仍需继续统一，避免 WSL/Windows 解释器差异造成误解

## Goal Tracker Update Request

### Requested Changes:
- 更新 AC2 中 `实现 Top-N/分组收益/回撤/风险暴露计算` 的备注，说明已进一步落地分位数组、多空、成本后净值和超额收益产物
- 更新 AC2 中 `将组合层结果与 Rank IC 指标联动分析并回写第五章` 的备注，说明第五章已吸收新的多空、成本和超额收益证据
- 将 Open Issues 中“组合层虽然已生成净值曲线和回撤图，但严格分位数组收益、交易成本和更系统的暴露/超额收益分析仍未完成”收紧为“分位数组、交易成本和超额收益基础合同已完成，但更长窗口稳健性检验与更系统暴露比较仍未完成”
- 在 Plan Evolution Log 中记录：Round 7 已把 AC2 从 Top-N 基础闭环推进到分位数组/多空/成本/超额收益的第一版正式合同

### Justification:
Round 7 的核心工作是真实推进 AC2。当前 committed outputs 已不再只有 Top-N 基础净值和回撤，而是新增了分位数组、多空、成本后净值和基准超额收益四类结构化证据，并且这些结果已经回写到第五章。Tracker 需要同步这一步推进，否则后续 review 会继续沿用过时的 AC2 状态描述。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes:
  - 已按流程读取 `.humanize/bitlesson.md`
  - `bitlesson-select.sh` 仍因本地 selector 流式请求断开不可用，且当前知识库无有效条目，因此本轮继续按 `NONE` 执行
