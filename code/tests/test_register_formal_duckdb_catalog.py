from pathlib import Path
import tempfile
import unittest

sys_path_inserted = False
try:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    sys_path_inserted = True
except Exception:
    pass

from data.register_formal_duckdb_catalog import (
    duckdb_available,
    register_formal_duckdb_catalog,
)


class RegisterFormalDuckdbCatalogTests(unittest.TestCase):
    @unittest.skipUnless(duckdb_available(), "duckdb not installed")
    def test_register_formal_duckdb_catalog_creates_expected_views(self) -> None:
        import duckdb

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir) / "formal"
            (root / "universes").mkdir(parents=True, exist_ok=True)
            (root / "factors").mkdir(parents=True, exist_ok=True)
            (root / "master").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "financial" / "profit_data").mkdir(parents=True, exist_ok=True)
            (root / "baostock" / "reports" / "forecast_report").mkdir(parents=True, exist_ok=True)

            (root / "universes" / "hs300_history.csv").write_text(
                "\n".join(
                    [
                        "market_id,universe_id,stock_code,start_date,end_date",
                        "cn_a,HS300,600000.SH,2026-03-02,2026-03-03",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "factors" / "hs300_factor_panel.csv").write_text(
                "\n".join(
                    [
                        "stock_code,trade_date,industry,value_factor,momentum_factor,quality_factor,volatility_factor,future_return",
                        "600000.SH,2026-03-02,Bank,1,2,3,4,0.1",
                        "600000.SH,2026-03-03,Bank,1,2,3,4,0.2",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "master" / "shared_kline_panel.csv").write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2026-03-02,sh.600000,10,11,9,10,9.8,100,1000,3,0.2,1,2.0,6.4,0.45,1.85,-1.52,0",
                        "2026-03-03,sh.600000,10,11,9,10,9.8,100,1000,3,0.2,1,2.0,6.4,0.45,1.85,-1.52,0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "master" / "full_master_2026.csv").write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,pctChg,source_price_vendor,source_file,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2026-03-02,sh.600000,10,11,9,10,9.8,100,1000,2,2.0,tongdaxin,a.day,0.2,1,6.4,0.45,1.85,-1.52,0",
                        "2026-03-03,sh.600000,10,11,9,10,9.8,100,1000,2,2.0,tongdaxin,a.day,0.2,1,6.4,0.45,1.85,-1.52,0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "baostock" / "financial" / "profit_data" / "2025.csv").write_text(
                "\n".join(
                    [
                        "code,pubDate,statDate,dataset,query_year,query_quarter",
                        "sh.600000,2025-04-30,2025-03-31,profit_data,2025,1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (root / "baostock" / "reports" / "forecast_report" / "2025.csv").write_text(
                "\n".join(
                    [
                        "code,profitForcastExpPubDate,profitForcastExpStatDate,dataset,query_year",
                        "sh.600000,2025-01-21,2024-12-31,forecast_report,2025",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            catalog_path = root / "catalog.duckdb"
            summary = register_formal_duckdb_catalog(formal_root=root, catalog_path=catalog_path)
            self.assertTrue(catalog_path.exists())
            self.assertIn("full_master.daily", summary["registered_objects"])
            self.assertIn("financial.vw_financial_dataset_coverage", summary["registered_objects"])

            connection = duckdb.connect(str(catalog_path))
            try:
                full_master_rows = connection.execute(
                    "SELECT CAST(trade_date AS VARCHAR), stock_code, source_year "
                    "FROM full_master.daily ORDER BY trade_date"
                ).fetchall()
                self.assertEqual(
                    full_master_rows,
                    [("2026-03-02", "600000.SH", "2026"), ("2026-03-03", "600000.SH", "2026")],
                )

                universe_rows = connection.execute(
                    "SELECT CAST(trade_date AS VARCHAR), stock_code "
                    "FROM universes.vw_hs300_on_date ORDER BY trade_date"
                ).fetchall()
                self.assertEqual(universe_rows, [("2026-03-02", "600000.SH"), ("2026-03-03", "600000.SH")])

                factor_coverage = connection.execute(
                    "SELECT universe_id, row_count, stock_count FROM factors.vw_factor_panel_coverage"
                ).fetchall()
                self.assertEqual(factor_coverage, [("HS300", 2, 1)])

                financial_coverage = connection.execute(
                    "SELECT dataset_name, row_count, stock_count, min_query_year, max_query_year "
                    "FROM financial.vw_financial_dataset_coverage"
                ).fetchall()
                self.assertEqual(financial_coverage, [("profit_data", 1, 1, 2025, 2025)])

                report_coverage = connection.execute(
                    "SELECT dataset_name, row_count, stock_count, min_query_year, max_query_year "
                    "FROM reports.vw_report_dataset_coverage"
                ).fetchall()
                self.assertEqual(report_coverage, [("forecast_report", 1, 1, 2025, 2025)])
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
