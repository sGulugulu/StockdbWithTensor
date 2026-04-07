from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_full_master_for_year import build_full_master_for_year


class BuildFullMasterForYearTests(unittest.TestCase):
    def test_build_full_master_for_year_creates_three_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tdx_raw = root / "tdx.csv"
            baostock_master = root / "baostock.csv"
            output_dir = root / "master"
            tdx_raw.write_text(
                "\n".join(
                    [
                        "market,tdx_prefix,stock_code,trade_date,open,high,low,close,amount,volume,source_file",
                        "sh,sh,600000.SH,2015-01-05,10,11,9,10,1000,100,a.day",
                        "sh,sh,600000.SH,2015-01-06,11,12,10,12,1200,110,a.day",
                        "sh,sh,600000.SH,2016-01-04,12,13,11,13,1300,120,a.day",
                    ]
                ),
                encoding="utf-8",
            )
            baostock_master.write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2015-01-05,sh.600000,0.22,1,6.4,0.45,1.85,-1.52,0",
                        "2015-01-06,sh.600000,0.23,1,6.5,0.46,1.86,-1.51,0",
                    ]
                ),
                encoding="utf-8",
            )
            slice_path, base_path, full_path = build_full_master_for_year(
                tdx_raw_path=tdx_raw,
                baostock_master_path=baostock_master,
                output_dir=output_dir,
                year=2015,
                adjustflag_value="2",
            )
            self.assertTrue(slice_path.exists())
            self.assertTrue(base_path.exists())
            self.assertTrue(full_path.exists())
            content = full_path.read_text(encoding="utf-8")
            self.assertIn("2015-01-05,sh.600000", content)
            self.assertIn("0.22,1,6.4,0.45,1.85,-1.52,0", content)
            self.assertNotIn("2016-01-04", content)


if __name__ == "__main__":
    unittest.main()
