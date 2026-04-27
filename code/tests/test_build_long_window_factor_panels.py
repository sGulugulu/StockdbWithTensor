from pathlib import Path
import csv
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_long_window_factor_panels import build_long_window_factor_panels


class BuildLongWindowFactorPanelsTests(unittest.TestCase):
    def test_build_long_window_factor_panels_builds_and_concatenates_yearly_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "formal"
            (root / "master").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "metadata").mkdir(parents=True, exist_ok=True)
            (root / "universes" / "segmented").mkdir(parents=True, exist_ok=True)

            (root / "baostock" / "metadata" / "stock_industry.csv").write_text(
                "\n".join(
                    [
                        "updateDate,code,code_name,industry,industryClassification",
                        "2026-03-30,sh.600000,浦发银行,J66货币金融服务,证监会行业分类",
                    ]
                ),
                encoding="utf-8",
            )
            for history_name in (
                "all_a_active_history.csv",
                "industry_c27_history.csv",
                "industry_c35_history.csv",
                "industry_c39_history.csv",
                "size_small_history.csv",
                "size_mid_history.csv",
                "size_large_history.csv",
            ):
                (root / "universes" / "segmented" / history_name).write_text(
                    "\n".join(
                        [
                            "market_id,universe_id,stock_code,start_date,end_date",
                            "cn_a,TEST,600000,2015-01-01,2026-12-31",
                        ]
                    ),
                    encoding="utf-8",
                )

            for year, rows in (
                (
                    2015,
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,pctChg,source_price_vendor,source_file,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2015-01-05,sh.600000,10,10,10,10,9,100,1000,2,0,tongdaxin,a,1,1,10,2,3,4,0",
                        "2015-01-12,sh.600000,10,10,10,11,10,100,1000,2,0,tongdaxin,a,1,1,10,2,3,4,0",
                    ],
                ),
                (
                    2016,
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,pctChg,source_price_vendor,source_file,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2016-01-04,sh.600000,11,11,11,12,11,100,1000,2,0,tongdaxin,a,1,1,10,2,3,4,0",
                        "2016-01-11,sh.600000,12,12,12,13,12,100,1000,2,0,tongdaxin,a,1,1,10,2,3,4,0",
                    ],
                ),
            ):
                (root / "master" / f"full_master_{year}.csv").write_text("\n".join(rows), encoding="utf-8")

            outputs = build_long_window_factor_panels(
                formal_root=root,
                start_year=2015,
                end_year=2016,
                max_trade_date="2016-12-31",
            )

            final_panel = root / "factors" / "long_window" / "all_a_factor_panel_long_window.csv"
            self.assertIn(final_panel, outputs)
            self.assertTrue(final_panel.exists())
            with final_panel.open("r", encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                rows = list(reader)
            dates = [row["trade_date"] for row in rows]
            self.assertIn("2015-01-05", dates)
            self.assertIn("2016-01-04", dates)
            self.assertTrue((root / "factors" / "long_window" / "yearly" / "2015" / "all_a_factor_panel_long_window.csv").exists())


if __name__ == "__main__":
    unittest.main()
