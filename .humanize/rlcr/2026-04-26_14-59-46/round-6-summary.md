# Round 6 Summary

## Work Completed

- 按 Round 5 review 的 AC1 directive，扩展了第一版完整 extended 输入：
  - 在 `code/data/build_extended_factor_panel.py` 中新增市场级代理变量：
    - `market_return_1d`
    - `market_momentum_5d`
    - `market_volatility_20d`
    - `market_amount_change_5d`
  - 新增业绩预告事件特征：
    - `forecast_direction`
    - `forecast_chg_pct_up`
    - `forecast_chg_pct_dwn`
    - `forecast_flag`
  - 财务 PIT、业绩快报和业绩预告统一改为“公告日后的首个交易日可用”规则，不再允许公告当日直接生效
- 修改 `code/data/refresh_formal_factor_panels.py`，将 `index_daily` 与 `forecast_report` 接入 extended panel 统一刷新入口
- 更新 3 个 extended formal 配置，使新增 `market_*` 和 `forecast_*` 列真实进入训练接口
- 更新扩展输入合同与说明文档：
  - `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`
  - `code/data/formal/factors/README.md`
  - `训练输入扩展与PIT安全说明.md`
- 重建 3 个 extended factor panel，并重跑：
  - `formal_hs300_extended_run`
  - `formal_sz50_extended_run`
  - `formal_zz500_extended_run`
- 同步回写文稿：
  - `paper_body.tex` 已改成“市场代理变量 + 财务 PIT + 快报 + 预告”的描述
  - `扩展特征对照实验结果.md` 已改成新的 extended 对照表和观察结论

## Files Changed

- `code/data/build_extended_factor_panel.py`
- `code/data/refresh_formal_factor_panels.py`
- `code/data/formal/factors/EXTENDED_FACTOR_CONTRACT.md`
- `code/data/formal/factors/README.md`
- `code/data/formal/factors/hs300_factor_panel_extended.csv`
- `code/data/formal/factors/sz50_factor_panel_extended.csv`
- `code/data/formal/factors/zz500_factor_panel_extended.csv`
- `code/configs/formal_hs300_extended.yaml`
- `code/configs/formal_sz50_extended.yaml`
- `code/configs/formal_zz500_extended.yaml`
- `code/tests/test_config_profiles.py`
- `code/tests/test_extended_factor_panel.py`
- `code/tests/test_refresh_formal_factor_panels.py`
- `paper_body.tex`
- `扩展特征对照实验结果.md`
- `训练输入扩展与PIT安全说明.md`
- `.humanize/rlcr/2026-04-26_14-59-46/round-6-summary.md`

## Validation

以下验证均在当前 Windows 主机 PowerShell 环境中执行：

- `python -m unittest discover -s code/tests -p test_extended_factor_panel.py`：通过
- `python -m unittest discover -s code/tests -p test_refresh_formal_factor_panels.py`：通过
- `python -m unittest discover -s code/tests -p test_config_profiles.py`：通过
- `python code/data/refresh_formal_factor_panels.py --formal-root code/data/formal --max-trade-date 2026-03-30`：通过
- `python code/main.py --config code/configs/formal_hs300_extended.yaml`：通过
- `python code/main.py --config code/configs/formal_sz50_extended.yaml`：通过
- `python code/main.py --config code/configs/formal_zz500_extended.yaml`：通过
- `latexmk -xelatex -synctex=1 -interaction=nonstopmode -file-line-error "-outdir=.latex-build" template.tex`：通过

额外核实：

- `hs300_factor_panel_extended.csv` 已真实包含 `market_*` 与 `forecast_*` 列
- `paper_body.tex` 与 `扩展特征对照实验结果.md` 已切换到新的扩展输入口径
- 三组 extended formal 输出已按新列重跑

## Remaining Items

- AC1：第一版完整扩展输入已接入，但更完整宏观变量与更广泛事件字典尚未完成
- AC2：仍缺分位数组收益、多空组合、交易成本、基准超额收益和更系统的暴露比较
- AC3：全 A / 行业分层 / 市值分层实验仍未落地
- AC4：股票潜在结构图、行业聚类图和样本边界对比图仍未完成
- AC5：参考文献条目级元数据补齐与最终格式统一仍未完成
- 验证入口说明仍需在仓库文档中进一步统一，避免 WSL/Windows 解释器差异造成误解

## Goal Tracker Update Request

### Requested Changes:
- 将 AC1 中 `将通过 PIT 校验的扩展特征接入统一训练接口并生成扩展版 factor panel` 的备注更新为：已接入市场级代理变量、财务 PIT、业绩快报和业绩预告四类第一版特征
- 将 Open Issues 中“扩展特征当前仅覆盖财务 PIT 与业绩快报”调整为“已扩展到市场代理变量 + 财务 PIT + 快报 + 预告，但更完整宏观变量与更广泛事件字典仍待补齐”
- 在 Plan Evolution Log 中记录：Round 6 已把 AC1 从“局部特征接入”推进到“第一版完整扩展输入合同”

### Justification:
Round 6 的核心工作是响应 Round 5 review 对 AC1 的主体要求。当前 extended panel 已不再只依赖财务 PIT 与快报，而是完成了第一版市场代理变量、财务 PIT、快报和预告的统一接入。Tracker 需要反映这一真实推进，否则后续 review 会继续沿用过时状态。

## BitLesson Delta

- Action: none
- Lesson ID(s): NONE
- Notes:
  - 已按流程读取 `.humanize/bitlesson.md`
  - `bitlesson-select.sh` 仍因本地 selector 流式请求断开不可用，且当前知识库无有效条目，因此本轮继续按 `NONE` 执行
