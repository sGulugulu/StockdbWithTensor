# Master

这个目录保存正式共享市场主数据。当前重点文件是：

- `shared_kline_panel.csv`
- `FULL_MASTER_CONTRACT.md`

它应该最终成为：

- 全 A 范围
- `2015-01-01` 到 `2026-04-01`
- 前复权

## 文件格式

当前共享 kline 使用 baostock 原始字段为主，常见字段包括：

- `date`
- `code`
- `open`
- `high`
- `low`
- `close`
- `preclose`
- `volume`
- `amount`
- `adjustflag`
- `turn`
- `tradestatus`
- `pctChg`
- `peTTM`
- `pbMRQ`
- `psTTM`
- `pcfNcfTTM`
- `isST`
- `query_year`（按年份切窗抓取时附加）

说明：

- `code` 使用 baostock 原生格式，例如 `sh.600000`
- `date` 使用 `YYYY-MM-DD`

## 按年份抓共享 kline

### 跑某一年

```powershell
bash code/data/run_baostock_stage3_year.sh 2015
```

### 直接跑底层脚本

```powershell
.venv/bin/python code/data/fetch_baostock_kline.py `
  --codes-file code/data/formal/baostock/metadata/all_a_codes.csv `
  --output-path code/data/formal/master/shared_kline_panel.csv `
  --progress-path code/data/formal/master/shared_kline_panel_2015.progress.json `
  --start-date 2015-01-01 `
  --end-date 2015-12-31 `
  --adjustflag 2 `
  --partition-by-year
```

## 参数说明

`fetch_baostock_kline.py`

- `--codes-file`
  - 代码列表，推荐使用 `metadata/all_a_codes.csv`
- `--output-path`
  - 输出共享 kline 文件
- `--progress-path`
  - 进度文件，建议按年份单独保存
- `--start-date` / `--end-date`
  - 请求窗口
- `--adjustflag`
  - `2` 表示前复权
- `--partition-by-year`
  - 自动把窗口拆成逐年请求，并记录 `completed_units`
- `--batch-size`
  - 单批股票数量
- `--no-resume`
  - 禁用恢复

## 注意

- 当前建议始终按年跑，不要一口气请求 `2015-2026`
- 如果一个年份跑完，再进入下一个年份

## Full Master Contract

如果你要把通达信作为价格量底座，再用 baostock 补齐估值 / 状态字段，完整字段合同见：

- `code/data/formal/master/FULL_MASTER_CONTRACT.md`

## Transitional Full Master For One Year

如果你现在只是想先验证某一年的 full master 生成链，而不是等待完整的全 A shared master 重建完成，可以直接生成一版“过渡版 full master”。

### 一键命令

```powershell
powershell -ExecutionPolicy Bypass -File code/data/build_full_master_for_existing_year.ps1 2015
```

也可以在当前 PowerShell 会话里直接运行：

```powershell
.\code\data\build_full_master_for_existing_year.ps1 2015
```

这个 `.ps1` 入口脚本已经适配了 **Windows PowerShell -> WSL `.venv/bin/python`** 的调用方式。

也就是说：

- 你在 Windows PowerShell 里直接运行即可
- 不需要手动切到 WSL shell
- 脚本内部会自动调用 WSL 里的 `.venv/bin/python`
- 中文路径编码问题已经处理过，不需要你手工写 `/mnt/d/...`

### 输入文件

- `code/data/formal/tdx_daily_raw.csv`
- `code/data/formal/master/baostock_fields/2015.csv` 或你手动指定给 `merge_baostock_master_fields.py` 的年份补字段源

### 输出文件

- `code/data/formal/master/tdx_2015_raw.csv`
- `code/data/formal/master/tdx_full_master_base_2015.csv`
- `code/data/formal/master/full_master_2015.csv`

### 当前限制

- 这版 `full_master_2015.csv` 是**过渡版**，不是最终正式版。
- 价格量字段来自通达信，因此是完整的。
- baostock 补字段是否能补上，取决于 `shared_kline_panel.csv` 是否覆盖到目标年份。
- 当前仓库里的 `shared_kline_panel.csv` 仍是短窗口数据，所以像 `2015` 这种年份通常会出现：
  - `turn` 空
  - `tradestatus` 空
  - `peTTM` 空
  - `pbMRQ` 空
  - `psTTM` 空
  - `pcfNcfTTM` 空
  - `isST` 空

### 代码格式

- 通达信原始输入：`600000.SH`
- 过渡版 full master 输出：`sh.600000`

后者与 baostock shared master 和后续补字段合并逻辑保持一致。

对应的两个脚本是：

### 1. 通达信原始日线 -> TDX Base Master

```powershell
.venv/bin/python code/data/build_tdx_full_master_base.py `
  --input-path code/data/formal/tdx_daily_raw.csv `
  --output-path code/data/formal/master/tdx_full_master_base.csv `
  --adjustflag-value 2
```

### 2. 用 baostock shared master 补齐估值 / 状态字段

```powershell
.venv/bin/python code/data/merge_baostock_master_fields.py `
  --tdx-base-path code/data/formal/master/tdx_full_master_base.csv `
  --baostock-path code/data/formal/master/shared_kline_panel.csv `
  --output-path code/data/formal/master/full_master.csv
```

### 3. 先切某一年的通达信切片再单独验证

```powershell
.venv/bin/python code/data/build_tdx_year_slice.py `
  --input-path code/data/formal/tdx_daily_raw.csv `
  --output-path code/data/formal/master/tdx_2015_raw.csv `
  --year 2015
```

### 3. 为某一年单独抓 baostock 补字段源

如果你不想碰当前 `shared_kline_panel.csv`，而是为某个年份单独生成补字段源，再去合并对应年份的 full master，可以用：

```powershell
bash code/data/run_baostock_master_fields_year.sh 2015 2
```

说明：

- 第 1 个参数：年份
- 第 2 个参数：同时并行抓几个月，默认建议 `2`
- 如果存在 `code/data/formal/master/tdx_full_master_base_<year>.csv`，
  脚本会优先从该年份 TDX base 中提取实际出现的股票代码，再抓 baostock 补字段
- 只有在对应年份的 `tdx_full_master_base_<year>.csv` 不存在时，才会回退到 `all_a_codes.csv`

输出位置：

- 月文件：
  - `code/data/formal/master/baostock_fields/2015/2015-01.csv`
  - ...
- 年文件：
  - `code/data/formal/master/baostock_fields/2015.csv`

然后你可以用它去补 2015 年的过渡版 full master：

```powershell
.\code\data\build_full_master_for_existing_year.ps1 2015
```

## 检查某一年的 full master

如果你想检查某一年 `full_master_<year>.csv` 是否完整，可以运行：

```powershell
.venv/bin/python code/data/check_full_master_year.py --year 2015
```

默认会输出并写入：

- `code/data/formal/master/full_master_2015_check.json`

检查内容包括：

- 行数
- 日期范围
- 股票数量
- 以下字段的非空数量与非空率：
  - `turn`
  - `tradestatus`
  - `peTTM`
  - `pbMRQ`
  - `psTTM`
  - `pcfNcfTTM`
  - `isST`

如果某些补字段非空率过低，结果会标记为 `ISSUES`，并在 `issues` 中指出问题。

## 对账某一年的 TDX base / baostock_fields / full master

如果你想进一步定位问题到底出在：

- `tdx_full_master_base_<year>.csv`
- `baostock_fields/<year>.csv`
- `full_master_<year>.csv`

可以运行：

```powershell
.venv/bin/python code/data/reconcile_full_master_year.py --year 2019
```

默认会输出并写入：

- `code/data/formal/master/logs/full_master_2019_reconcile.log`

这个对账日志会告诉你：

- 三层文件各自的行数
- 日期范围
- 股票数量
- `date + code` 的覆盖差异
- 有差异的股票完整列表与日期完整列表

日志里除了 `top-*` 概览外，还会额外写出：

- `all-missing-from-baostock-by-code`
- `all-missing-from-baostock-by-date`
- `all-extra-in-baostock-by-code`
- `all-extra-in-baostock-by-date`

这样你可以直接从日志里定位具体差异股票和具体差异日期，而不是只看 top10。
- `tdx` 有但 `baostock_fields` 没有的 top code / top date
- `full_master` 的补字段非空率

适合排查“为什么某个年份补字段非空率偏低”这类问题。

## 审计某一年的 baostock_fields 质量

如果你想进一步判断问题是不是出在：

- `baostock_fields/<year>.csv` 里有重复 `date + code`
- `baostock_fields/<year>.csv` 在和 TDX base 的交集键上存在空补字段

可以运行：

```powershell
.venv/bin/python code/data/audit_baostock_fields_year.py --year 2019
```

默认会输出并写入：

- `code/data/formal/master/logs/baostock_fields_2019_audit.json`

这个审计文件会告诉你：

- `intersection_keys`
- `duplicate_key_count`
- `duplicate_keys`
- 每个补字段在交集键上的空值计数
- 哪些日期最容易出现空值
- 哪些股票最容易出现空值
