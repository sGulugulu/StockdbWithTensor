# Round 9 Summary

## Work Completed

- 按 Round 9 review 的 `STOP` directive，把本轮主线从 AC2 局部打磨切换到 AC3、AC4、AC5 主体交付：
  - AC3：新增全 A 活跃股票、行业分层和市值分层 formal 配置。
  - AC4：新增股票潜在结构图、cluster-vs-industry 图和跨样本边界 Tucker 对比图。
  - AC5：补齐参考文献缺失元数据，并把正文参考文献中的 `[Z]` 占位改为可核对载体类型。
- 新增 AC3 样本边界资产生成入口：
  - `code/data/build_segmented_formal_universes.py`
  - `code/data/refresh_segmented_formal_assets.py`
  - 输出并纳入版本控制：
    - `code/data/formal/universes/segmented/all_a_active_history.csv`
    - `code/data/formal/universes/segmented/industry_c27_history.csv`
    - `code/data/formal/universes/segmented/industry_c35_history.csv`
    - `code/data/formal/universes/segmented/industry_c39_history.csv`
    - `code/data/formal/universes/segmented/size_small_history.csv`
    - `code/data/formal/universes/segmented/size_mid_history.csv`
    - `code/data/formal/universes/segmented/size_large_history.csv`
    - 对应 7 份 factor panel CSV
- 新增并运行第一批分层 formal 配置：
  - `formal_all_a.yaml`
  - `formal_industry_c27.yaml`
  - `formal_industry_c35.yaml`
  - `formal_industry_c39.yaml`
  - `formal_size_small.yaml`
  - `formal_size_mid.yaml`
  - `formal_size_large.yaml`
- 将至少一组全 A、一组行业、一组市值 run 的关键输出纳入版本控制：
  - `code/outputs/formal_all_a_run/{run_manifest.json,metrics.json,portfolio_metrics.json,summary.md}`
  - `code/outputs/formal_industry_c27_run/{run_manifest.json,metrics.json,portfolio_metrics.json,summary.md}`
  - `code/outputs/formal_size_large_run/{run_manifest.json,metrics.json,portfolio_metrics.json,summary.md}`
- 新增 AC4 图组生成入口：
  - `code/data/build_pattern_discovery_assets.py`
  - `code/data/formal/reports/pattern_discovery/stock_latent_structure_formal_all_a_run_tucker.svg`
  - `code/data/formal/reports/pattern_discovery/cluster_vs_industry_formal_all_a_run_tucker.svg`
  - `code/data/formal/reports/pattern_discovery/boundary_comparison_tucker.svg`
  - `code/data/formal/reports/pattern_discovery/pattern_discovery_summary.json`
- 更新论文正文：
  - 新增“样本边界扩展探索”章节，写入全 A、行业分层、市值分层结果。
  - 在模式发现章节补入股票潜在结构图和行业聚类交叉图说明。
  - 将局限性从“仍未扩展样本边界/参考文献仍待逐条核对”修正为“第一批扩展已落地，但仍需长窗口与最终格式校验”。
- 更新 `参考文献元数据核对清单.md` 与 `paper_body.tex`：
  - 补齐夏虹、曾亚丽、Brandi、Spelta、刘宇轩、Lettau、Han、Wang 等条目。
  - 将正文参考文献中的 `[Z]` 占位统一替换为 `[J]`、`[D]`、`[R]` 或 `[EB/OL]`。

## Files Changed

- `.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md`
- `.humanize/rlcr/2026-04-26_14-59-46/round-9-summary.md`
- `code/configs/formal_all_a.yaml`
- `code/configs/formal_industry_c27.yaml`
- `code/configs/formal_industry_c35.yaml`
- `code/configs/formal_industry_c39.yaml`
- `code/configs/formal_size_large.yaml`
- `code/configs/formal_size_mid.yaml`
- `code/configs/formal_size_small.yaml`
- `code/data/build_segmented_formal_universes.py`
- `code/data/refresh_segmented_formal_assets.py`
- `code/data/build_pattern_discovery_assets.py`
- `code/data/formal/README.md`
- `code/data/formal/universes/segmented/*.csv`
- `code/data/formal/factors/*_factor_panel.csv`
- `code/data/formal/reports/pattern_discovery/*`
- `code/outputs/formal_all_a_run/{run_manifest.json,metrics.json,portfolio_metrics.json,summary.md}`
- `code/outputs/formal_industry_c27_run/{run_manifest.json,metrics.json,portfolio_metrics.json,summary.md}`
- `code/outputs/formal_size_large_run/{run_manifest.json,metrics.json,portfolio_metrics.json,summary.md}`
- `code/tests/test_config_profiles.py`
- `code/tests/test_segmented_formal_assets.py`
- `code/tests/test_pattern_discovery_assets.py`
- `paper_body.tex`
- `参考文献元数据核对清单.md`

## Validation

以下验证均在当前 Windows 主机 PowerShell 环境中执行：

- `python code/data/refresh_segmented_formal_assets.py --formal-root code/data/formal --max-trade-date 2026-03-30`：通过
- `python code/main.py --config code/configs/formal_all_a.yaml`：通过
- `python code/main.py --config code/configs/formal_industry_c27.yaml`：通过
- `python code/main.py --config code/configs/formal_size_large.yaml`：通过
- `python code/main.py --config code/configs/formal_industry_c39.yaml`：通过
- `python code/main.py --config code/configs/formal_industry_c35.yaml`：通过
- `python code/main.py --config code/configs/formal_size_small.yaml`：通过
- `python code/main.py --config code/configs/formal_size_mid.yaml`：通过
- `python code/data/build_pattern_discovery_assets.py ... --output-dir code/data/formal/reports/pattern_discovery --model-name tucker --max-stocks 60`：通过
- `python -m unittest discover -s code/tests -p 'test_segmented_formal_assets.py'`：通过
- `python -m unittest discover -s code/tests -p 'test_pattern_discovery_assets.py'`：通过
- `python -m unittest discover -s code/tests -p 'test_config_profiles.py'`：通过
- `python -m unittest discover -s code/tests -p 'test_formal_config.py'`：通过
- `python -m unittest discover -s code/tests -p 'test_[d-z]*.py' -v`：通过，39 个测试通过

全量 `python -m unittest discover -s code/tests -v` 在当前环境中会在 `test_convert_formal_csv_to_parquet_writes_output` 后无失败摘要地以非零退出；该测试单独执行通过，后半段测试集合也通过。当前判断为本机依赖组合或解释器进程级退出问题，不是本轮新增 AC3/AC4/AC5 代码路径失败。

## Remaining Items

- AC1：第一版扩展输入合同已落地，但更完整宏观变量与更广泛事件字典仍未完成。
- AC2：基础组合合同已完成并有测试保护，但更长窗口稳健性检验、交易冲击和系统暴露比较仍未完成。
- AC3：第一批全 A、行业、市值分层 run 已落地；剩余问题是长窗口和更多行业/市值边界的稳健性扩展。
- AC4：股票潜在结构图、行业交叉图、跨样本边界对比图已落地；剩余问题是答辩展示页和长窗口图组。
- AC5：参考文献元数据已完成第一轮补齐；剩余问题是最终学校格式细节、DOI 展示与标点空格校验。
- 环境入口：`.venv/bin/python` 在当前 PowerShell 中表现为 0 字节 reparse point，实际可复现入口是 `python`。`python3` 仍缺 `PyYAML`。

## Goal Tracker Update Request

### Requested Changes:

- 将 AC3 的“设计全 A 股、行业分层、市值分层扩展实验路径”标记为 completed，证据为新增分层生成脚本、7 份配置、7 份 factor panel 和论文“样本边界扩展探索”章节。
- 将 AC3 的“落地全 A 股、行业分层、市值分层配置并生成运行产物”标记为 in_progress 或部分完成，证据为全 A、C27 行业、大市值三个 run 的关键输出已纳入版本控制，同时其余分层 run 已在本地重跑并进入对比图。
- 将 AC3 的“将样本边界扩展影响回写论文正文”标记为 in_progress，证据为 `paper_body.tex` 已写入全 A、行业、市值分层结果，但仍需要长窗口补强。
- 将 AC4 的“设计模式发现增强图组清单”标记为 completed，证据为 `pattern_discovery/README.md` 与 `pattern_discovery_summary.json` 已列出三类图组。
- 将 AC4 的“实现模式发现增强图与图文解释”推进为 in_progress，证据为股票潜在结构图、cluster-vs-industry 图和跨样本边界对比图已落地并回写正文。
- 将 AC5 的“逐条补齐参考文献缺失元数据”标记为 completed，证据为 `参考文献元数据核对清单.md` 条目 6、10、11、12、14、15、16、17 已补齐。
- 将 AC5 的“统一参考文献格式并复核正文引用—条目对照表”标记为 in_progress，证据为 `paper_body.tex` 已移除 `[Z]` 占位，但最终学校模板细节仍需提交前校验。
- 更新 Open Issues：删除“样本边界扩展尚无全 A/行业/市值分层配置与运行产物”和“股票潜在结构图、样本边界对比图未落地”的旧表述，替换为“扩展结果仍需长窗口稳健性和答辩页收口”。

### Justification:

本轮已按 review 的 circuit breaker 要求，从 AC2 局部打磨切回 AC3、AC4、AC5 主体交付，并且同时提交了真实分层 run 证据、模式发现图产物和参考文献元数据补齐结果。Tracker 需要反映这些主体任务已经从 pending 进入可验证产物阶段，同时保留长窗口、答辩图组和最终格式校验等真实剩余风险。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes:
  - 已按流程读取 `.humanize/bitlesson.md`。
  - 当前 `.humanize/bitlesson.md` 没有已记录 lesson。
  - `bitlesson-selector` 命令在当前 PowerShell 环境中不可用，因此本轮按 `NONE` 执行并在这里记录。
