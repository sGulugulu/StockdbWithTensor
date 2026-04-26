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
基于《论文不足与完善计划》，对论文当前版本中已经识别出的五类不足建立可执行的修复与扩展闭环，并在 RLCR 过程中逐步推进论文正文、实验验证、图表表达、样本边界与参考文献规范化等改进工作。

Source plan: 论文不足与完善计划.md

### Acceptance Criteria
<!-- Each criterion must be independently verifiable -->
<!-- Claude must extract or define these in Round 0 -->

1. 论文正文中对“训练输入仍以主线因子面板为核心”的不足有更完整、可执行的分析与后续扩展说明。
2. 论文正文中对“排序有效性分析尚未形成组合回测闭环”的不足有明确的完善路径，并能落为后续任务清单。
3. 论文正文中对“样本边界仍局限于三个指数样本池”的不足有可验证的扩展计划与预期产出说明。
4. 论文正文中对“模式发现图表展开不充分”的不足有明确的图表增强方案，并在独立文档中形成记录。
5. 论文正文中对“参考文献元数据与正文联动仍需规范化”的不足有明确的核对与修订方案，并在独立文档中形成记录。
6. 形成一份独立的不足与完善计划文档，逐项记录问题表现、原因、影响、完善步骤和预期产出。

---

## MUTABLE SECTION
<!-- Update each round with justification for changes -->

### Plan Version: 14 (Updated: Round 7 Review)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | - | - |
| 0 | 将五类不足拆细为可执行子任务，并补充开放问题记录 | 首轮评审指出任务粒度过粗，无法约束执行 | 提高 AC1-AC5 的可验证性 |
| 1 | 拒绝将 AC1 的“扩展特征字典”任务按完成处理，并补入 split 协议、正式窗口一致性与扩展实验遗漏任务 | Round 1 评审发现当前仅有说明性文档，且论文、代码、输出之间存在明显口径错位 | 防止 AC1-AC4 在失实前提下继续推进 |
| 1 | 将 AC6 标记为已验证完成 | 独立不足计划文档及两份配套说明文档已存在且可核实 | AC6 达成 |
| 2 | 确认 split / held-out 主链路已在代码与 smoke 产物中落地，但保留 formal 产物刷新、Top-N 合同生效与 stock/hybrid 修复为活动任务 | Round 2 评审验证了 `sample_run` 新 manifest 合同，同时发现 formal 输出仍是旧产物，且新实现存在配置失效与元数据丢失问题 | 防止 AC2 被过早判定为完成，并补齐后续实现边界 |
| 3 | 部分批准 Round 3 的 tracker 更新请求：确认 formal manifest 已刷新、Top-N 与 stock/hybrid 行业元数据缺陷已修复，但新增正文失实表述修正与组合层联动分析遗漏任务 | Round 3 评审验证了局部代码修复和 formal 产物刷新，同时确认原始计划主体仍未完成，且论文继续引用不存在的图表与超窗口结论 | 防止 AC1-AC5 因局部修复而掩盖剩余主体交付 |
| 4 | 批准将 AC1/AC4 的局部真实进展更新为 `in_progress`，并新增“baseline/extended 对照结果回写论文”任务 | Round 4 评审验证了增强图组已真实落盘、第一版 extended 配置与输出已生成，但正文图表数值和章节叙事仍未完全按当前产物收口 | 让 tracker 反映真实推进，同时避免把局部产物误记为 AC 完成 |
| 4 | 修正 AC4 收口备注与 Open Issue，删除已失效的“手工数值仍未更新”表述 | 本轮审计核实 `paper_body.tex` 中解释方差、Rank IC 与滚动稳定性三张 PGFPlots 已与当前 committed `metrics.json` 对齐 | 防止 tracker 继续记录已解决问题，并把注意力收束到 AC4 真正剩余的图系缺口 |
| 4 | 批准将 AC2 的组合层闭环进展提升为“结构化产物已落盘”，并补入“分组收益图/回撤图仍缺失”为开放问题 | 本轮审计核实 `evaluation.py` / `output.py` 已生成 `portfolio_metrics`、`group_returns`、`drawdown`、`exposure` 产物，且第五章已有初版 Rank IC 联动分析；但原始计划要求的图形化结果仍未完成 | 让 tracker 同时反映真实推进与未收口缺口 |
| 4 | 新增 formal factor panel 统一刷新入口，并将 committed factor panel、formal profile 与六组正式输出统一到 `2026-03-30` | 本轮已验证 baseline/extended 六个 factor panel 最大 `trade_date` 均为 `2026-03-30`，六组 formal 输出的 `requested_end_date` 与 `actual_end_date` 也都为 `2026-03-30` | 收口 AC1 的窗口错位，并把 extended panel 纳入统一刷新入口 |
| 4 | 新增 formal 标签退化与论文数值失配修复任务 | Round 4 复审发现 `build_formal_factor_panel.py` 在 `max_trade_date` 截断后再计算 `future_return`，使当前 formal 测试窗口标签全为 0；同时 `paper_body.tex` 与 `扩展特征对照实验结果.md` 仍引用旧数值 | 防止 AC1/AC2 因“产物存在”而掩盖数值失真与正文失实问题 |
| 4 | 修复 formal 标签退化并按 committed outputs 回填正文与对照文档 | 已改为先按股票全量 K 线计算动量和未来收益，再在输出阶段按 universe history 与 `max_trade_date` 过滤；六组 formal 输出重新生成后不再是平线，论文正文与对照文档也已按新结果同步 | 恢复 AC2 组合层证据的数值有效性，并消除 AC1/AC2 的文稿失配 |
| 5 | 接受 Round 5 的 tracker update request，但保持 AC1-AC5 主体未完成状态 | 本轮复核确认 formal 标签退化修复属实，`paper_body.tex` 与 `扩展特征对照实验结果.md` 的核心数值也已和 committed outputs 对齐；但原始计划的大部分扩展任务仍处于未完成状态 | 允许清除已解决 blocker，同时防止把局部修复误判为全计划完成 |
| 5 | 新增验证命令契约失配 open issue | 当前仓库环境中 `python` 仍指向 2.7，`python3` 运行测试缺少 `PyYAML` 依赖，且本机无 `latexmk` / `xelatex`，导致 Round 5 Validation 无法按文档命令直接复现 | 需要在后续收口中同步修正文档和验证入口，避免 AC 进展无法复核 |
| 6 | 接受 Round 6 的 tracker update request，并把 AC1 进展从“局部 PIT/快报接入”更新为“第一版完整扩展输入合同” | 本轮复核确认 extended panel、formal extended 配置、合同文档与对照说明已真实覆盖市场代理变量、财务 PIT、业绩快报和业绩预告四类输入；但更完整宏观变量与更广泛事件字典仍未完成 | 让 tracker 反映 AC1 的真实推进，同时保持 AC1-AC5 主体任务未完成的审计结论 |
| 7 | 部分接受 Round 7 的 tracker update request，并把 AC2 进展更新为“分位数组/多空/成本/超额收益第一版合同已落盘” | 本轮复核确认六组 formal / extended 输出已真实新增 `quantile_returns_*`、`long_short_*`、`cost_adjusted_*`、`excess_returns_*` 与对应 SVG，`paper_body.tex` 也已吸收新证据；但同时发现 ZZ500 基准指数接错到 `000510.SH`，且 `quantile_count > pool_size` 时会生成伪造空分位并污染多空腿 | 让 tracker 记录 AC2 的真实推进，同时把新增 blocker 显式暴露出来，避免把第一版合同误记为稳定完成 |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| 建立扩展特征字典与 PIT 安全说明文档 | AC1 | in_progress | coding | claude | BitLesson=NONE；`EXTENDED_FACTOR_CONTRACT.md` 已覆盖第一版市场代理变量、财务 PIT、业绩快报和业绩预告字段、披露时点与缺失处理，但更完整宏观变量与更广泛事件字典仍待补齐 |
| 将训练输入边界说明回写到第三章与局限性分析 | AC1 | completed | coding | claude | BitLesson=NONE；已在数据来源与局限性部分补写 |
| 修正《训练输入扩展与 PIT 安全说明》中对正式窗口已统一的失实表述 | AC1 | completed | coding | claude | 已改为区分数据底座窗口、formal 因子面板窗口与当前 committed formal 输出窗口 |
| 将通过 PIT 校验的扩展特征接入统一训练接口并生成扩展版 factor panel | AC1 | in_progress | coding | claude | 已接入市场代理变量、财务 PIT、业绩快报和业绩预告四类第一版特征，三组 extended 配置与输出已生成；`refresh_formal_factor_panels.py` 已把 baseline/extended panel 收口到统一刷新入口，但更完整宏观变量与更广泛事件字典仍未接入 |
| 将 baseline/extended 对照结果回写第三章与局限性分析 | AC1 | in_progress | coding | claude | `paper_body.tex` 与 `扩展特征对照实验结果.md` 已按当前 committed `metrics.json` / `portfolio_metrics.json` 回填核心数值，但第三章数据边界说明和更多 extended 细节仍可继续补充 |
| 修复 formal 因子面板与正式输出实际窗口仅覆盖 2026-03 的口径错位 | AC1 | completed | coding | claude | 已重建六个 baseline/extended factor panel 到 `2026-03-30`，六组 formal 输出的 `requested_end_date` 与 `actual_end_date` 也都统一为 `2026-03-30` |
| 实现显式训练/验证/测试切分与 held-out 评估，并把 split 元数据写入产物 | AC2 | in_progress | coding | claude | `sample_run` 与三组 committed formal 输出已包含 split / preprocess 合同，Top-N 合同与 `stock` / `hybrid` 行业元数据缺陷已修复；组合层基础图形化产物已落盘，但分位数组、交易成本和更完整暴露分析仍未实现 |
| 重跑 formal HS300、SZ50、ZZ500 以刷新 split / preprocess 产物并替换旧 manifest | AC2 | completed | coding | claude | 已验证 `code/outputs/formal_*_run/run_manifest.json` 含 split / preprocess 字段，旧版简化 manifest 已被替换 |
| 修复 factor panel 截断后测试窗口 future_return 全为 0 的标签退化 | AC2 | completed | coding | claude | 已改为先基于股票全量 K 线计算未来收益和动量，再在输出阶段按成分历史和 `max_trade_date` 过滤；`test_formal_factor_panel.py`、`test_refresh_formal_factor_panels.py` 与 `test_formal_config.py` 已覆盖这一回归路径 |
| 实现 Top-N/分组收益/回撤/风险暴露计算 | AC2 | in_progress | coding | claude | `portfolio_metrics`、`group_returns`、`drawdown`、`exposure` 之外，`quantile_returns_*`、`long_short_*`、`cost_adjusted_*`、`excess_returns_*` 与三张 overview SVG 也已在六组 formal / extended 输出目录落盘；但 ZZ500 超额收益当前误用 `000510.SH` 基准，`quantile_count > pool_size` 时会生成空分位，多空腿与更系统暴露比较仍未收口 |
| 将组合层结果与 Rank IC 指标联动分析并回写第五章 | AC2 | in_progress | coding | claude | 第五章已吸收新的多空、成本后净值和超额收益证据；但 `paper_body.tex` 中涉及 ZZ500 相对基准表述需在基准修正后重算，且仍缺更长窗口稳健性检验与更系统暴露章节 |
| 设计全 A 股、行业分层、市值分层扩展实验路径 | AC3 | pending | coding | claude | BitLesson=NONE；先补样本边界说明，再落配置与脚本 |
| 落地全 A 股、行业分层、市值分层配置并生成运行产物 | AC3 | pending | coding | claude | 需形成真实实验结果，而非仅保留扩展路径说明 |
| 将样本边界扩展影响回写论文正文 | AC3 | pending | coding | claude | BitLesson=NONE；依赖扩展实验结果 |
| 设计模式发现增强图组清单 | AC4 | pending | coding | claude | BitLesson=NONE；热力图、阶段切换图、聚类图仍待实现 |
| 实现模式发现增强图与图文解释 | AC4 | in_progress | coding | claude | 增强图组已落地到 formal 输出目录，时间状态描述已开始按真实产物修正；但股票潜在结构图、样本边界对比图和章节联动仍待补齐 |
| 用真实产物重写模式发现章节，删除不存在图表与超窗口时间状态结论 | AC4 | in_progress | coding | claude | 2024/2025 跳变表述已删除，解释方差、Rank IC 与稳定性图表数值已按当前 committed outputs 收口；但股票潜在结构图、样本边界对比图与章节联动仍未完成 |
| 建立参考文献元数据核对清单 | AC5 | completed | coding | claude | BitLesson=NONE；已新增独立核对清单 |
| 将参考文献规范化方案回写正文 | AC5 | completed | coding | claude | BitLesson=NONE；已在第六章不足分析中回写 |
| 逐条补齐参考文献缺失元数据 | AC5 | pending | coding | claude | BitLesson=NONE；当前 open issue 为若干 PDF 元数据待提取 |
| 统一参考文献格式并复核正文引用—条目对照表 | AC5 | pending | coding | claude | 原始计划除补元数据外，还要求统一学校格式并避免漏引、错引 |
| 维护并扩展独立不足记录文档 | AC6 | completed | coding | claude | 已创建并扩展《论文不足与完善计划》及两份配套文档 |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|
| AC6 | 维护并扩展独立不足记录文档 | 0 | 1 | 已维护 `论文不足与完善计划.md` 并新增 `训练输入扩展与PIT安全说明.md`、`参考文献元数据核对清单.md` |
| AC1 | 重跑 HS300、SZ50、ZZ500 扩展前后对比实验 | 4 | 4 | 已核实 `formal_hs300_extended_run`、`formal_sz50_extended_run`、`formal_zz500_extended_run` 均存在 `run_manifest.json` 与 `metrics.json`，并新增 `扩展特征对照实验结果.md` |
| AC2 | 设计组合回测指标框架与产物清单 | 4 | 4 | 已核实 `output.py` 会落盘 `portfolio_metrics.*`、`group_returns_*.*`、`drawdown_*.*`、`exposure_*.*`，六个 formal / extended 输出目录均已有对应产物 |
| AC1 | 统一 committed factor panel、formal profile 与正式输出窗口 | 4 | 4 | 已核实六个 baseline/extended factor panel 最大 `trade_date` 为 `2026-03-30`，六组 formal 输出 `run_manifest.json` 的 `requested_end_date` / `actual_end_date` 也均为 `2026-03-30` |
| AC2 | 修复 formal factor panel 截断导致的组合层平线退化 | 4 | 4 | 已核实三组 baseline factor panel 在 `2026-03-25` 至 `2026-03-30` 仍保留大量非零 `future_return`，`test_formal_config.py` 生成的 `portfolio_metrics.json` 也不再是全零平线 |

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|

### Open Issues
<!-- Issues discovered during implementation -->
| Issue | Discovered Round | Blocking AC | Resolution Path |
|-------|-----------------|-------------|-----------------|
| 参考文献中若干 PDF 条目仍缺少完整出版元数据，当前只能先形成核对清单 | 0 | AC5 | 后续逐篇提取首页信息并统一重排参考文献格式 |
| 样本边界扩展尚无全 A/行业/市值分层配置与运行产物 | 0 | AC3 | 下一轮补样本派生脚本和配置 |
| 增强图组与基础图文已落盘，但股票潜在结构图、样本边界对比图和更完整的模式发现章节联动仍未完成 | 4 | AC4 | 继续补股票潜在结构/行业聚类图、样本边界对比图，并把章节叙事扩展到完整图系 |
| 扩展特征已扩展到市场代理变量 + 财务 PIT + 业绩快报 + 业绩预告；baseline/extended 对照在不同样本池表现分化明显，仍需继续补更完整宏观变量与更广泛事件字典 | 4 | AC1 | 保持统一刷新入口不变，在此基础上继续扩展特征合同、筛选规则与样本池比较 |
| 分位数组、交易成本和超额收益基础合同已落地，但 ZZ500 当前误用 `000510.SH` 基准，且更长窗口稳健性检验与更系统暴露比较仍未完成 | 7 | AC2 | 先修正 ZZ500 benchmark contract、补 quantile 小样本回归测试并重跑受影响产物，再继续扩展暴露与稳健性章节 |
| `quantile_count` 当前在股票池小于分位数时会补空桶，并把空桶收益误作为多空空头腿 | 7 | AC2 | 修改 `build_portfolio_backtest` 只用非空分位构造 long-short，并补充 `quantile_count > pool_size` 的回归测试 |
| 仓库命令与当前环境解释器/依赖不一致：`python`=2.7，`python3` 默认环境缺 `PyYAML`，且本机无 `latexmk` / `xelatex`，Round 5 的验证命令无法直接复现 | 5 | ALL | 统一到 `python3` / `.venv` 入口，补齐依赖安装说明，并只保留可在仓库内复现的验证命令 |
