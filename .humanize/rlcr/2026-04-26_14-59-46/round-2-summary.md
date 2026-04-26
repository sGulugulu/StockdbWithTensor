# Round 2 Summary

## 本轮完成内容

1. 实现了最小可运行的 split 协议主链路，修复了论文中“显式 train/validation/test 切分与 held-out 评估”只写在正文里、代码却没有实现的问题。
2. 更新 `code/stock_tensor/config.py`：
   - 新增 `SplitConfig`
   - 为 `PreprocessConfig` 增加 `fill_strategy` 和 `standardize_method`
   - 要求配置文件显式提供 `split` 段
3. 更新 `code/stock_tensor/dataset.py`：
   - 引入 `build_raw_tensor_dataset`
   - 引入 `slice_tensor_dataset`
   - 为 `TensorDataset` 增加 `preprocess_summary`
4. 新增 `code/stock_tensor/preprocess.py`：
   - 落地 train-only 预处理状态拟合
   - 支持将训练集状态复用到 validation/test/refit 分区
5. 新增 `code/stock_tensor/splits.py`：
   - 支持 `time` / `stock` / `hybrid` 三种切分策略
   - 生成 split metadata 供 `run_manifest.json` 使用
6. 更新 `code/stock_tensor/models.py`：
   - 为 CP/Tucker/PCA 模型补充 held-out scoring 所需的 `score_*` 函数
   - 补上 `weights`、`core`、`mean_vector` 等诊断信息
7. 更新 `code/stock_tensor/pipeline.py`：
   - 引入 raw dataset -> split plan -> preprocess fit/apply -> validation rank selection -> refit -> held-out test scoring 的完整流程
   - 在 run manifest 中写入 `split` 和 `preprocess` 元数据
8. 更新配置文件：
   - `code/configs/default.yaml`
   - `code/configs/sample_cn_smoke.yaml`
   - `code/configs/sample_us_equity.yaml`
   - `code/configs/formal_hs300.yaml`
   - `code/configs/formal_sz50.yaml`
   - `code/configs/formal_zz500.yaml`
   以上配置均已补入 `fill_strategy`、`standardize_method` 与 `split`
9. 更新测试：
   - `code/tests/test_config.py`
   - `code/tests/test_dataset.py`
   - `code/tests/test_pipeline.py`
10. 修正了论文中关于正式实验窗口的失实表述，使其与当前根仓库中已提交的 formal 输出窗口一致，而不再错误宣称已完成 2015-2026 全窗口正式结果。

## 修改文件

- `code/stock_tensor/config.py`
- `code/stock_tensor/dataset.py`
- `code/stock_tensor/preprocess.py`
- `code/stock_tensor/splits.py`
- `code/stock_tensor/models.py`
- `code/stock_tensor/pipeline.py`
- `code/configs/default.yaml`
- `code/configs/sample_cn_smoke.yaml`
- `code/configs/sample_us_equity.yaml`
- `code/configs/formal_hs300.yaml`
- `code/configs/formal_sz50.yaml`
- `code/configs/formal_zz500.yaml`
- `code/tests/test_config.py`
- `code/tests/test_dataset.py`
- `code/tests/test_pipeline.py`
- `paper_body.tex`

## 测试与验证

- 已通过：
  - `python -m unittest discover -s code/tests -p test_config.py`
  - `python -m unittest discover -s code/tests -p test_dataset.py`
  - `python -m unittest discover -s code/tests -p test_pipeline.py`
  - `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error -outdir=.latex-build template.tex`

- 结果说明：
  - split 配置已被 loader 正常识别
  - dataset 预处理摘要与新接口可正常工作
  - pipeline 已输出 split 元数据并通过现有 smoke test
  - 论文仍可编译

## 当前未完成项

1. 正式样本窗口仍未真正扩展到论文原先希望的长期窗口，当前只是修正了错误叙述。
2. 扩展输入仍停留在说明文档和核对清单层，没有真实接入财务 PIT、事件和宏观特征。
3. 组合回测闭环仍未实现。
4. 全 A / 行业分层 / 市值分层实验仍未落地。
5. 模式发现增强图组仍未实现。
6. 参考文献缺失元数据仍未全部补齐。

## Goal Tracker Update Request

### Requested Changes:
- 将 AC1 相关任务“建立扩展特征字典与 PIT 安全说明文档”“将训练输入边界说明回写到第三章与局限性分析”继续保留为已完成，但新增一条 open issue：真实扩展输入合同和接入代码仍未落地。
- 在 Active Tasks 中新增或强化以下待办：
  - split 协议已落地，但“扩展版 factor panel 接入统一训练接口”仍待实现
  - “组合回测闭环实现”应提升优先级
  - “样本边界扩展实验落地”应提升优先级
  - “模式发现增强图组实现”应保持 pending
  - “参考文献最终规范化”应保持 pending
- 在 Open Issues 中新增：
  - 当前根仓库 formal 输出窗口与论文最初长期窗口目标不一致，只完成了叙事修正，尚未完成数据与实验层补齐

### Justification:
本轮已经把 split/held-out 协议真正落到了代码与配置中，这是 review 指出的首要方法学缺口。但原计划中更大的实体交付仍未完成，因此 tracker 需要明确区分“方法协议已修复”和“数据、实验、图表、参考文献主体任务仍待继续”。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: 当前 `.humanize/bitlesson.md` 仍为空知识库；本轮继续执行的 split 协议迁移任务暂无可匹配 lesson。
