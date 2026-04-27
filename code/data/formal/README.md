# Formal Data Layout

This directory now has two responsibilities:

1. Keep the legacy local formal fixtures as backward-compatible raw inputs.
2. Host the newer full-data layout for the formal all-A-share pipeline.

Legacy committed files such as `hs300_history.csv` and `hs300_factor_panel.csv` are still kept here as source fixtures and migration fallbacks, while the formal profiles are moving to the structured `universes/` and `factors/` layout.

需要区分两层时间口径：

- canonical formal 原始数据链可以继续覆盖到 `2026-04-01`
- 当前仓库提交、用于论文与 formal profile 复现实验的因子面板快照统一截断到 `2026-03-30`

For the newer formal layout, prefer the following structure:

- `code/data/formal/baostock/`
  - canonical baostock root for shared metadata, index memberships, shared kline panel, and manifest
- `code/data/formal/universes/`
  - `all_a_tradable_history.csv`
  - `hs300_history.csv`
  - `sz50_history.csv`
  - `zz500_history.csv`
- `code/data/formal/master/`
  - shared CN-A master / shared kline panel used by formal profile builders
  - transitional / final `full master` files
- `code/data/formal/financial/`
  - table-split full-data financial exports
- `code/data/formal/external/`
  - PIT-safe external macro / rate tables for extended factor inputs
- `code/data/formal/events/`
  - PIT-safe dividend, major-event, and announcement-text tables for extended factor inputs
- `code/data/formal/reports/`
  - table-split full-data report exports
- `code/data/formal/parquet/`
  - parquet mirrors of validated CSV outputs

Each structured subdirectory now also has its own `README.md` with:

- runnable commands
- file formats
- parameter notes
- expected inputs / outputs

`code/data/formal/master/README.md` 另外还会说明：

- full master 的标准字段合同
- 通达信价格量底座如何生成
- baostock shared master 如何补齐估值 / 状态字段
- 如何生成某一年的过渡版 full master 进行验证
- 如何在 Windows PowerShell 中通过 `code/data/build_full_master_for_existing_year.ps1` 直接调用本地 Python 生成某一年的 full master

Tongdaxin workflow:

1. Export the full daily panel to `tdx_daily_raw.csv` when you need stock-level raw daily data.
2. Build tracked named index daily CSV files directly from Tongdaxin `.day` sources：

```powershell
python3 code/data/build_tdx_named_index_files.py `
  --vipdoc-root D:\stock\TongDaXin\vipdoc `
  --output-dir code/data/formal/index_daily
```

该脚本会生成：

- `hs300_index_daily.csv` 对应 `000300.SH`
- `000050_index_daily.csv` 对应 `000050.SH`
- `csi_a500_index_daily.csv` 对应 `000510.SH`
- `zz500_index_daily.csv` 对应 `000905.SH`

Baostock workflow:

1. Create a dedicated canonical output directory, for example `code/data/formal/baostock/`.
2. Download index constituents and derived change records for:
   - 沪深300 (`hs300`)
   - 上证50 (`sz50`)
   - 中证500 (`zz500`)
3. Download company metadata with `--metadata-scope all_a` so `stock_basic.csv` and `stock_industry.csv` can support the formal all-A-share universe history.
   This also writes `metadata/all_a_codes.csv`, which is the raw baostock code list for the shared all-A master kline fetch.
4. Build `all_a_tradable_history.csv` from `stock_basic.csv`.
5. Download financial/report tables into the canonical root.
4. Example command:

```powershell
python3 code/data/fetch_baostock_data.py `
  --output-root code/data/formal/baostock `
  --start-date 2015-01-01 `
  --end-date 2026-04-01 `
  --indices hs300,sz50,zz500 `
  --metadata-scope all_a `
  --all-a-history-output code/data/formal/universes/all_a_tradable_history.csv
```

Output layout:

- `index_memberships/<index>_snapshots.csv`
- `index_memberships/<index>_changes.csv`
- `metadata/stock_basic.csv`
- `metadata/stock_industry.csv`
- `metadata/all_a_codes.csv`
- `code/data/formal/universes/all_a_tradable_history.csv`
- `financial/*.csv`
- `reports/*.csv`
- `manifest.json`

After the constituent snapshots are ready, you can build member-history files and kline panels:

```powershell
python3 code/data/build_baostock_member_history.py `
  --snapshot code/data/formal/baostock/index_memberships/hs300_snapshots.csv `
  --output code/data/formal/universes/hs300_history.csv `
  --horizon-date 2026-04-01
```

```powershell
python3 code/data/fetch_baostock_kline.py `
  --codes-file code/data/formal/baostock/metadata/all_a_codes.csv `
  --output-path code/data/formal/master/shared_kline_panel.csv `
  --start-date 2015-01-01 `
  --end-date 2026-04-01
```

If `stock_basic.csv` already exists, you can build the tradable all-A-share universe history offline:

```powershell
python3 code/data/build_all_a_tradable_history.py `
  --stock-basic-path code/data/formal/baostock/metadata/stock_basic.csv `
  --output-path code/data/formal/universes/all_a_tradable_history.csv `
  --horizon-date 2026-04-01
```

Once the structured CSV outputs are validated, you can create parquet mirrors:

```powershell
python3 code/data/convert_formal_csv_to_parquet.py `
  --formal-root code/data/formal `
  --overwrite
```

如果你要刷新当前提交版实验所使用的 baseline/extended 因子面板，推荐直接执行：

```powershell
python3 code/data/refresh_formal_factor_panels.py `
  --formal-root code/data/formal `
  --max-trade-date 2026-03-30
```

如果你要单独重建 AC1 所需的外部宏观、分红、重大事项和公告标题文本源表，执行：

```powershell
bash -lc '.venv/bin/python3 code/data/build_formal_extended_sources.py `
  --formal-root code/data/formal `
  --max-trade-date 2026-03-30 `
  --notice-lookback-days 180'
```

该命令会生成：

- `code/data/formal/external/macro_interest_rate.csv`
- `code/data/formal/external/macro_monthly_indicator.csv`
- `code/data/formal/events/dividend_event.csv`
- `code/data/formal/events/major_event_notice.csv`
- `code/data/formal/events/announcement_text.csv`

当前这些表以提交版实验窗口为主要服务对象，并统一带有 `pub_date` 与 `available_date` 字段，用于 `build_extended_factor_panel.py` 中的 PIT-safe 选择逻辑。

如果你要刷新 AC3 的样本边界扩展资产，推荐执行：

```powershell
python3 code/data/refresh_segmented_formal_assets.py `
  --formal-root code/data/formal `
  --max-trade-date 2026-03-30
```

该脚本会同时生成：

- `universes/segmented/all_a_active_history.csv`
- `universes/segmented/industry_c39_history.csv`
- `universes/segmented/industry_c27_history.csv`
- `universes/segmented/industry_c35_history.csv`
- `universes/segmented/size_small_history.csv`
- `universes/segmented/size_mid_history.csv`
- `universes/segmented/size_large_history.csv`
- 以及对应的 7 份 baseline factor panel

分层 run 完成后，可以生成 AC4 的模式发现扩展图组：

```powershell
python3 code/data/build_pattern_discovery_assets.py `
  --anchor-output-dir code/outputs/formal_all_a_run `
  --comparison-output-dir code/outputs/formal_hs300_run `
  --comparison-output-dir code/outputs/formal_sz50_run `
  --comparison-output-dir code/outputs/formal_zz500_run `
  --comparison-output-dir code/outputs/formal_all_a_run `
  --comparison-output-dir code/outputs/formal_industry_c27_run `
  --comparison-output-dir code/outputs/formal_industry_c35_run `
  --comparison-output-dir code/outputs/formal_industry_c39_run `
  --comparison-output-dir code/outputs/formal_size_small_run `
  --comparison-output-dir code/outputs/formal_size_mid_run `
  --comparison-output-dir code/outputs/formal_size_large_run `
  --output-dir code/data/formal/reports/pattern_discovery `
  --model-name tucker `
  --max-stocks 60
```

该命令会生成股票潜在结构图、聚类与行业交叉图、跨样本边界 Tucker 指标对比图，以及 `pattern_discovery_summary.json`。

如果你要刷新跨样本边界的组合表现与行业/风格暴露汇总，执行：

```powershell
python3 code/data/summarize_boundary_portfolio.py `
  --output-dir code/outputs/formal_hs300_run `
  --output-dir code/outputs/formal_sz50_run `
  --output-dir code/outputs/formal_zz500_run `
  --output-dir code/outputs/formal_all_a_run `
  --output-dir code/outputs/formal_industry_c27_run `
  --output-dir code/outputs/formal_industry_c35_run `
  --output-dir code/outputs/formal_industry_c39_run `
  --output-dir code/outputs/formal_size_small_run `
  --output-dir code/outputs/formal_size_mid_run `
  --output-dir code/outputs/formal_size_large_run `
  --report-dir code/data/formal/reports/boundary_portfolio `
  --exposure-limit 3
```

该命令会生成 `boundary_portfolio_summary.json` 和 Markdown 汇总表，用于把 Rank IC、稳定性、Top-N 收益、分组价差、多空 NAV、成本后 NAV、交易成本、超额 NAV、年化波动、Sharpe、回撤、换手率和主要暴露统一到同一张表。

如果你要为 AC3 / AC4 生成长窗口稳健性复跑入口，执行：

```powershell
python3 code/data/build_long_window_run_plan.py `
  --config code/configs/formal_all_a.yaml `
  --config code/configs/formal_industry_c27.yaml `
  --config code/configs/formal_industry_c35.yaml `
  --config code/configs/formal_industry_c39.yaml `
  --config code/configs/formal_size_small.yaml `
  --config code/configs/formal_size_mid.yaml `
  --config code/configs/formal_size_large.yaml `
  --start-date 2015-01-01 `
  --end-date 2026-03-30 `
  --report-dir code/data/formal/reports/long_window_plan
```

该命令会生成：

- `long_window_run_plan.json`
- `long_window_plan/configs/*.yaml`
- `long_window_plan/README.md`

这些派生配置按年份拆分全 A、行业分层和市值分层实验，并默认指向 `code/data/formal/factors/long_window/*_long_window.csv`。在当前仓库里，`2015-2026` 全部年度的 long-window run 都已经完成本地复跑。

如果你要构建 long-window 专用因子面板，执行：

```powershell
python3 code/data/build_long_window_factor_panels.py `
  --formal-root code/data/formal `
  --start-year 2015 `
  --end-year 2026 `
  --max-trade-date 2026-03-30
```

该命令会：

- 使用 `master/full_master_<year>.csv` 为 2015-2026 每个年度分别生成 all A、行业分层和市值分层因子面板
- 将年度面板拼接为 `code/data/formal/factors/long_window/*_long_window.csv`
- 保留 `code/data/formal/factors/long_window/yearly/<year>/` 中间产物，便于逐年排障

如果你要刷新全年份长窗口的跨边界组合汇总，执行：

```powershell
@'
from pathlib import Path
import sys
sys.path.insert(0, str(Path("code").resolve()))
from data.summarize_boundary_portfolio import summarize_boundary_portfolio
root = Path("code/outputs")
output_dirs = sorted(root.glob("formal_*_long_window_run"))
summarize_boundary_portfolio(
  output_dirs=output_dirs,
  report_dir=Path("code/data/formal/reports/long_window_portfolio"),
  exposure_limit=3,
)
'@ | python3 -
```

该命令会输出 `code/data/formal/reports/long_window_portfolio/README.md` 与对应 JSON 汇总。

如果你要为全部年份生成 long-window 模式发现图组，执行：

```powershell
@'
from pathlib import Path
import sys
sys.path.insert(0, str(Path("code").resolve()))
from data.build_pattern_discovery_assets import build_pattern_discovery_assets
project_root = Path(".").resolve()
base = Path("code/outputs")
for year in range(2015, 2027):
    anchor = base / f"formal_all_a_{year}_long_window_run"
    comparisons = [
        anchor,
        base / f"formal_industry_c27_{year}_long_window_run",
        base / f"formal_industry_c35_{year}_long_window_run",
        base / f"formal_industry_c39_{year}_long_window_run",
        base / f"formal_size_small_{year}_long_window_run",
        base / f"formal_size_mid_{year}_long_window_run",
        base / f"formal_size_large_{year}_long_window_run",
    ]
    build_pattern_discovery_assets(
        project_root=project_root,
        anchor_output_dir=anchor,
        comparison_output_dirs=comparisons,
        output_dir=Path("code/data/formal/reports") / f"pattern_discovery_long_window_{year}",
        model_name="tucker",
        max_stocks=60,
    )
'@ | bash -lc '.venv/bin/python3 -'
```

## Stage 2 Dataset-Year Runner

你现在可以用统一入口脚本按“表 + 年份”执行 Stage 2：

### 执行抓取

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh profit_data 2015
bash code/data/run_baostock_stage2_dataset_year.sh forecast_report 2015
```

### 检查某一年是否已经完整导入

```powershell
bash code/data/run_baostock_stage2_dataset_year.sh 2015
```

检查模式会输出：

- 8 个 dataset 的完成状态
- 已完成 `code|year` 数 / 总数
- 对应 `dataset/year.csv` 是否存在
- 当前行数

## Full Master Route

如果你准备使用“通达信价格量 + baostock补字段”的方式构建正式 shared master / full master，推荐路线如下：

### Step 1

先从通达信原始日线中切出某一年的原始切片：

```powershell
python3 code/data/build_tdx_year_slice.py `
  --input-path code/data/formal/tdx_daily_raw.csv `
  --output-path code/data/formal/master/tdx_2015_raw.csv `
  --year 2015
```

### Step 2

把通达信原始切片转换成标准化价格量主表：

```powershell
python3 code/data/build_tdx_full_master_base.py `
  --input-path code/data/formal/master/tdx_2015_raw.csv `
  --output-path code/data/formal/master/tdx_full_master_base_2015.csv `
  --adjustflag-value 2
```

### Step 3

如果当前只有短窗口的 baostock shared master，可以先生成过渡版：

```powershell
powershell -ExecutionPolicy Bypass -File code/data/build_full_master_for_existing_year.ps1 2015
```

### Step 4

如果你已经抓到某一年的独立 baostock 补字段源，例如：

- `code/data/formal/master/baostock_fields/2015.csv`

则优先使用它来补齐估值 / 状态字段，而不是继续用短窗口的 `shared_kline_panel.csv`。
