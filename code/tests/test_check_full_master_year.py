from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.check_full_master_year import check_full_master_year


class CheckFullMasterYearTests(unittest.TestCase):
    def test_check_full_master_year_reports_ok_when_fields_are_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            master = root / "master"
            master.mkdir(parents=True, exist_ok=True)
            csv_path = master / "full_master_2015.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2015-01-05,sh.600000,1,1,6,1,2,3,0",
                        "2015-12-31,sz.000001,1,1,7,1,2,3,0",
                    ]
                ),
                encoding="utf-8",
            )
            result = check_full_master_year(master_dir=master, year=2015, output_path=master / "check.json")
            self.assertEqual(result["status"], "OK")
            self.assertEqual(result["rows"], 2)
            self.assertEqual(result["stock_count"], 2)
            self.assertEqual(result["min_date"], "2015-01-05")
            self.assertEqual(result["max_date"], "2015-12-31")
            self.assertEqual(json.loads((master / "check.json").read_text(encoding="utf-8"))["status"], "OK")

    def test_check_full_master_year_reports_issues_for_missing_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            master = root / "master"
            master.mkdir(parents=True, exist_ok=True)
            csv_path = master / "full_master_2015.csv"
            csv_path.write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2015-01-05,sh.600000,,,,,,,",
                    ]
                ),
                encoding="utf-8",
            )
            result = check_full_master_year(master_dir=master, year=2015)
            self.assertEqual(result["status"], "ISSUES")
            self.assertTrue(any("补字段非空率过低" in issue for issue in result["issues"]))


if __name__ == "__main__":
    unittest.main()
