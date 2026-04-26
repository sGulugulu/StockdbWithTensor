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

### Plan Version: 2 (Updated: Round 0)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | - | - |
| 0 | 将五类不足拆细为可执行子任务，并补充开放问题记录 | 首轮评审指出任务粒度过粗，无法约束执行 | 提高 AC1-AC5 的可验证性 |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| 建立扩展特征字典与 PIT 安全说明文档 | AC1 | completed | coding | claude | BitLesson=NONE；已新增独立说明文档并回写正文 |
| 将训练输入边界说明回写到第三章与局限性分析 | AC1 | completed | coding | claude | BitLesson=NONE；已在数据来源与局限性部分补写 |
| 设计组合回测指标框架与产物清单 | AC2 | pending | coding | claude | BitLesson=NONE；下一轮补回测结果表与图 |
| 实现 Top-N/分组收益/回撤/风险暴露计算 | AC2 | pending | coding | claude | BitLesson=NONE；需改 evaluation/output |
| 设计全 A 股、行业分层、市值分层扩展实验路径 | AC3 | pending | coding | claude | BitLesson=NONE；先补样本边界说明，再落配置与脚本 |
| 将样本边界扩展影响回写论文正文 | AC3 | pending | coding | claude | BitLesson=NONE；依赖扩展实验结果 |
| 设计模式发现增强图组清单 | AC4 | pending | coding | claude | BitLesson=NONE；热力图、阶段切换图、聚类图仍待实现 |
| 实现模式发现增强图与图文解释 | AC4 | pending | coding | claude | BitLesson=NONE；需改 output 与正文章节 |
| 建立参考文献元数据核对清单 | AC5 | completed | coding | claude | BitLesson=NONE；已新增独立核对清单 |
| 将参考文献规范化方案回写正文 | AC5 | completed | coding | claude | BitLesson=NONE；已在第六章不足分析中回写 |
| 逐条补齐参考文献缺失元数据 | AC5 | pending | coding | claude | BitLesson=NONE；当前 open issue 为若干 PDF 元数据待提取 |
| 维护并扩展独立不足记录文档 | AC6 | completed | coding | claude | 已创建并扩展《论文不足与完善计划》及两份配套文档 |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|
| AC1 | 补全训练输入边界不足分析与扩展计划 | 0 | pending | `paper_body.tex` 增补训练输入边界说明；新增 `训练输入扩展与PIT安全说明.md` |
| AC5 | 补全参考文献元数据不足分析与规范化计划 | 0 | pending | `paper_body.tex` 增补参考文献规范化说明；新增 `参考文献元数据核对清单.md` |
| AC6 | 维护并扩展独立不足记录文档 | 0 | pending | 已维护 `论文不足与完善计划.md` 并新增两份配套说明文档 |

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
