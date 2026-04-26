# Round 0 Review Result

## Findings

1. **阻断：Round 0 没有执行原始计划的主体工作，只完成了 loop 初始化与追踪文件搭建。**  
   原始计划要求围绕五类不足补论文、补实验、补图表、补样本边界和补参考文献规范化，且每类都给出了明确步骤与预期产出（`论文不足与完善计划.md:18-115`）。但 Claude 自己在总结中明确承认“五类不足的实体修复或扩展实现”尚未开始，参考文献核对、正文补写、图表扩展、样本边界扩展和组合回测闭环均“待后续轮次推进”（`.humanize/rlcr/2026-04-26_14-59-46/round-0-summary.md:33-36`）。这与“已完成本轮工作”的表述不一致，也不满足用户要求的“现在就完成全部计划项”。

2. **高危：`goal-tracker.md` 的 AC 被弱化成“分析/说明/任务清单”，没有绑定原始计划中的可交付产物。**  
   例如 AC1-AC5 只要求“更完整分析”“明确路径”“形成记录”等（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:26-31`），但原始计划要求的是扩展版因子面板、三大样本重跑结果、回测结果表、分组收益图、样本分层可视化、参考文献核对清单等实际产物（`论文不足与完善计划.md:18-115`）。按当前 AC 设计，即使不改代码、不补实验，也可能被误判为“达标”，这已经发生了目标漂移。

3. **高危：`goal-tracker.md` 没有把原始计划拆成可验证子任务，20 个原始执行步骤全部丢失。**  
   Tracker 当前只保留 5 个笼统 Active Task 和 1 个“独立文档已完成”项（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:46-55`），但原始计划对五类不足分别定义了 4 个执行步骤，总计 20 个动作项（`论文不足与完善计划.md:18-22`, `40-44`, `62-66`, `84-88`, `106-110`）。这些步骤没有进入 Active/Completed/Deferred 任一栏位，导致后续无法判断 Claude 究竟完成到哪一步。

4. **高危：组合回测闭环完全未实现，当前流水线只停留在 IC 类指标和候选股导出。**  
   `evaluation.py` 只计算 `mse`、`rmse`、`explained_variance`、`bic`、`ic_mean`、`rank_ic_mean`、`ir` 和 `rolling_stability`（`code/stock_tensor/evaluation.py:64-103`），没有任何 Top-N 收益、分组收益、换手率、最大回撤、年化波动、夏普或风格/行业暴露计算。`build_selection_records` 和 `build_candidate_pool` 只是把每个日期的分数落盘（`code/stock_tensor/evaluation.py:199-276`）；`pipeline.py` 也只是把这些记录写出去（`code/stock_tensor/pipeline.py:168-205`）。更直接的问题是 `selection_top_n` 配置虽被读取，却仅写入 manifest，没有驱动任何回测逻辑（`code/stock_tensor/config.py:82-84, 218-220`; `code/stock_tensor/pipeline.py:202-205`）。因此“不足二”当前是 0% 实现。

5. **高危：模式发现图表产物与论文表述不一致，论文已经声称存在的图表，代码根本不会生成。**  
   论文正文写明实验会输出“模型解释方差对比图、Rank IC 对比图、模型指标总览图、时间状态变化图和因子重要性热力图”（`paper_body.tex:159-161`），但 `output.py` 实际只生成 `model_explained_variance.svg` 和 `model_rank_ic.svg` 两张柱状图（`code/stock_tensor/output.py:209-241`）。时间状态与因子重要性目前只有 CSV/JSON，没有图；股票潜在相似结构也只有相似对数据，没有聚类可视化。`code/outputs/sample_run/` 的现有产物同样只包含这两张 SVG 和若干表格/JSON。也就是说，“不足四”不仅未完成，论文表述还已经先于实现。

6. **高危：训练输入扩展与 PIT 安全链路没有落地，正式因子面板仍是纯 K 线/估值派生版。**  
   当前 `build_formal_factor_panel.py` 只读取 K 线、行业和成分股历史，然后从 `close`、`peTTM`、`pbMRQ`、`psTTM`、`turn` 派生 `value_factor`、`momentum_factor`、`quality_factor`、`volatility_factor`、`turn_factor` 和 `future_return`（`code/data/build_formal_factor_panel.py:67-128`）。正式配置文件也只把 `value_factor`、`momentum_factor`、`quality_factor`、`volatility_factor` 作为训练输入（`code/configs/formal_hs300.yaml:14-19`; `code/configs/formal_sz50.yaml:14-19`；`formal_zz500.yaml` 同构）。这与原始计划要求的“宏观、财务 PIT、事件特征的数据字典 + 披露时点映射 + 纳入统一训练接口 + 三个样本池重跑”完全不符（`论文不足与完善计划.md:18-27`）。

7. **高危：参考文献规范化没有开始，正文-文献联动清单也不存在。**  
   `paper_body.tex` 的参考文献章节仍有多条明显未规范化条目，例如多处仍是 `[Z]` 占位或缺失刊物/页码/学校信息（`paper_body.tex:327-337`）。我在仓库内检索“正文引用—参考文献条目”核对表、citation audit、bibliography checklist 等产物均未发现，仅有原始计划本身提到需要建立这类清单（`论文不足与完善计划.md:106-115`）。因此“不足五”并未因为把任务标成 `in_progress` 就有任何实际进展。

8. **中危：Goal Tracker 没有如实记录 deferral 和 open issues。**  
   Claude 在总结里已经把五类工作全部推迟到后续轮次（`.humanize/rlcr/2026-04-26_14-59-46/round-0-summary.md:33-36`），但 `goal-tracker.md` 的 `Explicitly Deferred` 仍为空（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:62-65`），`Open Issues` 也为空（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:67-70`）。这违反了 tracker 的基本用途，也掩盖了当前真正的阻塞项，例如参考文献元数据缺失、扩展特征未建合同、组合层尚无实现、样本分层实验未配置等。

## Goal Alignment Summary

`ACs: 1/6 addressed | Forgotten items: 20 | Unjustified deferrals: 5`

- AC1：未推进。正文虽然已有“输入边界”讨论（`paper_body.tex:121`, `287-295`），但本轮没有新增数据字典、PIT 映射、扩展因子面板或重跑结果。
- AC2：未推进。代码中没有组合回测闭环实现，tracker 也只保留笼统任务名。
- AC3：未推进。原始计划要求全 A、行业分层、市值分层实验，但本轮没有新增配置、样本派生脚本或结果产物。
- AC4：未推进。只有两张基础 SVG，缺少热力图、阶段切换图、聚类图和对应论文增强说明。
- AC5：未推进。参考文献仍未规范化，也没有正文引用核对清单。
- AC6：仓库中确实存在独立计划文档，但这是本轮输入前提，不应被当成本轮核心完成成果。

### Forgotten Items

下列 20 个原始步骤没有被 tracker 作为独立任务跟踪：

- 不足一：数据字典整理、披露/可用时点映射、扩展版 factor panel 接入、HS300/SZ50/ZZ500 重跑。
- 不足二：Top-N/分组收益框架、换手/回撤/波动/夏普、风格/行业暴露检查、与 Rank IC 联动分析。
- 不足三：全 A 股实验、行业分层实验、市值分层实验、样本边界影响章节补写。
- 不足四：因子热力图、时间状态切换图、股票相似结构/行业聚类图、图前图后解释文字补充。
- 不足五：逐条元数据核对、统一格式重排、正文引用对照表、后续扩展时同步补引。

### Deferred Items

- Claude 实际延期了五条主线工作流，但没有给出强理由，也没有写入 `Explicitly Deferred`。
- 这些延期直接阻塞 AC1-AC5，因此全部属于不合理 deferral。

### Plan Evolution

- `Plan Evolution Log` 只有一条 “Initial plan”，没有记录任何真正的计划调整（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:40-44`）。
- 问题不在于“修改了计划”，而在于 Claude 把“执行计划”降格成了“登记计划”，但没有在 tracker 中承认这种收缩。

## Goal Tracker Update Request 处理

- Claude 的总结里没有 `Goal Tracker Update Request` 段落。
- 因此本轮我**没有直接修改** `goal-tracker.md`。但上面的 goal-alignment 结论已经说明，后续轮次必须先把 tracker 拆成与原始 20 个步骤一致的可验证任务，再继续实施。

## Directive Implementation Plan

Claude 下一轮不得继续停留在 loop/文档初始化层，必须按下面的单一路径把五类原始任务落地：

1. **先完成参考文献规范化，并同步修正文稿。**  
   以 `参考文献/` 目录下的 PDF/文档为唯一来源，逐条补齐 `paper_body.tex:322-340` 中缺失的作者、题名、年份、刊物/学校、卷期与页码；新增一份 `docs/thesis/reference-audit.md`，逐条记录“正文出现位置、对应参考文献编号、元数据校验结果、仍需补证据项”；然后回写 `paper_body.tex` 的参考文献章节与正文上标引用。

2. **把训练输入扩展做成正式合同，而不是只写论文说明。**  
   在 `code/data/` 下扩展正式因子面板生成链路：保留现有 `build_formal_factor_panel.py` 作为 baseline，但新增一个面向正式实验的扩展 builder，用 `code/data/formal/baostock/financial/` 与 `code/data/formal/baostock/reports/` 中已存在的数据表生成财务 PIT 和事件特征，并把“披露日期 -> 可用日期”的映射规则落成可复用函数；同时新增一份 `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`，明确每个扩展特征的来源表、时间字段、可用时点规则和输出列名。

3. **生成扩展版正式因子面板并重跑三大样本池。**  
   基于上一步的扩展 builder 产出 `hs300`、`sz50`、`zz500` 三个扩展 factor panel，补对应配置文件，使 `code/configs/formal_hs300.yaml`、`formal_sz50.yaml`、`formal_zz500.yaml` 指向新的扩展输入列集合；运行三组正式实验，产出新的 `metrics`、`factor_summary`、`time_regimes`、`selection_candidates`，并整理成一张可直接写入论文的“扩展前后对比表”。

4. **在现有评估模块上补齐组合回测闭环。**  
   以 `selection_candidates.json` 为输入，在 `code/stock_tensor/evaluation.py` 新增组合层评估：Top-N 组合、分组收益、累计净值、换手率、最大回撤、年化波动、夏普比率、行业暴露统计；让 `selection_top_n` 真正参与组合构建，而不是只写进 manifest；把结果写入新的 `portfolio_metrics.*`、`group_returns.*`、`drawdown.*`、`exposure.*` 产物，并补单测覆盖这些关键计算。

5. **把模式发现图表做成真实输出。**  
   在 `code/stock_tensor/output.py` 新增图形产物生成，至少落地四类图：因子重要性热力图、时间状态切换图、股票潜在相似结构/聚类图、模型指标总览图；同时让 `paper_body.tex` 中对图表的描述严格对应这些真实输出，不再提前声明不存在的图。

6. **扩展样本边界实验，不允许只写“后续会做”。**  
   基于现有 `all_a_tradable_history.csv` 与 `stock_industry.csv`，先补 `formal_all_a` 配置和全 A 股正式运行；再新增一条样本派生脚本，生成行业分层 universe；市值分层所需字段如果当前 formal 数据中缺失，必须先在同一轮中把用于分层的规模字段补进正式合同，再生成 size-layer universes。完成后输出多样本边界对比表，并把结论写回论文第五章和第六章。

7. **重写 goal tracker 的 mutable 区域，使之能约束执行。**  
   下一轮开始前，先把五类不足拆成与上面步骤一致的可验证任务，至少覆盖原始 20 个动作项；每完成一步就移动到 `Completed and Verified`，任何未做完的主线必须明确写入 `Explicitly Deferred` 并说明阻塞 AC 的影响。

8. **用自动化验证为每条新增能力兜底。**  
   扩展因子面板 builder、PIT 可用时点映射、组合评估、图表生成和新配置运行都必须补测试；至少运行受影响的 `unittest` 子集，并在总结中给出执行命令与结果。仅运行 loop 初始化脚本和 BitLesson selector 不再算有效验证。

## 结论

Round 0 只能判定为“初始化完成、主体工作未开始”。Claude 目前的产出不能视为原始计划的实现，更不能停止在后续轮次“继续推进”的表述上。下一轮必须直接进入上述补完计划，逐项交付实际代码、数据产物、论文修订和验证结果。
