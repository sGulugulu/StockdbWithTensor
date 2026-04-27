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

### Plan Version: 1 (Updated: Round 0)

#### Plan Evolution Log
<!-- Document any changes to the plan with justification -->
| Round | Change | Reason | Impact on AC |
|-------|--------|--------|--------------|
| 0 | Initial plan | 从 `论文不足与完善计划.md` 抽取目标、验收标准和任务清单 | 建立 AC1-AC6 的新一轮 RLCR 追踪锚点 |
| 0 | 将上一轮已提交成果作为当前基线 | 当前 base commit `5d20f4f` 已包含样本边界、模式发现图组和参考文献第一轮补齐 | 避免重复实现已完成内容，把后续焦点转向长窗口、AC1 残余和 AC2 暴露闭环 |

#### Active Tasks
<!-- Map each task to its target Acceptance Criterion and routing tag -->
| Task | Target AC | Status | Tag | Owner | Notes |
|------|-----------|--------|-----|-------|-------|
| 补齐更完整宏观变量与更广泛事件字典 | AC1 | pending | coding | claude | BitLesson=NONE；已有第一版市场代理、财务 PIT、业绩快报和业绩预告合同，仍需补宏观/事件扩展清单与边界说明 |
| 将新增输入边界与 PIT 可用时点规则回写第三章和局限性 | AC1 | pending | coding | claude | 依赖扩展字典更新 |
| 补充组合层系统暴露汇总和 Rank IC 联动分析 | AC2 | completed | coding | claude | Round 0 已新增 `summarize_boundary_portfolio.py`、`boundary_portfolio` 汇总和论文联动说明；长窗口仍另列任务 |
| 设计并提交长窗口稳健性实验入口 | AC2 | pending | coding | claude | 当前 run 仍为短窗口第一批结果，后续需扩展窗口或形成长窗口配置 |
| 扩展 AC3 分层实验的长窗口和更多边界复核 | AC3 | pending | coding | claude | 第一批全 A/行业/市值分层已落地，仍需长期稳健性 |
| 将 AC3 多样本边界结果整理为对比表 | AC3 | completed | coding | claude | Round 0 已生成 `code/data/formal/reports/boundary_portfolio/README.md` 和 JSON 汇总 |
| 将 AC4 图组整理成答辩展示页素材 | AC4 | pending | coding | claude | 已有 SVG 图组，仍需面向答辩的结果页说明或素材清单 |
| 完成参考文献学校格式最终校验 | AC5 | pending | coding | claude | 第一轮元数据已补齐，仍需标点、空格、DOI 展示规则和正文引用顺序校验 |
| 维护独立不足计划与 RLCR 记录 | AC6 | in_progress | coding | claude | 本轮继续维护 |

### Completed and Verified
<!-- Only move tasks here after Codex verification -->
| AC | Task | Completed Round | Verified Round | Evidence |
|----|------|-----------------|----------------|----------|
| AC3 | 第一批全 A、行业分层、市值分层配置和产物 | previous | 0 baseline | `code/configs/formal_all_a.yaml`、行业/市值配置、`code/data/formal/universes/segmented/*.csv`、`code/outputs/formal_all_a_run/*` 等已在 base commit |
| AC4 | 第一批股票潜在结构、行业聚类和跨样本边界图组 | previous | 0 baseline | `code/data/formal/reports/pattern_discovery/*.svg` 和 `pattern_discovery_summary.json` 已在 base commit |
| AC5 | 参考文献缺失元数据第一轮补齐 | previous | 0 baseline | `参考文献元数据核对清单.md` 与 `paper_body.tex` 已移除 `[Z]` 占位 |
| AC6 | 独立不足与完善计划文档 | previous | 0 baseline | `论文不足与完善计划.md` 已存在并作为本轮 plan_file |
| AC2 | 跨样本边界组合与暴露汇总 | 0 | pending verification | `code/data/summarize_boundary_portfolio.py`、`code/data/formal/reports/boundary_portfolio/README.md`、`boundary_portfolio_summary.json`、`paper_body.tex` |
| AC3 | 多样本边界结果对比表 | 0 | pending verification | `boundary_portfolio` 汇总覆盖 HS300、SZ50、ZZ500、全 A、行业分层和市值分层 |

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
| 当前实验多数为短窗口结果，长窗口稳定性不足 | 0 | AC2/AC3/AC4 | 新增长窗口配置或生成长窗口对比说明 |
| 参考文献最终学校格式规则尚未逐条校验 | 0 | AC5 | 在最终排版前统一检查标点、空格、载体类型和 DOI 展示 |
