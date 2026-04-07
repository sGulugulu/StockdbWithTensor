from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_tdx_full_master_base import build_tdx_full_master_base
from data.merge_baostock_master_fields import merge_baostock_master_fields


class FullMasterContractTests(unittest.TestCase):
    def test_build_tdx_full_master_base_derives_preclose_and_pctchg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            raw_path = root / "tdx.csv"
            out_path = root / "base.csv"
            raw_path.write_text(
                "\n".join(
                    [
                        "market,tdx_prefix,stock_code,trade_date,open,high,low,close,amount,volume,source_file",
                        "sh,sh,600000.SH,2024-01-02,10,11,9,10,1000,100,a.day",
                        "sh,sh,600000.SH,2024-01-03,11,12,10,12,1200,110,a.day",
                    ]
                ),
                encoding="utf-8",
            )
            build_tdx_full_master_base(input_path=raw_path, output_path=out_path, adjustflag_value="2")
            content = out_path.read_text(encoding="utf-8")
            self.assertIn("date,code,open,high,low,close,preclose,volume,amount,adjustflag,pctChg,source_price_vendor,source_file", content)
            self.assertIn("2024-01-03,sh.600000,11,12,10,12,10.0000,110,1200,2,20.000000,tongdaxin,a.day", content)

    def test_merge_baostock_master_fields_adds_required_supplement_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            tdx_path = root / "tdx_base.csv"
            baostock_path = root / "baostock.csv"
            out_path = root / "merged.csv"
            tdx_path.write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,pctChg,source_price_vendor,source_file",
                        "2024-01-03,sh.600000,11,12,10,12,10.0000,110,1200,2,20.000000,tongdaxin,a.day",
                    ]
                ),
                encoding="utf-8",
            )
            baostock_path.write_text(
                "\n".join(
                    [
                        "date,code,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2024-01-03,sh.600000,0.22,1,6.4,0.45,1.85,-1.52,0",
                    ]
                ),
                encoding="utf-8",
            )
            merge_baostock_master_fields(
                tdx_base_path=tdx_path,
                baostock_path=baostock_path,
                output_path=out_path,
            )
            content = out_path.read_text(encoding="utf-8")
            self.assertIn("turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST", content)
            self.assertIn("0.22,1,6.4,0.45,1.85,-1.52,0", content)


if __name__ == "__main__":
    unittest.main()
