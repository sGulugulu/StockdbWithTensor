from pathlib import Path
import csv
from datetime import date, timedelta
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_long_window_factor_panels import build_long_window_factor_panels


def _sample_master_rows(start_date: date, end_date: date) -> list[tuple[int, str]]:
    rows: list[tuple[int, str]] = []
    current = start_date
    close_price = 10
    while current <= end_date:
        if current.weekday() < 5:
            rows.append((close_price, current.isoformat()))
            close_price += 1
        current += timedelta(days=1)
    return rows


def _master_csv_for_year(rows: list[tuple[int, str]], year: int) -> str:
    header = (
        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,pctChg,"
        "source_price_vendor,source_file,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST"
    )
    year_rows = [row for row in rows if row[1].startswith(f"{year}-")]
    body = [
        (
            f"{trade_date},sh.600000,{close_price},{close_price},{close_price},{close_price},"
            f"{close_price - 1},100,1000,2,0,tongdaxin,a,1,1,10,2,3,4,0"
        )
        for close_price, trade_date in year_rows
    ]
    return "\n".join([header, *body])


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

            sample_rows = _sample_master_rows(date(2015, 12, 1), date(2016, 1, 15))
            for year in (2015, 2016):
                (root / "master" / f"full_master_{year}.csv").write_text(
                    _master_csv_for_year(sample_rows, year),
                    encoding="utf-8",
                )

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
            self.assertIn("2015-12-31", dates)
            self.assertIn("2016-01-04", dates)
            self.assertTrue((root / "factors" / "long_window" / "yearly" / "2015" / "all_a_factor_panel_long_window.csv").exists())
            row_by_date = {row["trade_date"]: row for row in rows}
            self.assertNotEqual(float(row_by_date["2015-12-31"]["future_return"]), 0.0)
            self.assertGreater(float(row_by_date["2016-01-04"]["momentum_factor"]), 0.0)


if __name__ == "__main__":
    unittest.main()
