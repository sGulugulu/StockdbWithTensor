from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_formal_extended_sources import build_dividend_rows
from data.build_formal_extended_sources import build_formal_extended_sources
from data.build_formal_extended_sources import build_notice_rows


class FakeDataFrame:
    def __init__(self, rows):
        self._rows = rows

    def to_dict(self, orient: str):
        if orient != "records":
            raise ValueError(orient)
        return list(self._rows)


class FakeAkshare:
    def __init__(self) -> None:
        self.notice_dates: list[str] = []
        self.macro_bank_china_interest_rate = lambda: FakeDataFrame(
            [{"商品": "中国央行决议报告", "日期": "2026-03-24", "今值": 2.5, "预测值": None, "前值": 2.4}]
        )
        self.macro_china_lpr = lambda: FakeDataFrame(
            [{"TRADE_DATE": "2026-03-24", "LPR1Y": 3.1, "LPR5Y": 3.6, "RATE_1": 2.5, "RATE_2": 3.0}]
        )
        macro_df = FakeDataFrame([{"商品": "指标", "日期": "2026-03-20", "今值": 1.1, "预测值": None, "前值": 1.0}])
        self.macro_china_cpi_monthly = lambda: macro_df
        self.macro_china_m2_yearly = lambda: macro_df
        self.macro_china_industrial_production_yoy = lambda: macro_df
        self.macro_china_exports_yoy = lambda: macro_df
        self.macro_china_imports_yoy = lambda: macro_df
        self.stock_dividend_cninfo = lambda symbol: FakeDataFrame(
            [
                {
                    "实施方案公告日期": "2026-03-24",
                    "报告时间": "2025年报",
                    "分红类型": "年度分红",
                    "股权登记日": "2026-03-27",
                    "除权日": "2026-03-28",
                    "派息日": "2026-03-30",
                    "送股比例": 0,
                    "转增比例": 1,
                    "派息比例": 2.5,
                    "实施方案分红说明": "10派2.5元",
                }
            ]
        )

    def stock_notice_report(self, symbol, date):
        self.notice_dates.append(date)
        pub_date = f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        return FakeDataFrame(
            [
                {
                    "代码": "600000",
                    "名称": "浦发银行",
                    "公告标题": "关于重大事项停牌与分红安排的公告",
                    "公告类型": "重大事项",
                    "公告日期": pub_date,
                    "网址": "https://example.com/a",
                },
                {
                    "代码": "600000",
                    "名称": "浦发银行",
                    "公告标题": "关于重大事项停牌与分红安排的公告",
                    "公告类型": "重大事项",
                    "公告日期": pub_date,
                    "网址": "https://example.com/a",
                },
                {
                    "代码": "600000",
                    "名称": "浦发银行",
                    "公告标题": "关于减持事项的法律意见书",
                    "公告类型": "法律意见书",
                    "公告日期": pub_date,
                    "网址": "https://example.com/legal",
                },
            ]
        )


class FailingAkshare:
    def stock_dividend_cninfo(self, symbol):
        raise RuntimeError("api down")

    def stock_notice_report(self, symbol, date):
        raise RuntimeError("api down")


class BuildFormalExtendedSourcesTests(unittest.TestCase):
    @patch("data.build_formal_extended_sources._load_akshare", return_value=FakeAkshare())
    def test_build_formal_extended_sources_writes_normalized_tables(self, _mock_akshare) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "formal"
            (root / "universes").mkdir(parents=True, exist_ok=True)
            (root / "factors").mkdir(parents=True, exist_ok=True)
            for history_name in ("hs300_history.csv", "sz50_history.csv", "zz500_history.csv"):
                (root / "universes" / history_name).write_text(
                    "\n".join(
                        [
                            "market_id,universe_id,stock_code,start_date,end_date",
                            "cn_a,IDX,600000,2026-03-02,2026-03-30",
                        ]
                    ),
                    encoding="utf-8",
                )
            for panel_name in ("hs300_factor_panel.csv", "sz50_factor_panel.csv", "zz500_factor_panel.csv"):
                (root / "factors" / panel_name).write_text(
                    "\n".join(
                        [
                            "stock_code,trade_date,industry,value_factor,momentum_factor,quality_factor,volatility_factor,turn_factor,ps_ttm,future_return",
                            "600000.SH,2026-03-25,Bank,0.5,0.1,0.2,0.3,0.4,1.0,0.02",
                            "600000.SH,2026-03-30,Bank,0.5,0.1,0.2,0.3,0.4,1.0,0.02",
                        ]
                    ),
                    encoding="utf-8",
                )

            result = build_formal_extended_sources(
                formal_root=root,
                max_trade_date="2026-03-30",
                notice_lookback_days=5,
            )

            self.assertTrue(result.macro_interest_rate_path.exists())
            self.assertTrue(result.macro_monthly_path.exists())
            self.assertTrue(result.dividend_events_path.exists())
            self.assertTrue(result.major_event_notice_path.exists())
            self.assertTrue(result.announcement_text_path.exists())
            macro_content = result.macro_interest_rate_path.read_text(encoding="utf-8")
            self.assertIn("policy_rate_current", macro_content)
            dividend_content = result.dividend_events_path.read_text(encoding="utf-8")
            self.assertIn("10派2.5元", dividend_content)
            notice_content = result.major_event_notice_path.read_text(encoding="utf-8")
            self.assertIn("重大事项", notice_content)
            self.assertNotIn("法律意见书", notice_content)
            fake_akshare = _mock_akshare.return_value
            self.assertEqual(notice_content.count("https://example.com/a"), len(fake_akshare.notice_dates))
            self.assertIn("20260321", fake_akshare.notice_dates)
            self.assertIn("20260322", fake_akshare.notice_dates)
            self.assertIn("2026-03-21,2026-03-21", notice_content)

    @patch("data.build_formal_extended_sources._load_akshare", return_value=FailingAkshare())
    def test_build_dividend_rows_fails_fast_on_fetch_error(self, _mock_akshare) -> None:
        with self.assertRaisesRegex(RuntimeError, "600000.SH"):
            build_dividend_rows(symbols=["600000.SH"], trade_dates=["2026-03-25"])

    @patch("data.build_formal_extended_sources._load_akshare", return_value=FailingAkshare())
    def test_build_notice_rows_fails_fast_on_fetch_error(self, _mock_akshare) -> None:
        with self.assertRaisesRegex(RuntimeError, "2026-03-24"):
            build_notice_rows(
                symbols=["600000.SH"],
                trade_dates=["2026-03-25"],
                start_date="2026-03-24",
                end_date="2026-03-24",
            )


if __name__ == "__main__":
    unittest.main()
