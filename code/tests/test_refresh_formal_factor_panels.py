from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.refresh_formal_factor_panels import refresh_formal_factor_panels


class RefreshFormalFactorPanelsTests(unittest.TestCase):
    def test_refresh_formal_factor_panels_builds_baseline_and_extended_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "formal"
            (root / "master").mkdir(parents=True, exist_ok=True)
            (root / "universes").mkdir(parents=True, exist_ok=True)
            (root / "factors").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "metadata").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "financial").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "reports" / "performance_express_report").mkdir(parents=True, exist_ok=True)

            (root / "master" / "shared_kline_panel.csv").write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2026-03-25,sh.600000,1,1,1,10,9,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-03-25,sh.600001,1,1,1,11,10,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                        "2026-03-30,sh.600000,1,1,1,12,10,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-03-30,sh.600001,1,1,1,13,11,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                        "2026-04-03,sh.600000,1,1,1,14,12,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-04-03,sh.600001,1,1,1,15,13,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "baostock" / "metadata" / "stock_industry.csv").write_text(
                "\n".join(
                    [
                        "updateDate,code,code_name,industry,industryClassification",
                        "2026-03-30,sh.600000,浦发银行,J66货币金融服务,证监会行业分类",
                        "2026-03-30,sh.600001,邯郸钢铁,C31黑色金属冶炼和压延加工业,证监会行业分类",
                    ]
                ),
                encoding="utf-8",
            )
            for history_name in ("hs300_history.csv", "sz50_history.csv", "zz500_history.csv"):
                (root / "universes" / history_name).write_text(
                    "\n".join(
                        [
                            "market_id,universe_id,stock_code,start_date,end_date",
                            "cn_a,IDX,600000,2026-03-25,2026-03-30",
                            "cn_a,IDX,600001,2026-03-25,2026-03-30",
                        ]
                    ),
                    encoding="utf-8",
                )
            (root / "baostock" / "financial" / "profit_data.csv").write_text(
                "\n".join(
                    [
                        "code,pubDate,statDate,roeAvg,npMargin,gpMargin,netProfit,epsTTM,MBRevenue,totalShare,liqaShare,dataset,query_year,query_quarter",
                        "sh.600000,2026-03-24,2025-12-31,0.11,0.22,0.33,1,0.44,1,1,1,profit_data,2025,4",
                        "sh.600001,2026-03-24,2025-12-31,0.12,0.23,0.34,1,0.45,1,1,1,profit_data,2025,4",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "baostock" / "reports" / "performance_express_report" / "2026.csv").write_text(
                "\n".join(
                    [
                        "code,performanceExpPubDate,performanceExpStatDate,performanceExpUpdateDate,performanceExpressTotalAsset,performanceExpressNetAsset,performanceExpressEPSChgPct,performanceExpressROEWa,performanceExpressEPSDiluted,performanceExpressGRYOY,performanceExpressOPYOY,dataset,query_year",
                        "sh.600000,2026-03-26,2025-12-31,2026-03-26,1,1,0.55,6.7,1,0.66,0.77,performance_express_report,2026",
                        "sh.600001,2026-03-26,2025-12-31,2026-03-26,1,1,0.56,6.8,1,0.67,0.78,performance_express_report,2026",
                    ]
                ),
                encoding="utf-8",
            )

            outputs = refresh_formal_factor_panels(formal_root=root, max_trade_date="2026-03-30")

            self.assertEqual(len(outputs), 6)
            for output_path in outputs:
                self.assertTrue(output_path.exists())
                content = output_path.read_text(encoding="utf-8")
                self.assertIn("2026-03-30", content)
                self.assertNotIn("2026-04-03", content)


if __name__ == "__main__":
    unittest.main()
