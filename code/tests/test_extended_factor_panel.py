from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_extended_factor_panel import build_extended_factor_panel


class ExtendedFactorPanelTests(unittest.TestCase):
    def test_build_extended_factor_panel_merges_pit_and_event_features(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            base_panel = root / "base.csv"
            profit_data = root / "profit.csv"
            perf_dir = root / "performance_express_report"
            perf_dir.mkdir(parents=True, exist_ok=True)
            perf_data = perf_dir / "2026.csv"
            forecast_dir = root / "forecast_report"
            forecast_dir.mkdir(parents=True, exist_ok=True)
            forecast_data = forecast_dir / "2026.csv"
            market_index = root / "hs300_index_daily.csv"
            output_path = root / "extended.csv"

            base_panel.write_text(
                "\n".join(
                    [
                        "stock_code,trade_date,industry,value_factor,momentum_factor,quality_factor,volatility_factor,turn_factor,ps_ttm,future_return",
                        "600000.SH,2026-03-25,Bank,0.5,0.1,0.2,0.3,0.4,1.0,0.02",
                        "600000.SH,2026-03-30,Bank,0.5,0.1,0.2,0.3,0.4,1.0,0.02",
                    ]
                ),
                encoding="utf-8",
            )
            profit_data.write_text(
                "\n".join(
                    [
                        "code,pubDate,statDate,roeAvg,npMargin,gpMargin,netProfit,epsTTM,MBRevenue,totalShare,liqaShare,dataset,query_year,query_quarter",
                        "sh.600000,2026-03-24,2025-12-31,0.11,0.22,0.33,1,0.44,1,1,1,profit_data,2025,4",
                    ]
                ),
                encoding="utf-8",
            )
            perf_data.write_text(
                "\n".join(
                    [
                        "code,performanceExpPubDate,performanceExpStatDate,performanceExpUpdateDate,performanceExpressTotalAsset,performanceExpressNetAsset,performanceExpressEPSChgPct,performanceExpressROEWa,performanceExpressEPSDiluted,performanceExpressGRYOY,performanceExpressOPYOY,dataset,query_year",
                        "sh.600000,2026-03-25,2025-12-31,2026-03-25,1,1,0.55,6.7,1,0.66,0.77,performance_express_report,2026",
                    ]
                ),
                encoding="utf-8",
            )
            forecast_data.write_text(
                "\n".join(
                    [
                        "code,profitForcastExpPubDate,profitForcastExpStatDate,profitForcastType,profitForcastAbstract,profitForcastChgPctUp,profitForcastChgPctDwn,dataset,query_year",
                        "sh.600000,2026-03-25,2025-12-31,预增,预计增长,20,10,forecast_report,2026",
                    ]
                ),
                encoding="utf-8",
            )
            market_index.write_text(
                "\n".join(
                    [
                        "market,tdx_prefix,stock_code,trade_date,open,high,low,close,amount,volume,source_file",
                        "sh,sh,000300.SH,2026-03-18,100,100,100,100,1000,100,a",
                        "sh,sh,000300.SH,2026-03-19,100,100,100,101,1100,100,a",
                        "sh,sh,000300.SH,2026-03-20,100,100,100,102,1200,100,a",
                        "sh,sh,000300.SH,2026-03-23,100,100,100,103,1300,100,a",
                        "sh,sh,000300.SH,2026-03-24,100,100,100,104,1400,100,a",
                        "sh,sh,000300.SH,2026-03-25,100,100,100,105,1500,100,a",
                        "sh,sh,000300.SH,2026-03-30,100,100,100,106,1600,100,a",
                    ]
                ),
                encoding="utf-8",
            )

            build_extended_factor_panel(
                base_panel_path=base_panel,
                profit_data_path=profit_data,
                performance_express_path=perf_dir,
                forecast_report_path=forecast_dir,
                market_index_path=market_index,
                output_path=output_path,
            )

            content = output_path.read_text(encoding="utf-8")
            self.assertIn("market_return_1d", content)
            self.assertIn("pit_roe_avg", content)
            self.assertIn("perf_express_eps_chg_pct", content)
            self.assertIn("perf_express_flag", content)
            self.assertIn("forecast_direction", content)
            self.assertIn("forecast_flag", content)
            self.assertIn("0.11", content)
            self.assertIn("0.55", content)

            rows = output_path.read_text(encoding="utf-8").strip().splitlines()
            first_data = rows[1].split(",")
            second_data = rows[2].split(",")
            header = rows[0].split(",")
            row1 = dict(zip(header, first_data))
            row2 = dict(zip(header, second_data))
            self.assertEqual(row1["trade_date"], "2026-03-25")
            self.assertAlmostEqual(float(row1["pit_roe_avg"]), 0.11, places=6)
            self.assertEqual(float(row1["perf_express_flag"]), 0.0)
            self.assertEqual(float(row1["perf_express_eps_chg_pct"]), 0.0)
            self.assertEqual(float(row1["forecast_flag"]), 0.0)
            self.assertEqual(row2["trade_date"], "2026-03-30")
            self.assertEqual(float(row2["perf_express_flag"]), 1.0)
            self.assertAlmostEqual(float(row2["perf_express_eps_chg_pct"]), 0.55, places=6)
            self.assertEqual(float(row2["forecast_flag"]), 1.0)
            self.assertEqual(float(row2["forecast_direction"]), 1.0)
            self.assertAlmostEqual(float(row2["forecast_chg_pct_up"]), 20.0, places=6)
            self.assertGreater(float(row2["market_momentum_5d"]), 0.0)

    def test_build_extended_factor_panel_supports_max_trade_date_cap(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            base_panel = root / "base.csv"
            profit_data = root / "profit.csv"
            perf_dir = root / "performance_express_report"
            perf_dir.mkdir(parents=True, exist_ok=True)
            perf_data = perf_dir / "2026.csv"
            forecast_dir = root / "forecast_report"
            forecast_dir.mkdir(parents=True, exist_ok=True)
            forecast_data = forecast_dir / "2026.csv"
            market_index = root / "hs300_index_daily.csv"
            output_path = root / "extended.csv"

            base_panel.write_text(
                "\n".join(
                    [
                        "stock_code,trade_date,industry,value_factor,momentum_factor,quality_factor,volatility_factor,turn_factor,ps_ttm,future_return",
                        "600000.SH,2026-03-25,Bank,0.5,0.1,0.2,0.3,0.4,1.0,0.02",
                        "600000.SH,2026-03-30,Bank,0.5,0.1,0.2,0.3,0.4,1.0,0.02",
                    ]
                ),
                encoding="utf-8",
            )
            profit_data.write_text(
                "\n".join(
                    [
                        "code,pubDate,statDate,roeAvg,npMargin,gpMargin,netProfit,epsTTM,MBRevenue,totalShare,liqaShare,dataset,query_year,query_quarter",
                        "sh.600000,2026-03-24,2025-12-31,0.11,0.22,0.33,1,0.44,1,1,1,profit_data,2025,4",
                    ]
                ),
                encoding="utf-8",
            )
            perf_data.write_text(
                "\n".join(
                    [
                        "code,performanceExpPubDate,performanceExpStatDate,performanceExpUpdateDate,performanceExpressTotalAsset,performanceExpressNetAsset,performanceExpressEPSChgPct,performanceExpressROEWa,performanceExpressEPSDiluted,performanceExpressGRYOY,performanceExpressOPYOY,dataset,query_year",
                        "sh.600000,2026-03-26,2025-12-31,2026-03-26,1,1,0.55,6.7,1,0.66,0.77,performance_express_report,2026",
                    ]
                ),
                encoding="utf-8",
            )
            forecast_data.write_text(
                "\n".join(
                    [
                        "code,profitForcastExpPubDate,profitForcastExpStatDate,profitForcastType,profitForcastAbstract,profitForcastChgPctUp,profitForcastChgPctDwn,dataset,query_year",
                        "sh.600000,2026-03-25,2025-12-31,预增,预计增长,20,10,forecast_report,2026",
                    ]
                ),
                encoding="utf-8",
            )
            market_index.write_text(
                "\n".join(
                    [
                        "market,tdx_prefix,stock_code,trade_date,open,high,low,close,amount,volume,source_file",
                        "sh,sh,000300.SH,2026-03-24,100,100,100,104,1400,100,a",
                        "sh,sh,000300.SH,2026-03-25,100,100,100,105,1500,100,a",
                        "sh,sh,000300.SH,2026-03-30,100,100,100,106,1600,100,a",
                    ]
                ),
                encoding="utf-8",
            )

            build_extended_factor_panel(
                base_panel_path=base_panel,
                profit_data_path=profit_data,
                performance_express_path=perf_dir,
                forecast_report_path=forecast_dir,
                market_index_path=market_index,
                output_path=output_path,
                max_trade_date="2026-03-25",
            )

            content = output_path.read_text(encoding="utf-8")
            self.assertIn("2026-03-25", content)
            self.assertNotIn("2026-03-30", content)


if __name__ == "__main__":
    unittest.main()
