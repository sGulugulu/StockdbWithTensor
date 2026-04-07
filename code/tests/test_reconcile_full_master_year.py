from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.reconcile_full_master_year import reconcile_full_master_year


class ReconcileFullMasterYearTests(unittest.TestCase):
    def test_reconcile_full_master_year_reports_missing_keys(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            master = root / "master"
            (master / "baostock_fields").mkdir(parents=True, exist_ok=True)

            (master / "tdx_full_master_base_2019.csv").write_text(
                "\n".join(
                    [
                        "date,code,close",
                        "2019-01-02,sh.600000,10",
                        "2019-01-03,sh.600000,11",
                    ]
                ),
                encoding="utf-8",
            )
            (master / "baostock_fields" / "2019.csv").write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2019-01-02,sh.600000,0.2,1,6,1,2,3,0",
                    ]
                ),
                encoding="utf-8",
            )
            (master / "full_master_2019.csv").write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2019-01-02,sh.600000,0.2,1,6,1,2,3,0",
                        "2019-01-03,sh.600000,,,,,,,",
                    ]
                ),
                encoding="utf-8",
            )

            output_path = master / "logs" / "full_master_2019_reconcile.log"
            report = reconcile_full_master_year(master_dir=master, year=2019, output_path=output_path)
            self.assertIn("tdx_minus_baostock=1", report)
            self.assertIn("[all-missing-from-baostock-by-code]", report)
            self.assertIn("sh.600000: 1", report)
            self.assertIn("[all-missing-from-baostock-by-date]", report)
            self.assertIn("2019-01-03: 1", report)
            self.assertIn("ISSUES", report)
            self.assertTrue(output_path.exists())

    def test_reconcile_full_master_year_reports_ok_when_sets_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            master = root / "master"
            (master / "baostock_fields").mkdir(parents=True, exist_ok=True)

            content = "\n".join(
                [
                    "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                    "2019-01-02,sh.600000,0.2,1,6,1,2,3,0",
                ]
            )
            (master / "tdx_full_master_base_2019.csv").write_text(
                "date,code,close\n2019-01-02,sh.600000,10\n",
                encoding="utf-8",
            )
            (master / "baostock_fields" / "2019.csv").write_text(content, encoding="utf-8")
            (master / "full_master_2019.csv").write_text(content, encoding="utf-8")
            report = reconcile_full_master_year(master_dir=master, year=2019)
            self.assertIn("[status]\nOK", report)

    def test_reconcile_full_master_year_reports_extra_baostock_keys_in_full_lists(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            master = root / "master"
            (master / "baostock_fields").mkdir(parents=True, exist_ok=True)

            (master / "tdx_full_master_base_2024.csv").write_text(
                "\n".join(
                    [
                        "date,code,close",
                        "2024-01-02,sh.600000,10",
                    ]
                ),
                encoding="utf-8",
            )
            (master / "baostock_fields" / "2024.csv").write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2024-01-02,sh.600000,0.2,1,6,1,2,3,0",
                        "2024-01-03,sz.000001,0.3,1,7,2,3,4,0",
                    ]
                ),
                encoding="utf-8",
            )
            (master / "full_master_2024.csv").write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2024-01-02,sh.600000,0.2,1,6,1,2,3,0",
                    ]
                ),
                encoding="utf-8",
            )

            report = reconcile_full_master_year(master_dir=master, year=2024)
            self.assertIn("[all-extra-in-baostock-by-code]", report)
            self.assertIn("sz.000001: 1", report)
            self.assertIn("[all-extra-in-baostock-by-date]", report)
            self.assertIn("2024-01-03: 1", report)


if __name__ == "__main__":
    unittest.main()
