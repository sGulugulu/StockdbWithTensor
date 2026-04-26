# Round 8 Summary

## Work Completed

- 修复 ZZ500 benchmark contract：
  - 在 `code/data/import_tdx_vipdoc.py` 中新增 `zz500_index_daily.csv -> sh000905.day`
  - 用现有 TongDaXin 数据真实生成 `code/data/formal/index_daily/zz500_index_daily.csv`
  - 将 `code/data/refresh_formal_factor_panels.py` 中 ZZ500 的 index daily 依赖从 `csi_a500_index_daily.csv` 改为 `zz500_index_daily.csv`
  - 将 `code/configs/formal_zz500.yaml` 与 `code/configs/formal_zz500_extended.yaml` 的 `benchmark_path` 同步改为 `../data/formal/index_daily/zz500_index_daily.csv`
- 修复 quantile 空桶与 long-short 空头腿错误：
  - 在 `code/stock_tensor/evaluation.py` 中移除“补空桶到 `quantile_count`”的逻辑
  - `long_short` 现在严格使用首个和最后一个非空分位，不再引用伪造空桶
- 补强 AC2 回归测试：
  - `code/tests/test_pipeline.py` 现在锁定 `quantile_count > pool_size` 场景下，最大分位数等于实际非空桶数，且 `short_quantile` 不得引用空桶
  - `code/tests/test_config_profiles.py` 与 `code/tests/test_formal_config.py` 现在锁定 ZZ500 benchmark 身份必须对应 `000905.SH`
  - `code/tests/test_refresh_formal_factor_panels.py` 已同步改用 `zz500_index_daily.csv`
- 重跑受影响的 ZZ500 两组 committed formal 输出：
  - `formal_zz500_run`
  - `formal_zz500_extended_run`
- 回写论文：
  - `paper_body.tex` 中关于 extended ZZ500 相对基准超额净值的表述，已从旧 benchmark 下的 5.04\% 修正为当前真实值 3.86\%

## Files Changed

- `code/data/import_tdx_vipdoc.py`
- `code/data/formal/index_daily/zz500_index_daily.csv`
- `code/data/refresh_formal_factor_panels.py`
- `code/configs/formal_zz500.yaml`
- `code/configs/formal_zz500_extended.yaml`
- `code/stock_tensor/evaluation.py`
- `code/tests/test_pipeline.py`
- `code/tests/test_config_profiles.py`
- `code/tests/test_formal_config.py`
- `code/tests/test_refresh_formal_factor_panels.py`
- `code/data/formal/factors/README.md`
- `paper_body.tex`
- `code/outputs/formal_zz500_run/*`
- `code/outputs/formal_zz500_extended_run/*`
- `.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md`
- `.humanize/rlcr/2026-04-26_14-59-46/round-8-summary.md`

## Validation

以下验证均在当前 Windows 主机 PowerShell 环境中执行：

- `python -m unittest discover -s code/tests -p test_pipeline.py`：通过
- `python -m unittest discover -s code/tests -p test_formal_config.py`：通过
- `python -m unittest discover -s code/tests -p test_config_profiles.py`：通过
- `python -m unittest discover -s code/tests -p test_refresh_formal_factor_panels.py`：通过
- `python code/main.py --config code/configs/formal_zz500.yaml`：通过
- `python code/main.py --config code/configs/formal_zz500_extended.yaml`：通过

额外核实：

- `code/data/formal/index_daily/zz500_index_daily.csv` 的 `stock_code` 现为 `000905.SH`
- `formal_zz500_run/excess_returns_*.json` 与 `formal_zz500_extended_run/excess_returns_*.json` 已按真实 ZZ500 benchmark 重算
- `quantile_count > pool_size` 的 smoke 场景下，`long_short_*.json` 的 `short_quantile` 现在等于最后一个非空分位

## Remaining Items

- AC1：第一版完整扩展输入合同已落地，但更完整宏观变量与更广泛事件字典仍未完成
- AC2：分位数组、多空、成本和超额收益基础合同已完成，但更长窗口稳健性检验与更系统暴露比较仍未完成
- AC3：全 A / 行业分层 / 市值分层实验仍未落地
- AC4：股票潜在结构图、行业聚类图和样本边界对比图仍未完成
- AC5：参考文献条目级元数据补齐与最终格式统一仍未完成
- 仓库验证入口说明仍需继续统一，避免 WSL/Windows 解释器差异造成误解

## Goal Tracker Update Request

### Requested Changes:
- 更新 Open Issues 中关于 AC2 的描述，移除“分位数组/交易成本/超额收益仍未完成”的过时表述，改为“这些基础合同已完成，但更长窗口稳健性检验与更系统暴露比较仍未完成”
- 在 Plan Evolution Log 中记录：Round 8 修复了 ZZ500 benchmark miswire 和 quantile 空桶合同缺陷
- 在 AC2 相关任务备注中补充：ZZ500 超额收益现已绑定真实 `000905.SH` benchmark，long-short 不再引用空桶

### Justification:
Round 8 的核心工作不是增加新功能点，而是修复 Round 7 review 发现的两条 AC2 合同缺陷。当前 committed outputs 中的 ZZ500 超额收益和 quantile/long-short 逻辑已经从“存在但不可靠”推进到“基础合同正确”。Tracker 需要同步这一点，否则后续 review 会继续沿用已经失效的 blocker。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes:
  - 已按流程读取 `.humanize/bitlesson.md`
  - `bitlesson-select.sh` 仍因本地 selector 流式请求断开不可用，且当前知识库无有效条目，因此本轮继续按 `NONE` 执行
