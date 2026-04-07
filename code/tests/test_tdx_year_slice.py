from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_tdx_year_slice import build_tdx_year_slice


class TdxYearSliceTests(unittest.TestCase):
    def test_build_tdx_year_slice_filters_single_year(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_path = root / "tdx.csv"
            out_path = root / "tdx_2015.csv"
            raw_path.write_text(
                "\n".join(
                    [
                        "market,tdx_prefix,stock_code,trade_date,open,high,low,close,amount,volume,source_file",
                        "sh,sh,600000.SH,2014-12-31,1,1,1,1,1,1,a.day",
                        "sh,sh,600000.SH,2015-01-05,2,2,2,2,2,2,a.day",
                        "sh,sh,600000.SH,2016-01-04,3,3,3,3,3,3,a.day",
                    ]
                ),
                encoding="utf-8",
            )
            build_tdx_year_slice(input_path=raw_path, output_path=out_path, year=2015)
            content = out_path.read_text(encoding="utf-8")
            self.assertIn("2015-01-05", content)
            self.assertNotIn("2014-12-31", content)
            self.assertNotIn("2016-01-04", content)


if __name__ == "__main__":
    unittest.main()
