# Round 9 Summary

## Work Completed

- 按 Round 8 review 的 AC2 directive，补齐 benchmark / manifest / quantile 三类回归保护：
  - `code/tests/test_config_profiles.py`
    - 为 `formal_zz500_extended.yaml` 增加 benchmark path 与 `000905.SH` 身份断言
  - `code/tests/test_formal_config.py`
    - 新增 `formal_zz500_extended.yaml` 的运行测试
    - 锁定 `run_manifest.json` 与 `config_snapshot.yaml` 中 benchmark path 为 `zz500_index_daily.csv`
  - `code/tests/test_pipeline.py`
    - 锁定 `run_manifest.evaluation.benchmark_path` 在无 benchmark 场景下显式为 `None`
    - 锁定 `quantile_count > pool_size` 时 `short_quantile` 必须等于最后一个非空分位
    - 锁定 `excess_returns_*` 与 `group_returns_*` 日期严格对齐
    - 锁定无 benchmark 的 smoke 场景下 `benchmark_return == 0.0`
- 把 ZZ500 benchmark 的可重建流程收口到 tracked workflow：
  - 新增受版本控制脚本 `code/data/build_tdx_named_index_files.py`
  - 该脚本直接从 TongDaXin `.day` 文件生成：
    - `hs300_index_daily.csv`
    - `000050_index_daily.csv`
    - `csi_a500_index_daily.csv`
    - `zz500_index_daily.csv`
  - 更新 `code/data/formal/README.md`，不再要求依赖 ignored 的本地 importer 来重建 named index daily 文件
- 保持 Round 8 已修复的 ZZ500 benchmark contract 不回退：
  - `zz500_index_daily.csv` 当前 `stock_code` 为 `000905.SH`
  - `formal_zz500.yaml` 与 `formal_zz500_extended.yaml` 当前 benchmark path 均指向 `zz500_index_daily.csv`

## Files Changed

- `code/data/build_tdx_named_index_files.py`
- `code/data/formal/README.md`
- `code/tests/test_config_profiles.py`
- `code/tests/test_formal_config.py`
- `code/tests/test_pipeline.py`
- `.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md`
- `.humanize/rlcr/2026-04-26_14-59-46/round-9-summary.md`

## Validation

以下验证均在当前 Windows 主机 PowerShell 环境中执行：

- `python -m unittest discover -s code/tests -p test_pipeline.py`：通过
- `python -m unittest discover -s code/tests -p test_formal_config.py`：通过
- `python -m unittest discover -s code/tests -p test_config_profiles.py`：通过

额外核实：

- `code/data/formal/index_daily/zz500_index_daily.csv` 的 `stock_code` 为 `000905.SH`
- `formal_zz500_extended_run/run_manifest.json` 的 `evaluation.benchmark_path` 为 `code/data/formal/index_daily/zz500_index_daily.csv`
- smoke 场景下 `run_manifest.evaluation.benchmark_path` 显式为 `null`

## Remaining Items

- AC1：第一版完整扩展输入合同已落地，但更完整宏观变量与更广泛事件字典仍未完成
- AC2：分位数组、多空、成本和超额收益基础合同已完成，但更长窗口稳健性检验与更系统暴露比较仍未完成
- AC3：全 A / 行业分层 / 市值分层实验仍未落地
- AC4：股票潜在结构图、行业聚类图和样本边界对比图仍未完成
- AC5：参考文献条目级元数据补齐与最终格式统一仍未完成
- 仍需继续统一仓库验证入口说明，避免 WSL/Windows 解释器差异造成误解

## Goal Tracker Update Request

### Requested Changes:
- 在 AC2 相关 open issue 中删除“ZZ500 benchmark miswire / quantile 空桶仍未修复”的残留表述
- 在 Plan Evolution Log 中记录：Round 9 已把 benchmark 身份、manifest 契约和 quantile 小样本场景锁进测试
- 在 Open Issues 中保留“更长窗口稳健性检验与更系统暴露比较仍未完成”，但不要再把 benchmark 身份和空桶问题算作当前 blocker

### Justification:
Round 9 的工作不是增加新功能，而是把 Round 8 修好的 AC2 合同真正锁进测试与 tracked workflow。当前 ZZ500 benchmark 身份、extended benchmark manifest、smoke 无 benchmark 语义以及 `quantile_count > pool_size` 的 long-short 行为都已经有明确保护，tracker 需要反映这一点。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes:
  - 已按流程读取 `.humanize/bitlesson.md`
  - `bitlesson-select.sh` 仍因本地 selector 流式请求断开不可用，且当前知识库无有效条目，因此本轮继续按 `NONE` 执行
