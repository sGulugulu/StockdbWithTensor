# Round 0 Review Result

## Findings

1. **阻断：Round 0 仍未完成原计划主体交付，Claude 自己也承认四条主线仍未完成。**  
   原计划要求五类不足都形成“补实验、补图表、补样本边界、补参考文献”的实体闭环，而不是只补说明文档（`论文不足与完善计划.md:18-27`, `40-49`, `62-71`, `84-93`, `106-115`）。当前总结明确承认仍未完成组合回测、样本边界扩展、模式发现增强图组和参考文献完整规范化（`.humanize/rlcr/2026-04-26_14-59-46/round-0-summary.md:41-46`）。这意味着 Round 0 只能算“补了部分说明文档并初始化追踪器”，不能算按原计划完成本轮实现。

2. **高危：Goal Tracker 的验收口径仍然被弱化成“说明/方案/记录”，没有绑定原计划中的实物产出。**  
   当前 AC1-AC5 仍然只要求“分析与扩展说明”“完善路径”“增强方案”“核对与修订方案”等（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:26-31`），但原计划对应的验收物是扩展版因子面板、三样本重跑结果、回测结果表、分组收益图和回撤图、多样本边界实验对比表、模式发现扩展图组、规范化参考文献列表等实体产物（`论文不足与完善计划.md:24-27`, `46-49`, `68-71`, `90-93`, `112-115`）。按当前 AC 设计，只写说明也能被误判为“达标”，这与原计划不一致。

3. **高危：AC1 被错误标记为 completed，但实际既没有“扩展特征字典”，也没有“可用时点映射”，更没有把扩展特征并入训练接口。**  
   `goal-tracker.md` 把“建立扩展特征字典与 PIT 安全说明文档”标成 completed（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:51`），但 `训练输入扩展与PIT安全说明.md` 只是描述“未来的数据字典至少要包含哪些字段”和“未来的可用时点映射应如何做”（`训练输入扩展与PIT安全说明.md:44-64`），并没有给出任何已经填好的特征字典表、字段清单或映射样例。代码层面，正式因子面板仍然只从 K 线字段派生 `value_factor`、`momentum_factor`、`quality_factor`、`volatility_factor`、`turn_factor` 和 `future_return`（`code/data/build_formal_factor_panel.py:92-117`），正式配置也仍只使用四个主线因子（`code/configs/formal_hs300.yaml:21-26`，`formal_sz50.yaml` 和 `formal_zz500.yaml` 同构）。更严重的是，正文声称 formal 数据链“已经具备财务、报告、复权和宏观等更多数据资产”（`paper_body.tex:123`），但仓库里 `code/data/formal/baostock/` 实际只有 `financial`、`reports`、`metadata`、`index_memberships` 和 `kline_panel.csv`，根本没有 `macro/` 目录或宏观对齐面板。这一块存在实质性过度表述。

4. **高危：论文与实验叙事声称存在显式训练/验证/测试协议和 held-out 评估，但当前 pipeline 仍是整样本拟合。**  
   论文正文已经写明“执行协议化预处理和训练/验证/测试切分，并只在测试集上进行 held-out 评估”（`paper_body.tex:153`）。但当前配置模型没有任何 split 配置，只有 `top_k_pairs`、`rolling_window` 和 `selection_top_n`（`code/stock_tensor/config.py:75-84`, `214-220`）；`build_tensor_dataset` 直接在全量记录上做填充、去极值、标准化（`code/stock_tensor/dataset.py:70-172`）；`run_experiment` 也是直接在完整张量上拟合、选 rank、算指标、写结果（`code/stock_tensor/pipeline.py:102-179`）。这意味着现有 `Rank IC`、`IR`、`rolling_stability` 乃至未来的组合回测如果继续沿用这条路径，都不是严格的 out-of-sample 结果。这个方法学缺口比“少了一张图”更严重。

5. **高危：组合回测闭环完全没有落地，`selection_top_n` 仍然只是读取后写进 manifest。**  
   `round-0-summary.md` 已承认组合回测尚未进入评估与输出链路（`.humanize/rlcr/2026-04-26_14-59-46/round-0-summary.md:43`）。代码核查也一致：`compute_quality_metrics` 只计算 `mse`、`rmse`、`explained_variance`、`compression_ratio`、`bic`、`ic_mean`、`rank_ic_mean`、`ir`（`code/stock_tensor/evaluation.py:64-103`）；`build_selection_records` 和 `build_candidate_pool` 只是把分数落盘（`code/stock_tensor/evaluation.py:199-276`）；`selection_top_n` 只在配置中读取，并在 manifest 中写出（`code/stock_tensor/config.py:82-84`, `218-220`; `code/stock_tensor/pipeline.py:194-206`），没有驱动任何 Top-N 组合、分组收益、换手率、最大回撤、年化波动、夏普、行业暴露或风格暴露计算。不足二当前仍是 0% 实现。

6. **高危：样本边界扩展仍然完全缺席，仓库里只有三个正式样本配置和对应输出。**  
   原计划要求新增全 A 股实验、行业分层实验和市值分层实验（`论文不足与完善计划.md:62-71`），但 `code/configs/` 里只有 `formal_hs300.yaml`、`formal_sz50.yaml`、`formal_zz500.yaml` 三个正式配置；`code/outputs/` 也只有 `formal_hs300_run`、`formal_sz50_run`、`formal_zz500_run` 三个正式样本输出目录。虽然 formal 数据底座已经有 `all_a_tradable_history.csv`、`stock_industry.csv`、`financial/profit_data.csv` 这类足以支撑全 A/行业/市值分层的原始材料，但目前没有任何派生 universe、分层配置或对比实验结果。`goal-tracker.md` 只记录了“设计扩展实验路径”（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:55-56`），没有记录实际运行任务。

7. **高危：模式发现增强图组没有落地，输出模块仍只生成两张柱状图。**  
   原计划要求增加因子重要性热力图、时间状态切换图、股票潜在相似结构或行业聚类示意，并在图前图后补说明（`论文不足与完善计划.md:84-93`）。当前 `write_outputs` 只生成 `model_explained_variance.svg` 和 `model_rank_ic.svg` 两张柱状图（`code/stock_tensor/output.py:209-218`）；虽有 `factor_summary_*`、`time_regimes_*` 和 `stock_similarity_*` 数据文件，但没有任何热力图、时间线图、聚类散点图或样本池分层图。`round-0-summary.md` 也承认“模式发现增强图组尚未落地到真实输出模块”（`.humanize/rlcr/2026-04-26_14-59-46/round-0-summary.md:45`）。这不是“细节待优化”，而是原计划的核心产物没有实现。

8. **高危：参考文献规范化仍停留在核对清单阶段，论文参考文献章节仍保留多个明显未规范化条目。**  
   `参考文献元数据核对清单.md` 已经清楚标出条目 6、10、11、12、14、15、16、17 仍待补齐（`参考文献元数据核对清单.md:24-35`, `51-53`），而 `paper_body.tex` 的参考文献章节也仍保留多条 `[Z]` 占位或信息不完整条目（`paper_body.tex:329`, `333-340`），例如夏虹综述、曾亚丽研究、Brandi 论文、Tensor predictability paper、High-dimensional Factor Models、Rank Determination、Tensor VAR 等。换句话说，Round 0 确实建立了核对清单，但“不足五”的预期产出之一“规范化参考文献列表”和“论文最终提交版参考文献章节”并没有实现。

## Goal Alignment Summary

`ACs: 3/6 addressed | Forgotten items: 7 | Unjustified deferrals: 5`

- AC1：**部分推进，但完成状态不成立。** 有说明文档和正文补写（`训练输入扩展与PIT安全说明.md`，`paper_body.tex:105`, `289`），但没有真实数据字典、可用时点映射、统一训练接口和三样本重跑结果。
- AC2：**未实质推进。** 只有 future work 描述与 pending task，没有任何组合回测实现或产物。
- AC3：**未实质推进。** 没有全 A、行业分层、市值分层配置与输出。
- AC4：**未实质推进。** 没有新增模式发现图组，只有两张基础柱状图。
- AC5：**部分推进。** 有核对清单和正文回写，但参考文献条目本身仍未完成规范化。
- AC6：**已推进。** 独立计划文档和两份配套说明文档确实存在。

### Forgotten Items

以下原计划事项没有被 Goal Tracker 作为独立可验证任务跟踪，或者被压缩成“设计/说明”后失去执行约束：

1. 将通过 PIT 校验的扩展特征真正纳入统一训练接口。
2. 重跑 HS300、SZ50、ZZ500 三个样本池并形成扩展前后对比表。
3. 将组合层结果与 Rank IC 指标做联动分析。
4. 新增全 A 股样本实验并形成结果产物。
5. 新增行业分层样本实验并形成结果产物。
6. 新增市值分层样本实验并形成结果产物。
7. 按学校格式真正重排参考文献章节，而不只是记录待补字段。

### Deferred Items

- Claude 已经实际把五类不足中的主体实现都推迟到后续轮次，但 `Explicitly Deferred` 仍为空（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:72-76`）。
- 这些 deferral 直接阻塞 AC1-AC5，因此都不成立，不能视为“合理阶段切分”。

### Plan Evolution

- `Plan Evolution Log` 新增了“拆细子任务并补充开放问题”的记录（`.humanize/rlcr/2026-04-26_14-59-46/goal-tracker.md:42-45`），这一步本身合理。
- 但拆细后的 tracker 仍然没有覆盖原计划里的关键执行动作，尤其是 AC1 的接口接入与重跑、AC2 的 Rank IC 联动、AC3 的真实分层实验。因此“提高可验证性”的目标没有真正达成。

## Goal Tracker Update Request 处理

- Claude 的总结里没有 `Goal Tracker Update Request` 段落。
- 因此本轮我**没有直接修改** `goal-tracker.md`。

## Directive Implementation Plan

Claude 下一轮不得继续追加“说明文档”替代主体工作，必须按下面这条单一路径把原计划补齐：

1. **先补 split 协议，再做任何新增实验。**  
   修改 `code/stock_tensor/config.py` 和三份 `code/configs/formal_*.yaml`，显式加入时间切分配置；新增 `code/stock_tensor/splits.py`，把训练、验证、测试窗口切分做成独立模块；调整 `code/stock_tensor/pipeline.py`，用验证集选 rank，用测试集计算最终指标，并把实际窗口写入 `run_manifest.json`。没有这一步，后续回测和样本扩展结果都不具备可信度。

2. **把“不足一”从说明文档升级为真实扩展输入合同。**  
   保留当前 `code/data/build_formal_factor_panel.py` 作为 baseline 生成器，新增 `code/data/build_extended_factor_panel.py` 作为扩展版生成器；用现有 `code/data/formal/baostock/financial/profit_data.csv` 的 `pubDate/statDate/roeAvg/npMargin/.../totalShare` 字段和 `code/data/formal/baostock/reports/forecast_report/*.csv`、`performance_express_report/*.csv` 的公告字段构造真正的财务 PIT 与事件特征；同时补上仓库里当前缺失的宏观抓取与对齐链路，新增 `code/data/fetch_baostock_macro.py` 和 `code/data/build_macro_aligned_panel.py`，把宏观原始数据落到 `code/data/formal/baostock/macro/<dataset>/<year>.csv`，再对齐成 `code/data/formal/master/macro_daily.csv`。最后新增 `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`，逐列写清来源表、披露字段、最早可用交易日规则和缺失处理规则。

3. **生成扩展版因子面板并重跑三大正式样本池。**  
   在 `code/configs/` 新增或改造扩展版 formal 配置，使 HS300、SZ50、ZZ500 都能切换到扩展因子面板；完成基线版与扩展版两套运行，产出一张统一对比表，至少比较最优 rank、解释方差、Rank IC、IR、滚动稳定性以及新增组合层指标。没有三样本重跑结果，就不能宣称 AC1 已完成。

4. **补齐组合回测闭环，并让 `selection_top_n` 真正生效。**  
   在 `code/stock_tensor/evaluation.py` 新增组合层评估模块，以测试集上的 `selection_signal` 为输入，构建 Top-N 组合和分组收益序列，输出累计净值、换手率、最大回撤、年化波动、夏普、行业暴露和风格暴露；把结果写成 `portfolio_metrics.*`、`group_returns.*`、`drawdown.*`、`exposure.*` 产物；再在 `summary.md` 和论文第五章里补“组合表现与 Rank IC 一致性分析”。这一步完成前，AC2 不得视为已推进。

5. **按现有数据底座把样本边界扩展真正跑起来。**  
   直接复用 `code/data/formal/universes/all_a_tradable_history.csv` 生成 `formal_all_a.yaml`；复用 `code/data/formal/baostock/metadata/stock_industry.csv` 生成行业 universe，并固定选择“股票数量最多的前三个行业”作为行业分层样本；复用 `profit_data.csv` 的 `totalShare` 与日频 `close` 计算 PIT 市值，按每个交易日三分位切成 `large/mid/small` 三个 size universe。随后新增对应配置、跑完实验、输出“基线三指数 vs 全 A vs 行业前三 vs 大中小盘”的多样本边界对比表，并把结论回写 `paper_body.tex`。

6. **把模式发现图组做成真实输出，而不是只在正文里承诺。**  
   扩展 `code/stock_tensor/output.py` 和 `code/stock_tensor/pipeline.py`，基于已有 `factor_summary`、`time_regimes`、`stock_similarity` 和 `stock_cluster` 生成至少四类图：`factor_importance_heatmap_<model>.svg`、`time_regime_timeline_<model>.svg`、`stock_cluster_scatter_<model>.svg`、`sample_boundary_comparison.svg`。正文只能引用已经真实落盘的图，不得再提前声明仓库不存在的图组。

7. **完成参考文献章节的真正规范化，而不是保留核对清单即止。**  
   以 `参考文献元数据核对清单.md` 中标出的 6、10、11、12、14、15、16、17 号条目为优先对象，逐条补齐作者、载体、年份、卷期和页码；把 `paper_body.tex:329-340` 的占位条目全部改成学校要求的正式格式；再复查正文中的上标引用顺序和清单一致。只有当参考文献章节本身改完，AC5 才能算通过。

8. **为新增能力补测试，并做最小充分验证。**  
   至少新增 `code/tests/test_split_strategy.py`、`test_extended_factor_panel.py`、`test_portfolio_evaluation.py`、`test_output_contract.py`，覆盖 split、PIT 映射、扩展因子落盘、组合层指标和新增图形产物；运行受影响的 `unittest` 子集以及三组 formal 配置；最后重新执行 `latexmk`，确保论文正文与新产物一致。

## 结论

Round 0 当前只能认定为“补了两份说明文档、改了正文、初始化了追踪器”，不能认定为完成了《论文不足与完善计划》的实体工作。Claude 下一轮必须直接进入上述实现主线，逐项交付代码、实验产物、论文修订和验证结果；在 AC1-AC5 主体闭环完成之前，不得输出 `COMPLETE`。
