from pathlib import Path
from unittest.mock import patch
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.refresh_formal_factor_panels import refresh_formal_factor_panels_with_sources


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
            (root / "baostock" / "reports" / "forecast_report").mkdir(parents=True, exist_ok=True)
            (root / "index_daily").mkdir(parents=True, exist_ok=True)
            (root / "external").mkdir(parents=True, exist_ok=True)
            (root / "events").mkdir(parents=True, exist_ok=True)

            (root / "master" / "shared_kline_panel.csv").write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2026-03-25,sh.600000,1,1,1,10,9,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-03-25,sh.600001,1,1,1,11,10,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                        "2026-03-30,sh.600000,1,1,1,12,10,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-03-30,sh.600001,1,1,1,13,11,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                        "2026-03-31,sh.600000,1,1,1,13,12,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-03-31,sh.600001,1,1,1,14,13,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                        "2026-04-01,sh.600000,1,1,1,14,13,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-04-01,sh.600001,1,1,1,15,14,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                        "2026-04-02,sh.600000,1,1,1,15,14,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-04-02,sh.600001,1,1,1,16,15,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                        "2026-04-03,sh.600000,1,1,1,16,15,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-04-03,sh.600001,1,1,1,17,16,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
                        "2026-04-06,sh.600000,1,1,1,17,16,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-04-06,sh.600001,1,1,1,18,17,100,1000,3,0.1,1,0.02,11,2.5,3.2,4,0",
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
                            "cn_a,IDX,600000,2026-03-25,2026-04-06",
                            "cn_a,IDX,600001,2026-03-25,2026-04-06",
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
            (root / "baostock" / "reports" / "forecast_report" / "2026.csv").write_text(
                "\n".join(
                    [
                        "code,profitForcastExpPubDate,profitForcastExpStatDate,profitForcastType,profitForcastAbstract,profitForcastChgPctUp,profitForcastChgPctDwn,dataset,query_year",
                        "sh.600000,2026-03-26,2025-12-31,预增,预计增长,20,10,forecast_report,2026",
                        "sh.600001,2026-03-26,2025-12-31,预减,预计下降,-10,-20,forecast_report,2026",
                    ]
                ),
                encoding="utf-8",
            )
            for index_name, code in (("hs300_index_daily.csv", "000300.SH"), ("000050_index_daily.csv", "000050.SH"), ("zz500_index_daily.csv", "000905.SH")):
                (root / "index_daily" / index_name).write_text(
                    "\n".join(
                        [
                            "market,tdx_prefix,stock_code,trade_date,open,high,low,close,amount,volume,source_file",
                            f"sh,sh,{code},2026-03-24,100,100,100,104,1400,100,a",
                            f"sh,sh,{code},2026-03-25,100,100,100,105,1500,100,a",
                            f"sh,sh,{code},2026-03-30,100,100,100,106,1600,100,a",
                            f"sh,sh,{code},2026-03-31,100,100,100,107,1700,100,a",
                            f"sh,sh,{code},2026-04-01,100,100,100,108,1800,100,a",
                            f"sh,sh,{code},2026-04-02,100,100,100,109,1900,100,a",
                            f"sh,sh,{code},2026-04-03,100,100,100,110,2000,100,a",
                            f"sh,sh,{code},2026-04-06,100,100,100,111,2100,100,a",
                        ]
                    ),
                    encoding="utf-8",
                )
            (root / "external" / "macro_interest_rate.csv").write_text(
                "\n".join(
                    [
                        "source_api,metric_id,metric_name,pub_date,available_date,value,expected_value,previous_value",
                        "akshare,policy_rate_current,china_policy_rate,2026-03-24,2026-03-25,2.5,0.0,2.4",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "external" / "macro_monthly_indicator.csv").write_text(
                "\n".join(
                    [
                        "source_api,metric_id,metric_name,pub_date,available_date,value,expected_value,previous_value",
                        "akshare,cpi_mom,china_cpi_monthly,2026-03-20,2026-03-25,0.8,0.0,0.7",
                        "akshare,m2_yoy,china_m2_yearly,2026-03-20,2026-03-25,7.1,0.0,7.0",
                        "akshare,industrial_production_yoy,china_industrial_production_yoy,2026-03-20,2026-03-25,5.5,0.0,5.3",
                        "akshare,exports_yoy,china_exports_yoy,2026-03-20,2026-03-25,4.4,0.0,4.1",
                        "akshare,imports_yoy,china_imports_yoy,2026-03-20,2026-03-25,3.3,0.0,3.1",
                        "akshare,lpr_1y,china_lpr_1y,2026-03-24,2026-03-25,3.1,0.0,3.0",
                        "akshare,lpr_5y,china_lpr_5y,2026-03-24,2026-03-25,3.6,0.0,3.5",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "events" / "dividend_event.csv").write_text(
                "\n".join(
                    [
                        "stock_code,report_period,dividend_type,pub_date,available_date,record_date,ex_date,pay_date,bonus_ratio,transfer_ratio,cash_ratio,plan_text,source_api",
                        "600000.SH,2025年报,年度分红,2026-03-24,2026-03-25,2026-03-27,2026-03-28,2026-03-30,0,1,2.5,10派2.5元,akshare",
                        "600001.SH,2025年报,年度分红,2026-03-24,2026-03-25,2026-03-27,2026-03-28,2026-03-30,0,0,1.5,10派1.5元,akshare",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "events" / "major_event_notice.csv").write_text(
                "\n".join(
                    [
                        "stock_code,notice_type,pub_date,available_date,title_text,title_length,keyword_score,severity_score,url,source_api",
                        "600000.SH,重大事项,2026-03-24,2026-03-25,关于重大事项停牌公告,10,1.5,2.5,https://example.com/a,akshare",
                        "600001.SH,重大事项,2026-03-24,2026-03-25,关于重大事项复牌公告,10,1.0,2.0,https://example.com/b,akshare",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "events" / "announcement_text.csv").write_text(
                "\n".join(
                    [
                        "stock_code,notice_type,pub_date,available_date,title_text,title_length,keyword_score,url,source_api",
                        "600000.SH,其他,2026-03-24,2026-03-25,关于分红预案与回购安排的公告,14,1.6,https://example.com/c,akshare",
                        "600001.SH,其他,2026-03-24,2026-03-25,关于重大合同签署进展的公告,13,0.8,https://example.com/d,akshare",
                    ]
                ),
                encoding="utf-8",
            )

            outputs = refresh_formal_factor_panels_with_sources(
                formal_root=root,
                max_trade_date="2026-03-30",
                build_extended_source_tables=False,
            )

            self.assertEqual(len(outputs), 6)
            for output_path in outputs:
                self.assertTrue(output_path.exists())
                content = output_path.read_text(encoding="utf-8")
                self.assertIn("2026-03-30", content)
                self.assertNotIn("2026-04-03", content)
                if "extended" in output_path.name:
                    self.assertIn("market_return_1d", content)
                    self.assertIn("market_drawdown_20d", content)
                    self.assertIn("macro_policy_rate", content)
                    self.assertIn("dividend_cash_ratio", content)
                    self.assertIn("major_event_count_30d", content)
                    self.assertIn("forecast_flag", content)
                    self.assertIn("event_intensity_score", content)

            baseline_rows = (
                root / "factors" / "hs300_factor_panel.csv"
            ).read_text(encoding="utf-8").strip().splitlines()
            header = baseline_rows[0].split(",")
            data_rows = [dict(zip(header, line.split(","))) for line in baseline_rows[1:]]
            tail_rows = [row for row in data_rows if row["trade_date"] >= "2026-03-25"]
            self.assertTrue(tail_rows)
            self.assertTrue(any(abs(float(row["future_return"])) > 0.0 for row in tail_rows))

    @patch("data.refresh_formal_factor_panels.build_formal_extended_sources")
    def test_refresh_formal_factor_panels_builds_baseline_before_extended_sources(self, mock_build_sources) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "formal"
            (root / "master").mkdir(parents=True, exist_ok=True)
            (root / "universes").mkdir(parents=True, exist_ok=True)
            (root / "factors").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "metadata").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "financial").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "reports" / "performance_express_report").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "reports" / "forecast_report").mkdir(parents=True, exist_ok=True)
            (root / "index_daily").mkdir(parents=True, exist_ok=True)

            (root / "master" / "shared_kline_panel.csv").write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2026-03-25,sh.600000,1,1,1,10,9,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2026-03-30,sh.600000,1,1,1,12,10,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                    ]
                ),
                encoding="utf-8",
            )
            (root / "baostock" / "metadata" / "stock_industry.csv").write_text(
                "updateDate,code,code_name,industry,industryClassification\n2026-03-30,sh.600000,浦发银行,J66货币金融服务,证监会行业分类\n",
                encoding="utf-8",
            )
            for history_name in ("hs300_history.csv", "sz50_history.csv", "zz500_history.csv"):
                (root / "universes" / history_name).write_text(
                    "market_id,universe_id,stock_code,start_date,end_date\ncn_a,IDX,600000,2026-03-25,2026-03-30\n",
                    encoding="utf-8",
                )
            (root / "baostock" / "financial" / "profit_data.csv").write_text(
                "code,pubDate,statDate,roeAvg,npMargin,gpMargin,netProfit,epsTTM,MBRevenue,totalShare,liqaShare,dataset,query_year,query_quarter\nsh.600000,2026-03-24,2025-12-31,0.11,0.22,0.33,1,0.44,1,1,1,profit_data,2025,4\n",
                encoding="utf-8",
            )
            (root / "baostock" / "reports" / "performance_express_report" / "2026.csv").write_text(
                "code,performanceExpPubDate,performanceExpStatDate,performanceExpUpdateDate,performanceExpressTotalAsset,performanceExpressNetAsset,performanceExpressEPSChgPct,performanceExpressROEWa,performanceExpressEPSDiluted,performanceExpressGRYOY,performanceExpressOPYOY,dataset,query_year\nsh.600000,2026-03-26,2025-12-31,2026-03-26,1,1,0.55,6.7,1,0.66,0.77,performance_express_report,2026\n",
                encoding="utf-8",
            )
            (root / "baostock" / "reports" / "forecast_report" / "2026.csv").write_text(
                "code,profitForcastExpPubDate,profitForcastExpStatDate,profitForcastType,profitForcastAbstract,profitForcastChgPctUp,profitForcastChgPctDwn,dataset,query_year\nsh.600000,2026-03-26,2025-12-31,预增,预计增长,20,10,forecast_report,2026\n",
                encoding="utf-8",
            )
            for index_name, code in (("hs300_index_daily.csv", "000300.SH"), ("000050_index_daily.csv", "000050.SH"), ("zz500_index_daily.csv", "000905.SH")):
                (root / "index_daily" / index_name).write_text(
                    "\n".join(
                        [
                            "market,tdx_prefix,stock_code,trade_date,open,high,low,close,amount,volume,source_file",
                            f"sh,sh,{code},2026-03-24,100,100,100,104,1400,100,a",
                            f"sh,sh,{code},2026-03-25,100,100,100,105,1500,100,a",
                            f"sh,sh,{code},2026-03-30,100,100,100,106,1600,100,a",
                        ]
                    ),
                    encoding="utf-8",
                )

            def _fake_build_sources(*, formal_root: Path, max_trade_date: str, notice_lookback_days: int = 180):
                self.assertTrue((formal_root / "factors" / "hs300_factor_panel.csv").exists())
                self.assertTrue((formal_root / "factors" / "sz50_factor_panel.csv").exists())
                self.assertTrue((formal_root / "factors" / "zz500_factor_panel.csv").exists())
                (formal_root / "external").mkdir(exist_ok=True)
                (formal_root / "events").mkdir(exist_ok=True)
                (formal_root / "external" / "macro_interest_rate.csv").write_text(
                    "source_api,metric_id,metric_name,pub_date,available_date,value,expected_value,previous_value\n"
                    "akshare,policy_rate_current,china_policy_rate,2026-03-24,2026-03-25,2.5,0.0,2.4\n",
                    encoding="utf-8",
                )
                (formal_root / "external" / "macro_monthly_indicator.csv").write_text(
                    "source_api,metric_id,metric_name,pub_date,available_date,value,expected_value,previous_value\n"
                    "akshare,cpi_mom,china_cpi_monthly,2026-03-20,2026-03-25,0.8,0.0,0.7\n",
                    encoding="utf-8",
                )
                (formal_root / "events" / "dividend_event.csv").write_text(
                    "stock_code,report_period,dividend_type,pub_date,available_date,record_date,ex_date,pay_date,bonus_ratio,transfer_ratio,cash_ratio,plan_text,source_api\n"
                    "600000.SH,2025年报,年度分红,2026-03-24,2026-03-25,2026-03-27,2026-03-28,2026-03-30,0,1,2.5,10派2.5元,akshare\n",
                    encoding="utf-8",
                )
                (formal_root / "events" / "major_event_notice.csv").write_text(
                    "stock_code,notice_type,pub_date,available_date,title_text,title_length,keyword_score,severity_score,url,source_api\n"
                    "600000.SH,重大事项,2026-03-24,2026-03-25,关于重大事项停牌公告,10,1.5,2.5,https://example.com/a,akshare\n",
                    encoding="utf-8",
                )
                (formal_root / "events" / "announcement_text.csv").write_text(
                    "stock_code,notice_type,pub_date,available_date,title_text,title_length,keyword_score,url,source_api\n"
                    "600000.SH,其他,2026-03-24,2026-03-25,关于分红预案与回购安排的公告,14,1.6,https://example.com/b,akshare\n",
                    encoding="utf-8",
                )
                return type(
                    "ExtendedSources",
                    (),
                    {
                        "macro_interest_rate_path": formal_root / "external" / "macro_interest_rate.csv",
                        "macro_monthly_path": formal_root / "external" / "macro_monthly_indicator.csv",
                        "dividend_events_path": formal_root / "events" / "dividend_event.csv",
                        "major_event_notice_path": formal_root / "events" / "major_event_notice.csv",
                        "announcement_text_path": formal_root / "events" / "announcement_text.csv",
                    },
                )()

            mock_build_sources.side_effect = _fake_build_sources

            outputs = refresh_formal_factor_panels_with_sources(
                formal_root=root,
                max_trade_date="2026-03-30",
                build_extended_source_tables=True,
            )

            self.assertEqual(len(outputs), 6)
            self.assertTrue((root / "factors" / "hs300_factor_panel_extended.csv").exists())


if __name__ == "__main__":
    unittest.main()
