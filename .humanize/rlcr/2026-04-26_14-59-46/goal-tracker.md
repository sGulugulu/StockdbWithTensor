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

### Plan Version: 5 (Updated: Round 3)

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

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| 建立扩展特征字典与 PIT 安全说明文档 | AC1 | pending | coding | claude | BitLesson=NONE；当前仅形成说明文档，未落地真实字典表、披露时点映射与样例 |
| 将训练输入边界说明回写到第三章与局限性分析 | AC1 | completed | coding | claude | BitLesson=NONE；已在数据来源与局限性部分补写 |
| 修正《训练输入扩展与 PIT 安全说明》中对正式窗口已统一的失实表述 | AC1 | completed | coding | claude | 已改为区分数据底座窗口、formal 因子面板窗口与当前 committed formal 输出窗口 |
| 将通过 PIT 校验的扩展特征接入统一训练接口并生成扩展版 factor panel | AC1 | pending | coding | claude | 需形成可运行扩展输入，而非停留在 future work 描述 |
| 重跑 HS300、SZ50、ZZ500 扩展前后对比实验 | AC1 | pending | coding | claude | 需产出 rank、解释方差、Rank IC、IR 等对比结果 |
| 修复 formal 因子面板与正式输出实际窗口仅覆盖 2026-03 的口径错位 | AC1 | pending | coding | claude | 当前 formal factor panel 已延伸到 2026-04-03，但正式输出仍停留在 2026-03-30；需统一数据、产物与论文口径 |
| 实现显式训练/验证/测试切分与 held-out 评估，并把 split 元数据写入产物 | AC2 | in_progress | coding | claude | `sample_run` 与三组 committed formal 输出已包含 split / preprocess 合同，Top-N 合同与 `stock` / `hybrid` 行业元数据缺陷已修复；但组合层评估、风险暴露与正文联动仍未实现 |
| 重跑 formal HS300、SZ50、ZZ500 以刷新 split / preprocess 产物并替换旧 manifest | AC2 | completed | coding | claude | 已验证 `code/outputs/formal_*_run/run_manifest.json` 含 split / preprocess 字段，旧版简化 manifest 已被替换 |
| 设计组合回测指标框架与产物清单 | AC2 | pending | coding | claude | BitLesson=NONE；下一轮补回测结果表与图 |
| 实现 Top-N/分组收益/回撤/风险暴露计算 | AC2 | pending | coding | claude | BitLesson=NONE；Top-N 裁剪已进入候选池合同，但组合收益、回撤、换手与风险暴露产物仍未实现 |
| 将组合层结果与 Rank IC 指标联动分析并回写第五章 | AC2 | pending | coding | claude | 原始计划明确要求判断排序指标与组合表现的一致性，当前 tracker 之前未单独追踪该项 |
| 设计全 A 股、行业分层、市值分层扩展实验路径 | AC3 | pending | coding | claude | BitLesson=NONE；先补样本边界说明，再落配置与脚本 |
| 落地全 A 股、行业分层、市值分层配置并生成运行产物 | AC3 | pending | coding | claude | 需形成真实实验结果，而非仅保留扩展路径说明 |
| 将样本边界扩展影响回写论文正文 | AC3 | pending | coding | claude | BitLesson=NONE；依赖扩展实验结果 |
| 设计模式发现增强图组清单 | AC4 | pending | coding | claude | BitLesson=NONE；热力图、阶段切换图、聚类图仍待实现 |
| 实现模式发现增强图与图文解释 | AC4 | pending | coding | claude | BitLesson=NONE；需改 output 与正文章节 |
| 用真实产物重写模式发现章节，删除不存在图表与超窗口时间状态结论 | AC4 | pending | coding | claude | 当前正文仍写入“模型指标总览图/时间状态变化图/因子热力图”以及 2024/2025 跳变结论，但 committed outputs 无对应证据 |
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

### Explicitly Deferred
<!-- Items here require strong justification -->
| Task | Original AC | Deferred Since | Justification | When to Reconsider |
|------|-------------|----------------|---------------|-------------------|

### Open Issues
<!-- Issues discovered during implementation -->
| Issue | Discovered Round | Blocking AC | Resolution Path |
|-------|-----------------|-------------|-----------------|
| 参考文献中若干 PDF 条目仍缺少完整出版元数据，当前只能先形成核对清单 | 0 | AC5 | 后续逐篇提取首页信息并统一重排参考文献格式 |
| 当前回测逻辑尚未进入 `code/stock_tensor`，组合层评估仍停留在计划阶段 | 0 | AC2 | 下一轮优先下钻 evaluation 与 output 链路 |
| 样本边界扩展尚无全 A/行业/市值分层配置与运行产物 | 0 | AC3 | 下一轮补样本派生脚本和配置 |
| formal 因子面板与正式输出的时间窗口口径仍不一致：factor panel 已到 2026-04-03，而 formal 输出仍停留在 2026-03-30 | 1 | AC1 | 统一 factor panel、formal 产物与论文叙事中的窗口口径，并在真正扩展或收缩窗口后同步刷新证据链 |
| formal manifest 已刷新，但正文仍引用不存在的模型指标总览图/时间状态变化图/因子热力图，并将仅覆盖 2026-03 的 time regimes 结果写成 2024/2025 跳变分析 | 3 | AC2, AC4 | 先用真实 committed outputs 重写第五章相关段落，再补齐真正的增强图组与时间状态图产物 |
| `build_formal_factor_panel.py` 已产出 `turn_factor` 与 `ps_ttm` 列，但 formal 配置仍只消费 4 个主线因子，更不用说宏观/PIT/事件特征；扩展输入尚未进入训练接口 | 3 | AC1 | 先定义扩展特征字典与可用时点映射，再扩展 formal 配置、训练接口与对照实验 |
