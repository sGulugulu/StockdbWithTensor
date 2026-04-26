from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_segmented_formal_universes import build_segmented_formal_universes


class SegmentedFormalAssetsTests(unittest.TestCase):
    def test_build_segmented_formal_universes_outputs_all_a_industry_and_size_histories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            all_a_path = root / "all_a.csv"
            industry_path = root / "industry.csv"
            profit_path = root / "profit.csv"
            kline_path = root / "kline.csv"
            output_dir = root / "segmented"

            all_a_path.write_text(
                "\n".join(
                    [
                        "market_id,universe_id,stock_code,start_date,end_date",
                        "cn_a,ALL_A,600000.SH,2026-03-01,2026-04-30",
                        "cn_a,ALL_A,600001.SH,2026-03-01,2026-04-30",
                        "cn_a,ALL_A,600002.SH,2026-03-01,2026-04-30",
                        "cn_a,ALL_A,600003.SH,2026-03-01,2026-04-30",
                    ]
                ),
                encoding="utf-8",
            )
            industry_path.write_text(
                "\n".join(
                    [
                        "updateDate,code,code_name,industry,industryClassification",
                        "2026-03-30,sh.600000,浦发银行,A01农业,证监会行业分类",
                        "2026-03-30,sh.600001,邯郸钢铁,B02采矿业,证监会行业分类",
                        "2026-03-30,sh.600002,齐鲁石化,A01农业,证监会行业分类",
                        "2026-03-30,sh.600003,中信电子,C39电子,证监会行业分类",
                    ]
                ),
                encoding="utf-8",
            )
            profit_path.write_text(
                "\n".join(
                    [
                        "code,pubDate,statDate,liqaShare,totalShare",
                        "sh.600000,2026-03-20,2025-12-31,10,10",
                        "sh.600001,2026-03-20,2025-12-31,20,20",
                        "sh.600002,2026-03-20,2025-12-31,30,30",
                        "sh.600003,2026-03-20,2025-12-31,40,40",
                    ]
                ),
                encoding="utf-8",
            )
            kline_path.write_text(
                "\n".join(
                    [
                        "date,code,close",
                        "2026-03-30,sh.600000,10",
                        "2026-03-30,sh.600001,10",
                        "2026-03-30,sh.600002,10",
                        "2026-03-30,sh.600003,10",
                    ]
                ),
                encoding="utf-8",
            )

            result = build_segmented_formal_universes(
                all_a_history_path=all_a_path,
                industry_path=industry_path,
                profit_data_path=profit_path,
                shared_kline_path=kline_path,
                output_dir=output_dir,
                as_of_date="2026-03-30",
                top_industry_count=2,
            )

            self.assertTrue(result.all_a_history_path.exists())
            self.assertEqual(len(result.industry_history_paths), 2)
            self.assertEqual(len(result.size_history_paths), 3)
            all_a_content = result.all_a_history_path.read_text(encoding="utf-8")
            self.assertIn("ALL_A_ACTIVE", all_a_content)
            self.assertIn("600003.SH", all_a_content)
            size_large = output_dir / "size_large_history.csv"
            self.assertIn("SIZE_LARGE", size_large.read_text(encoding="utf-8"))
            self.assertIn("600003.SH", size_large.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
