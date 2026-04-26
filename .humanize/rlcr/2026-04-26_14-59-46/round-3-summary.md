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

## 修改文件

- `code/stock_tensor/evaluation.py`
- `code/stock_tensor/pipeline.py`
- `code/stock_tensor/preprocess.py`
- `code/tests/test_split_strategy.py`
- `code/tests/test_pipeline.py`
- `.humanize/rlcr/2026-04-26_14-59-46/round-3-summary.md`

## 测试与验证

- 已通过：
  - `python -m unittest discover -s code/tests -p test_split_strategy.py`
  - `python -m unittest discover -s code/tests -p test_pipeline.py`
  - `python -m unittest discover -s code/tests -p test_dataset.py`
  - `python -m unittest discover -s code/tests -p test_config.py`

- 验证结果：
  - `selection_top_n=1` 时，候选池按日期只保留 1 只股票。
  - `stock` split 下，验证集股票行业信息可被保留到预处理输出。

## 当前未完成项

1. formal HS300、SZ50、ZZ500 输出仍未按 split 新协议重跑并刷新。
2. 论文与说明文档中的正式窗口口径虽已部分修正，但 formal 数据、factor panel 与正式输出仍未完全统一。
3. 扩展特征字典、PIT 映射、扩展版 factor panel 仍未真正进入训练接口。
4. 组合回测闭环、样本边界扩展实验、模式发现增强图组和参考文献最终规范化仍未完成。

## Goal Tracker Update Request

### Requested Changes:
- 将 “实现显式训练/验证/测试切分与 held-out 评估，并把 split 元数据写入产物” 保持为 `in_progress`，但更新备注：`selection_top_n` 合同与 `stock/hybrid` 行业元数据缺陷已修复。
- 在 Open Issues 中删除或弱化以下两项：
  - `runtime.selection_top_n` 当前未实际生效
  - `stock / hybrid split` 下行业元数据丢失
- 保留 “重跑 formal 输出替换旧 manifest” 为高优先级待办，因为 formal 证据链仍未刷新。

### Justification:
本轮不是新增说明文档，而是修复了 review 明确指出的两条真实代码缺陷，因此 tracker 中关于 AC2 的状态应反映“主链路继续推进且两个阻塞 bug 已被清除”，但由于 formal 输出尚未刷新，AC2 仍不能视为完成。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes: 当前 `.humanize/bitlesson.md` 仍为空知识库；本轮代码修复任务未匹配到既有 lesson。
