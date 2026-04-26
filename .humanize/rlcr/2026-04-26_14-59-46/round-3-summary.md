# Round 3 Summary

## 本轮完成内容

1. 针对 Round 2 review 指出的两个明确代码缺陷，完成了实质性修复：
   - `runtime.selection_top_n` 不再是死配置，候选池会按交易日执行 Top-N 裁剪。
   - `stock` / `hybrid` split 下，非训练股票的行业元数据不再在预处理阶段被写成 `None`。
2. 更新 `code/stock_tensor/evaluation.py`：
   - 为 `build_candidate_pool` 增加 `selection_top_n` 参数。
   - 统一按每个交易日截取得分最高的前 N 只股票进入候选池。
3. 更新 `code/stock_tensor/pipeline.py`：
   - 将 `config.runtime.selection_top_n` 传入 candidate pool 构建链路，使配置真正生效。
   - 修正 `apply_preprocess_state` 新签名的调用，显式传入 validation/test/refit 分区的行业映射。
4. 更新 `code/stock_tensor/preprocess.py`：
   - `apply_preprocess_state` 新增 `industries` 参数。
   - 预处理后输出的 `industries` 改为来自当前分区的原始行业映射，而不再只从训练态缓存中查找。
5. 新增/更新测试：
   - `code/tests/test_split_strategy.py`：验证 `stock` split 下验证集行业信息不会丢失。
   - `code/tests/test_pipeline.py`：新增 `selection_top_n` 按日期裁剪候选池的回归测试。
6. 重跑正式输出：
   - 重新运行 `formal_hs300`、`formal_sz50`、`formal_zz500` 三组实验。
   - 三个正式 `run_manifest.json` 现已包含 `preprocess` 与 `split` 元数据，不再是旧版简化 manifest。
   - `candidate_pool_size` 已受 `selection_top_n=20` 控制，三个正式样本池目前均裁剪为每个测试日 Top-20，总量为 80。
7. 修正文稿与说明文档中的窗口口径：
   - `paper_body.tex` 已把“长期正式窗口既成事实”改为“当前已提交正式输出窗口”的准确表述。
   - `训练输入扩展与PIT安全说明.md` 已删除“已统一到 2015-01-05 至 2026-04-01”的失实说法，改成区分数据底座窗口、factor panel 窗口和当前 formal 输出窗口。

## 修改文件

- `code/stock_tensor/evaluation.py`
- `code/stock_tensor/pipeline.py`
- `code/stock_tensor/preprocess.py`
- `code/tests/test_split_strategy.py`
- `code/tests/test_pipeline.py`
- `paper_body.tex`
- `训练输入扩展与PIT安全说明.md`
- `.humanize/rlcr/2026-04-26_14-59-46/round-3-summary.md`

## 测试与验证

- 已通过：
  - `python -m unittest discover -s code/tests -p test_split_strategy.py`
  - `python -m unittest discover -s code/tests -p test_pipeline.py`
  - `python -m unittest discover -s code/tests -p test_dataset.py`
  - `python -m unittest discover -s code/tests -p test_config.py`
  - `python code/main.py --config code/configs/formal_hs300.yaml`
  - `python code/main.py --config code/configs/formal_sz50.yaml`
  - `python code/main.py --config code/configs/formal_zz500.yaml`
  - `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error -outdir=.latex-build template.tex`

- 验证结果：
  - `selection_top_n=1` 时，候选池按日期只保留 1 只股票。
  - `stock` split 下，验证集股票行业信息可被保留到预处理输出。
  - formal HS300/SZ50/ZZ500 输出已刷新为带 split / preprocess 合同的新 manifest。
  - 论文与训练输入说明文档中的正式窗口表述已与当前根仓库产物口径对齐。

## 当前未完成项

1. formal 数据底座、factor panel 与正式输出之间仍未统一到同一长期窗口，当前只是把正文与说明文档修正为与已提交 formal 输出一致。
2. 扩展特征字典、PIT 映射、扩展版 factor panel 仍未真正进入训练接口。
3. 组合回测闭环、样本边界扩展实验、模式发现增强图组和参考文献最终规范化仍未完成。

## Goal Tracker Update Request

### Requested Changes:
- 将 “实现显式训练/验证/测试切分与 held-out 评估，并把 split 元数据写入产物” 保持为 `in_progress`，但更新备注：`selection_top_n` 合同与 `stock/hybrid` 行业元数据缺陷已修复。
- 在 Open Issues 中删除或弱化以下两项：
  - `runtime.selection_top_n` 当前未实际生效
  - `stock / hybrid split` 下行业元数据丢失
- 将 “重跑 formal 输出替换旧 manifest” 标记为已完成。
- 保留 “formal 长期窗口口径未统一”“扩展版 factor panel 未落地”“组合回测闭环未实现” 为高优先级待办。

### Justification:
本轮不仅修复了 review 明确指出的两条真实代码缺陷，还重跑并刷新了三组 formal 输出，使 split / preprocess 合同开始进入正式证据链。因此 tracker 中关于 AC2 的状态应反映“formal 输出已刷新，但组合层评估仍未实现”；同时 AC1 相关的窗口口径开放问题仍需继续保留。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: 当前 `.humanize/bitlesson.md` 仍为空知识库；本轮代码修复任务未匹配到既有 lesson。
