from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_formal_factor_panel import build_formal_factor_panel


class FormalFactorPanelTests(unittest.TestCase):
    def test_build_formal_factor_panel_outputs_expected_columns(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            kline_path = root / "kline.csv"
            industry_path = root / "industry.csv"
            output_path = root / "factor_panel.csv"

            kline_path.write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2024-01-02,sh.600000,1,1,1,10,9,100,1000,3,0.1,1,0.02,10,2,3,4,0",
                        "2024-01-03,sh.600000,1,1,1,11,10,100,1000,3,0.1,1,0.03,10,2,3,4,0",
                        "2024-01-04,sh.600000,1,1,1,12,11,100,1000,3,0.1,1,0.04,10,2,3,4,0",
                        "2024-01-05,sh.600000,1,1,1,13,12,100,1000,3,0.1,1,0.05,10,2,3,4,0",
                        "2024-01-08,sh.600000,1,1,1,14,13,100,1000,3,0.1,1,0.06,10,2,3,4,0",
                        "2024-01-09,sh.600000,1,1,1,15,14,100,1000,3,0.1,1,0.07,10,2,3,4,0",
                    ]
                ),
                encoding="utf-8",
            )
            industry_path.write_text(
                "\n".join(
                    [
                        "updateDate,code,code_name,industry,industryClassification",
                        "2024-01-09,sh.600000,浦发银行,J66货币金融服务,证监会行业分类",
                    ]
                ),
                encoding="utf-8",
            )

            build_formal_factor_panel(
                kline_path=kline_path,
                industry_path=industry_path,
                output_path=output_path,
            )
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("stock_code", content)
            self.assertIn("value_factor", content)
            self.assertIn("future_return", content)


if __name__ == "__main__":
    unittest.main()
