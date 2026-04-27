# Goal Tracker

<!--
This file tracks the ultimate goal, acceptance criteria, and plan evolution.
It prevents goal drift by maintaining a persistent anchor across all rounds.

RULES:
- IMMUTABLE SECTION: Do not modify after initialization
- MUTABLE SECTION: Update each round, but document all changes
- Every task must be in one of: Active, Completed, or Deferred
- Deferred items require explicit justification
-->

## IMMUTABLE SECTION
<!-- Do not modify after initialization -->

### Ultimate Goal
基于《论文不足与完善计划》，继续把论文当前识别出的五类不足推进到可验证交付状态：补强训练输入边界、完善组合回测闭环、扩展样本边界、展开模式发现图系、规范参考文献元数据，并让论文正文、数据脚本、实验输出和配套文档保持一致。

Source plan: 论文不足与完善计划.md

### Acceptance Criteria
<!-- Each criterion must be independently verifiable -->

1. AC1：训练输入边界有完整的扩展特征字典、PIT 可用时点规则、统一训练接口说明，并在论文“数据来源与样本说明”“局限性分析”中保持一致。
2. AC2：排序有效性分析形成组合回测闭环，至少覆盖 Top-N、分组收益、多空、成本后收益、超额收益、回撤、换手率、年化波动、夏普比率、行业/风格暴露，并与 Rank IC 进行联动分析。
3. AC3：样本边界扩展到全 A、行业分层和市值分层，并有可复现配置、运行产物、对比表和论文正文回写。
4. AC4：模式发现图系覆盖因子重要性、时间状态切换、股票潜在结构、行业聚类关系和跨样本边界对比，并有图前图后文字解释。
5. AC5：参考文献元数据与正文引用链完成核对，参考文献条目按学校提交口径统一格式，避免漏引、错引和占位载体类型。
6. AC6：维护独立不足与完善计划，以及配套说明文档、RLCR 摘要和可复核验证记录。

---

## MUTABLE SECTION
<!-- Update each round with justification for changes -->

### Plan Version: 7 (Updated: Round 6)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | 从 `论文不足与完善计划.md` 抽取目标、验收标准和任务清单 | 建立 AC1-AC6 的新一轮 RLCR 追踪锚点 |
| 0 | 将上一轮已提交成果作为当前基线 | 当前 base commit `5d20f4f` 已包含样本边界、模式发现图组和参考文献第一轮补齐 | 避免重复实现已完成内容，把后续焦点转向长窗口、AC1 残余和 AC2 暴露闭环 |
| 1 | 将 AC1 第一阶段扩展输入、AC2 组合闭环汇总、AC3 对比表与 AC5 终稿校验移入已验证 | Round 1 已形成真实代码、产物和论文回写，且本轮复核确认这些交付物存在 | 缩小未完成范围到外部宏观/更广事件源、长窗口结果产物与长窗口图组 |
| 1 | 保持“长窗口稳健性实验入口”为进行中而非完成 | 虽然派生配置和一个相对路径运行验证已落地，但 `long_window_run_plan.json` / `README.md` 生成的命令仍使用不可直接执行的 `D:/...` 绝对路径 | AC3/AC4 仍不能以当前入口产物视为 fully reproducible |
| 2 | 将“长窗口稳健性实验入口”移入已验证 | Round 2 已把 `build_long_window_run_plan.py`、`long_window_run_plan.json` 和 `README.md` 修正为 repo-root 可直接执行的相对路径命令，并复核通过直接复制命令 | AC3 入口合同闭环完成，可将剩余精力集中到真实 long-window 结果与图组 |
| 2 | 将 AC3 / AC4 的 long-window 进度更新为“代表性窗口已完成、全年份仍未完成” | Round 2 新增 long-window 因子面板、2015/2020/2024/2026 四个代表性年份的 28 个本地 run 结果、组合汇总和长窗口素材，但未完成 2016/2017/2018/2019/2021/2022/2023/2025 的全年份复跑，也未提交被 `code/outputs/` 忽略的 run 目录 | AC3 / AC4 由入口阶段推进到代表性结果阶段，但仍不能视为 fully complete |
| 3 | 验证全年 long-window 产物与长窗口图组已入库，但保留 AC3 为进行中 | Round 3 的 84 个 `formal_*_long_window_run` 目录、`long_window_portfolio` 汇总和 `pattern_discovery_long_window_2015-2026` 图组均已存在且进入版本控制；但 `paper_body.tex` 仍保留“只复核 2015/2020/2024/2026”与“仍受短窗口限制”的旧表述 | AC4 可视为完成，AC3 仍需完成论文正文一致性回写后才能 fully close |
| 4 | 关闭 AC3 论文正文一致性缺口并收束 Active Tasks | Round 4 已将 `paper_body.tex` 改写为与 `2015-2026` 全年 long-window 产物一致，不再保留“仅代表年份复核”与“仍缺长窗口证据”的旧表述 | AC3 现已满足“配置、产物、对比表、论文回写”完整闭环，剩余主阻塞收敛为 AC1 |
| 5 | 拒绝将 AC1 移入已验证，并重新打开 AC3/AC1 的论文一致性收口任务 | Round 5 虽已落盘五张 canonical source tables 并把字段接入 extended panel，但复核发现 `refresh_formal_factor_panels.py` 的 clean-rebuild 自动构建链路仍会在缺失 baseline panel 时失败，且 `paper_body.tex` 仍残留过时的 extended 组合收益数字、AC1“尚未纳入更广泛宏观/事件源”的旧表述，以及 AC3“仅四个代表年份复核”的旧口径 | AC1 仍未 fully close，AC3 的论文正文一致性也再次出现回归，当前不能视为 COMPLETE |
| 6 | 部分接受 Round 6 的 tracker 更新请求：关闭 AC1 clean-rebuild 问题并验证 AC3/AC1 口径修复，但重新打开 AC2 论文正文一致性任务 | Round 6 复核确认 `refresh_formal_factor_panels.py` 已先生成 baseline panel 再触发 `build_formal_extended_sources()`，新增回归测试也已覆盖该顺序；`paper_body.tex` 中 AC1/AC3 的训练输入与 `2015-2026` long-window 口径已同步。但同一章的组合层段落仍把 extended ZZ500 的成本后净值和超额净值写成正收益，和 committed CSV 不一致 | AC1 与 AC3 可视为完成；AC2 的论文证据链出现残留不一致，当前仍不能视为 COMPLETE |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| 修正 AC2 论文正文中残留的组合层旧数字 | AC2 | pending | coding | claude | `paper_body.tex` 第 260 行仍把 extended ZZ500 的成本后净值和相对基准超额净值写成正收益，但 `formal_zz500_extended_run/cost_adjusted_{tucker,pca}.csv` 与 `excess_returns_{tucker,pca}.csv` 的最终 `cumulative_nav` 均低于 `1.0` |
| 维护独立不足计划与 RLCR 记录 | AC6 | in_progress | coding | claude | 本轮继续维护 |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|
| AC3 | 第一批全 A、行业分层、市值分层配置和产物 | previous | 0 baseline | `code/configs/formal_all_a.yaml`、行业/市值配置、`code/data/formal/universes/segmented/*.csv`、`code/outputs/formal_all_a_run/*` 等已在 base commit |
| AC4 | 第一批股票潜在结构、行业聚类和跨样本边界图组 | previous | 0 baseline | `code/data/formal/reports/pattern_discovery/*.svg` 和 `pattern_discovery_summary.json` 已在 base commit |
| AC5 | 参考文献缺失元数据第一轮补齐 | previous | 0 baseline | `参考文献元数据核对清单.md` 与 `paper_body.tex` 已移除 `[Z]` 占位 |
| AC6 | 独立不足与完善计划文档 | previous | 0 baseline | `论文不足与完善计划.md` 已存在并作为本轮 plan_file |
| AC1 | 第一阶段扩展输入统一训练接口与三组正式样本池复跑对照 | 1 | 1 | `code/data/build_extended_factor_panel.py`、三份 `formal_*_extended.yaml`、`扩展特征对照实验结果.md`、`code/outputs/formal_*_extended_run/*` |
| AC1 | 新增输入边界与 PIT 可用时点规则回写第三章和局限性 | 1 | 1 | `训练输入扩展与PIT安全说明.md`、`code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`、`paper_body.tex` 第三章/局限性更新 |
| AC1 | 修复 extended source clean-rebuild 自动构建合同 | 6 | 6 | `code/data/refresh_formal_factor_panels.py` 现先生成三份 baseline panel 再按需调用 `build_formal_extended_sources()`；`code/tests/test_refresh_formal_factor_panels.py` 新增 `build_extended_source_tables=True` 顺序回归测试；Round 6 复核下 targeted unittest 与 temp-root clean rebuild 调用均通过 |
| AC1 | 训练输入边界旧口径收口到当前 committed snapshot | 6 | 6 | `paper_body.tex` 已改写为“外部宏观、分红、重大事项和公告标题文本已接入训练接口；剩余缺口为更长历史、更完整宏观品种与公告正文全文”，与 `EXTENDED_FACTOR_CONTRACT.md` 和 `训练输入扩展与PIT安全说明.md` 一致 |
| AC2 | 跨样本边界组合与暴露汇总 | 1 | 1 | `code/data/summarize_boundary_portfolio.py` 已汇总 `metrics`、`portfolio_metrics`、`quantile_returns`、`long_short`、`cost_adjusted`、`excess_returns`、`exposure_*`，并刷新 `code/data/formal/reports/boundary_portfolio/*` 与 `paper_body.tex` |
| AC3 | 多样本边界结果对比表 | 1 | 1 | `code/data/formal/reports/boundary_portfolio/README.md` 与 `boundary_portfolio_summary.json` 覆盖 HS300、SZ50、ZZ500、全 A、行业分层和市值分层 |
| AC3 | 长窗口稳健性实验入口 | 2 | 2 | `code/data/build_long_window_run_plan.py` 现输出 repo-root 相对路径命令；`code/data/formal/reports/long_window_plan/README.md` / `long_window_run_plan.json` 可直接复制运行，且 `formal_all_a_2026_long_window_run.yaml` 已复核可执行 |
| AC3 | 全年 long-window 分层复跑产物与组合汇总入库 | 3 | 3 | `find code/outputs -maxdepth 1 -type d -name 'formal_*_long_window_run' | wc -l = 84`、`git ls-files 'code/outputs/formal_*_long_window_run/*' | wc -l = 7476`、`code/data/formal/reports/long_window_portfolio/README.md` 与 `boundary_portfolio_summary.json` 已覆盖 2015-2026 全部年度与 7 个边界 |
| AC3 | 长窗口样本边界扩展论文正文一致性回写 | 4 | 4 | `paper_body.tex` 已改写为“2015-2026 全年 long-window 复核”口径，相关段落见第 274、323、325、347 行附近；不再保留“仅 2015/2020/2024/2026”与“仍缺长窗口证据”的旧表述 |
| AC3 | 清理样本边界段落中残留的代表年份旧口径 | 6 | 6 | `paper_body.tex` 样本边界章节已改为“基于 long-window 因子面板对 2015--2026 全部年度做年度复核”；Round 6 复核 `rg -n "2015、2020、2024、2026|代表性市场窗口" paper_body.tex` 不再命中旧口径 |
| AC4 | 全年 long-window 模式发现图组与答辩素材包 | 3 | 3 | `code/data/formal/reports/pattern_discovery_long_window/README.md`、`pattern_discovery_long_window_2015` 至 `pattern_discovery_long_window_2026`、`code/data/formal/reports/defense_materials/long_window_assets/README.md` 已形成受版本控制的全年图组与素材入口 |
| AC5 | 参考文献学校格式最终校验 | 1 | 1 | `参考文献元数据核对清单.md` 最终校验结论 + `paper_body.tex` 结论章节已统一为当前学校提交口径 |

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|

### Open Issues
<!-- Issues discovered during implementation -->
| Issue | Discovered Round | Blocking AC | Resolution Path |
|-------|-----------------|-------------|-----------------|
| `bitlesson-selector` 命令在当前 PowerShell 环境不可用，且 `.humanize/bitlesson.md` 暂无条目 | 0 | ALL | 本轮按 `BitLesson=NONE` 执行，并在 summary 中记录 |
| Bash 与 Windows Git 的换行配置不一致会误报 CRLF 文件为 dirty | 0 | ALL | 已设置本地 `core.autocrlf=true`，后续验证使用同一 Git 视角 |
| `paper_body.tex` 仍残留组合层旧结果表述：第 260 行把 extended ZZ500 的成本后净值与相对基准超额净值写成正收益，但 `formal_zz500_extended_run/cost_adjusted_{tucker,pca}.csv` 与 `excess_returns_{tucker,pca}.csv` 的最终 `cumulative_nav` 均低于 `1.0` | 6 | AC2 | 以 `formal_zz500_extended_run/{cost_adjusted,excess_returns}_*.csv` 为唯一证据源重写该句，并顺手复核同段所有 baseline/extended 组合层数字，避免继续混用旧实验口径 |
