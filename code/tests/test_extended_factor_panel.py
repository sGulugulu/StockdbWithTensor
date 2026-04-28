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
            external_dir = root / "external"
            external_dir.mkdir(parents=True, exist_ok=True)
            macro_interest = external_dir / "macro_interest_rate.csv"
            macro_monthly = external_dir / "macro_monthly_indicator.csv"
            events_dir = root / "events"
            events_dir.mkdir(parents=True, exist_ok=True)
            dividend_event = events_dir / "dividend_event.csv"
            major_event_notice = events_dir / "major_event_notice.csv"
            announcement_text = events_dir / "announcement_text.csv"
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
            macro_interest.write_text(
                "\n".join(
                    [
                        "source_api,metric_id,metric_name,pub_date,available_date,value,expected_value,previous_value",
                        "akshare,policy_rate_current,china_policy_rate,2026-03-24,2026-03-25,2.5,0.0,2.4",
                        "akshare,lpr_1y,china_lpr_1y,2026-03-24,2026-03-25,3.1,0.0,3.2",
                        "akshare,lpr_5y,china_lpr_5y,2026-03-24,2026-03-25,3.6,0.0,3.7",
                    ]
                ),
                encoding="utf-8",
            )
            macro_monthly.write_text(
                "\n".join(
                    [
                        "source_api,metric_id,metric_name,pub_date,available_date,value,expected_value,previous_value",
                        "akshare,cpi_mom,china_cpi_monthly,2026-03-20,2026-03-23,0.8,0.0,0.7",
                        "akshare,m2_yoy,china_m2_yearly,2026-03-20,2026-03-23,7.1,0.0,7.0",
                        "akshare,industrial_production_yoy,china_industrial_production_yoy,2026-03-20,2026-03-23,5.5,0.0,5.3",
                        "akshare,exports_yoy,china_exports_yoy,2026-03-20,2026-03-23,4.4,0.0,4.1",
                        "akshare,imports_yoy,china_imports_yoy,2026-03-20,2026-03-23,3.3,0.0,3.1",
                    ]
                ),
                encoding="utf-8",
            )
            dividend_event.write_text(
                "\n".join(
                    [
                        "stock_code,report_period,dividend_type,pub_date,available_date,record_date,ex_date,pay_date,bonus_ratio,transfer_ratio,cash_ratio,plan_text,source_api",
                        "600000.SH,2025年报,年度分红,2026-03-24,2026-03-25,2026-03-27,2026-03-28,2026-03-30,0,1,2.5,10派2.5元,akshare",
                    ]
                ),
                encoding="utf-8",
            )
            major_event_notice.write_text(
                "\n".join(
                    [
                        "stock_code,notice_type,pub_date,available_date,title_text,title_length,keyword_score,severity_score,url,source_api",
                        "600000.SH,重大事项,2026-03-24,2026-03-25,关于重大事项停牌公告,10,1.5,2.5,https://example.com/a,akshare",
                    ]
                ),
                encoding="utf-8",
            )
            announcement_text.write_text(
                "\n".join(
                    [
                        "stock_code,notice_type,pub_date,available_date,title_text,title_length,keyword_score,url,source_api",
                        "600000.SH,其他,2026-03-24,2026-03-25,关于分红预案与回购安排的公告,14,1.6,https://example.com/b,akshare",
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
                        "sh,sh,000300.SH,2026-03-26,100,100,100,103,2000,100,a",
                        "sh,sh,000300.SH,2026-03-27,100,100,100,102,2300,100,a",
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
                macro_interest_rate_path=macro_interest,
                macro_monthly_path=macro_monthly,
                dividend_event_path=dividend_event,
                major_event_notice_path=major_event_notice,
                announcement_text_path=announcement_text,
                output_path=output_path,
            )

            content = output_path.read_text(encoding="utf-8")
            self.assertIn("market_return_1d", content)
            self.assertIn("market_momentum_20d", content)
            self.assertIn("market_drawdown_20d", content)
            self.assertIn("market_amount_zscore_20d", content)
            self.assertIn("macro_proxy_risk_score", content)
            self.assertIn("macro_proxy_liquidity_score", content)
            self.assertIn("macro_policy_rate", content)
            self.assertIn("macro_lpr_1y", content)
            self.assertIn("macro_imports_yoy", content)
            self.assertIn("pit_roe_avg", content)
            self.assertIn("pit_data_age_days", content)
            self.assertIn("dividend_cash_ratio", content)
            self.assertIn("dividend_flag", content)
            self.assertIn("perf_express_eps_chg_pct", content)
            self.assertIn("perf_express_age_days", content)
            self.assertIn("perf_express_flag", content)
            self.assertIn("forecast_direction", content)
            self.assertIn("forecast_change_midpoint", content)
            self.assertIn("forecast_change_width", content)
            self.assertIn("forecast_age_days", content)
            self.assertIn("event_positive_flag", content)
            self.assertIn("event_negative_flag", content)
            self.assertIn("event_uncertainty_score", content)
            self.assertIn("event_age_decay_score", content)
            self.assertIn("event_intensity_score", content)
            self.assertIn("major_event_count_30d", content)
            self.assertIn("announcement_keyword_score_30d", content)
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
            self.assertEqual(float(row2["event_positive_flag"]), 1.0)
            self.assertEqual(float(row2["event_negative_flag"]), 0.0)
            self.assertAlmostEqual(float(row2["macro_policy_rate"]), 2.5, places=6)
            self.assertAlmostEqual(float(row2["macro_lpr_1y"]), 3.1, places=6)
            self.assertAlmostEqual(float(row2["macro_imports_yoy"]), 3.3, places=6)
            self.assertAlmostEqual(float(row2["dividend_cash_ratio"]), 2.5, places=6)
            self.assertEqual(float(row2["dividend_flag"]), 1.0)
            self.assertAlmostEqual(float(row2["forecast_chg_pct_up"]), 20.0, places=6)
            self.assertAlmostEqual(float(row2["forecast_change_midpoint"]), 15.0, places=6)
            self.assertAlmostEqual(float(row2["forecast_change_width"]), 10.0, places=6)
            self.assertAlmostEqual(float(row2["event_uncertainty_score"]), 10.0, places=6)
            self.assertEqual(float(row2["forecast_age_days"]), 5.0)
            self.assertEqual(float(row2["perf_express_age_days"]), 5.0)
            self.assertEqual(float(row2["pit_data_age_days"]), 6.0)
            self.assertGreater(float(row2["event_age_decay_score"]), 0.0)
            self.assertGreater(float(row2["event_intensity_score"]), 15.0)
            self.assertEqual(float(row2["major_event_count_30d"]), 1.0)
            self.assertGreater(float(row2["major_event_severity_score_30d"]), 0.0)
            self.assertEqual(float(row2["major_event_age_days"]), 6.0)
            self.assertEqual(float(row2["announcement_count_30d"]), 1.0)
            self.assertGreater(float(row2["announcement_keyword_score_30d"]), 0.0)
            self.assertGreater(float(row2["market_momentum_5d"]), 0.0)
            self.assertLessEqual(float(row2["market_drawdown_20d"]), 0.0)

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
            external_dir = root / "external"
            external_dir.mkdir(parents=True, exist_ok=True)
            macro_interest = external_dir / "macro_interest_rate.csv"
            macro_monthly = external_dir / "macro_monthly_indicator.csv"
            events_dir = root / "events"
            events_dir.mkdir(parents=True, exist_ok=True)
            dividend_event = events_dir / "dividend_event.csv"
            major_event_notice = events_dir / "major_event_notice.csv"
            announcement_text = events_dir / "announcement_text.csv"
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
            macro_interest.write_text(
                "source_api,metric_id,metric_name,pub_date,available_date,value,expected_value,previous_value\n"
                "akshare,policy_rate_current,china_policy_rate,2026-03-24,2026-03-25,2.5,0.0,2.4\n",
                encoding="utf-8",
            )
            macro_monthly.write_text(
                "source_api,metric_id,metric_name,pub_date,available_date,value,expected_value,previous_value\n"
                "akshare,cpi_mom,china_cpi_monthly,2026-03-20,2026-03-23,0.8,0.0,0.7\n",
                encoding="utf-8",
            )
            dividend_event.write_text(
                "stock_code,report_period,dividend_type,pub_date,available_date,record_date,ex_date,pay_date,bonus_ratio,transfer_ratio,cash_ratio,plan_text,source_api\n"
                "600000.SH,2025年报,年度分红,2026-03-24,2026-03-25,2026-03-27,2026-03-28,2026-03-30,0,1,2.5,10派2.5元,akshare\n",
                encoding="utf-8",
            )
            major_event_notice.write_text(
                "stock_code,notice_type,pub_date,available_date,title_text,title_length,keyword_score,severity_score,url,source_api\n"
                "600000.SH,重大事项,2025-09-01,2025-09-02,关于重大事项停牌公告,10,1.5,2.5,https://example.com/a,akshare\n",
                encoding="utf-8",
            )
            announcement_text.write_text(
                "stock_code,notice_type,pub_date,available_date,title_text,title_length,keyword_score,url,source_api\n"
                "600000.SH,其他,2026-03-24,2026-03-25,关于分红预案与回购安排的公告,14,1.6,https://example.com/b,akshare\n",
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
                macro_interest_rate_path=macro_interest,
                macro_monthly_path=macro_monthly,
                dividend_event_path=dividend_event,
                major_event_notice_path=major_event_notice,
                announcement_text_path=announcement_text,
                output_path=output_path,
                max_trade_date="2026-03-25",
            )

            content = output_path.read_text(encoding="utf-8")
            self.assertIn("2026-03-25", content)
            self.assertNotIn("2026-03-30", content)
            rows = content.strip().splitlines()
            row = dict(zip(rows[0].split(","), rows[1].split(",")))
            self.assertEqual(float(row["major_event_count_30d"]), 0.0)
            self.assertEqual(float(row["major_event_age_days"]), 0.0)


if __name__ == "__main__":
    unittest.main()
