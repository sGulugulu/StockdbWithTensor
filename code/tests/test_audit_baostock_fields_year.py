from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.audit_baostock_fields_year import audit_baostock_fields_year


class AuditBaostockFieldsYearTests(unittest.TestCase):
    def test_audit_reports_duplicates_and_missing_supplements_on_intersection(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            master_dir = root / "master"
            fields_dir = master_dir / "baostock_fields"
            fields_dir.mkdir(parents=True, exist_ok=True)

            (master_dir / "tdx_full_master_base_2019.csv").write_text(
                "\n".join(
                    [
                        "date,code,close",
                        "2019-01-02,sh.600000,10",
                        "2019-01-03,sh.600000,11",
                    ]
                ),
                encoding="utf-8",
            )
            (fields_dir / "2019.csv").write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2019-01-02,sh.600000,0.1,1,10,1,2,3,0",
                        "2019-01-02,sh.600000,0.2,1,10,1,2,3,0",
                        "2019-01-03,sh.600000,,,,,,,",
                    ]
                ),
                encoding="utf-8",
            )

            result = audit_baostock_fields_year(master_dir=master_dir, year=2019)

            self.assertEqual(result["status"], "ISSUES")
            self.assertEqual(result["intersection_keys"], 2)
            self.assertEqual(result["duplicate_key_count"], 1)
            self.assertEqual(result["missing_field_counts"]["turn"], 1)
            self.assertEqual(result["missing_field_counts"]["isST"], 1)
            self.assertEqual(result["duplicate_keys"][0]["code"], "sh.600000")
            self.assertEqual(result["duplicate_keys"][0]["date"], "2019-01-02")


if __name__ == "__main__":
    unittest.main()
