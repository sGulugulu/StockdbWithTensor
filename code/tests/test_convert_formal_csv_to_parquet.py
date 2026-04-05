from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.convert_formal_csv_to_parquet import (
    collect_formal_csv_targets,
    convert_formal_csv_to_parquet,
    parquet_engine_available,
    pd,
    summarize_parquet_outputs,
)


class ConvertFormalCsvToParquetTests(unittest.TestCase):
    def test_collect_formal_csv_targets_discovers_structured_csv_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "universes").mkdir(parents=True, exist_ok=True)
            (root / "factors").mkdir(parents=True, exist_ok=True)
            (root / "master").mkdir(parents=True, exist_ok=True)
            (root / "universes" / "hs300_history.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (root / "factors" / "hs300_factor_panel.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            (root / "master" / "shared_kline_panel.csv").write_text("a,b\n1,2\n", encoding="utf-8")
            targets = collect_formal_csv_targets(root)
            target_pairs = [(src.relative_to(root).as_posix(), dst.relative_to(root).as_posix()) for src, dst in targets]
            self.assertEqual(
                target_pairs,
                [
                    ("universes/hs300_history.csv", "parquet/universes/hs300_history.parquet"),
                    ("factors/hs300_factor_panel.csv", "parquet/factors/hs300_factor_panel.parquet"),
                    ("master/shared_kline_panel.csv", "parquet/master/shared_kline_panel.parquet"),
                ],
            )

    @unittest.skipIf(pd is None or not parquet_engine_available(), "pandas/parquet engine not installed")
    def test_convert_formal_csv_to_parquet_writes_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "universes").mkdir(parents=True, exist_ok=True)
            csv_path = root / "universes" / "hs300_history.csv"
            csv_path.write_text("market_id,universe_id,stock_code,start_date,end_date\ncn_a,HS300,600000.SH,2026-03-02,2026-04-01\n", encoding="utf-8")
            converted = convert_formal_csv_to_parquet(formal_root=root, overwrite=True)
            self.assertEqual(len(converted), 1)
            parquet_path = root / "parquet" / "universes" / "hs300_history.parquet"
            self.assertTrue(parquet_path.exists())
            summary = summarize_parquet_outputs(root)
            self.assertEqual(len(summary), 1)
            self.assertTrue(summary[0]["row_count_match"])
            self.assertTrue(summary[0]["column_match"])


if __name__ == "__main__":
    unittest.main()
