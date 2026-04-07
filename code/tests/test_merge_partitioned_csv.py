from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.merge_partitioned_csv import merge_partitioned_csv


class MergePartitionedCsvTests(unittest.TestCase):
    def test_merge_partitioned_csv_merges_and_sorts_rows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            p1 = root / "a.csv"
            p2 = root / "b.csv"
            out = root / "merged.csv"
            p1.write_text("date,code,turn\n2026-02-01,sh.600000,0.2\n", encoding="utf-8")
            p2.write_text("date,code,turn\n2026-01-01,sh.600000,0.1\n", encoding="utf-8")
            merge_partitioned_csv(
                input_paths=[p1, p2],
                output_path=out,
                sort_keys=["date", "code"],
            )
            lines = out.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(
                lines,
                [
                    "date,code,turn",
                    "2026-01-01,sh.600000,0.1",
                    "2026-02-01,sh.600000,0.2",
                ],
            )

    def test_merge_partitioned_csv_deduplicates_date_code_and_keeps_more_complete_row(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            p1 = root / "a.csv"
            p2 = root / "b.csv"
            out = root / "merged.csv"
            p1.write_text(
                "date,code,turn,peTTM\n2026-02-01,sh.600000,0.2,\n",
                encoding="utf-8",
            )
            p2.write_text(
                "date,code,turn,peTTM\n2026-02-01,sh.600000,0.2,6.4\n",
                encoding="utf-8",
            )
            stats = merge_partitioned_csv(
                input_paths=[p1, p2],
                output_path=out,
                sort_keys=["date", "code"],
            )
            lines = out.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(
                lines,
                [
                    "date,code,turn,peTTM",
                    "2026-02-01,sh.600000,0.2,6.4",
                ],
            )
            self.assertEqual(stats["input_rows"], 2)
            self.assertEqual(stats["output_rows"], 1)
            self.assertEqual(stats["duplicate_keys"], 1)
            self.assertEqual(stats["replaced_with_more_complete"], 1)


if __name__ == "__main__":
    unittest.main()
