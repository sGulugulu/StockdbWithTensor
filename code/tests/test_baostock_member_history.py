from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_baostock_member_history import build_member_history


class BaostockMemberHistoryTests(unittest.TestCase):
    def test_build_member_history_splits_reentry_intervals(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            snapshot_path = temp_root / "hs300_snapshots.csv"
            snapshot_path.write_text(
                "\n".join(
                    [
                        "index_id,snapshot_date,effective_date,code,code_name",
                        "hs300,2024-01-02,2024-01-02,sh.600000,A",
                        "hs300,2024-01-02,2024-01-02,sh.600001,B",
                        "hs300,2024-01-03,2024-01-03,sh.600002,C",
                        "hs300,2024-01-05,2024-01-05,sh.600000,A",
                        "hs300,2024-01-05,2024-01-05,sh.600002,C",
                    ]
                ),
                encoding="utf-8",
            )
            output_path = temp_root / "hs300_history.csv"
            build_member_history(snapshot_path, output_path)
            lines = output_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 5)
            content = "\n".join(lines)
            self.assertGreaterEqual(content.count("600000"), 2)
            self.assertIn("2024-01-02,2024-01-02", content)
            self.assertIn("2024-01-05,2024-01-05", content)

    def test_build_member_history_keeps_single_interval_for_continuous_membership(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            snapshot_path = temp_root / "zz500_snapshots.csv"
            snapshot_path.write_text(
                "\n".join(
                    [
                        "index_id,snapshot_date,effective_date,code,code_name",
                        "zz500,2024-01-02,2024-01-02,sh.600010,A",
                        "zz500,2024-01-05,2024-01-05,sh.600010,A",
                    ]
                ),
                encoding="utf-8",
            )
            output_path = temp_root / "zz500_history.csv"
            build_member_history(snapshot_path, output_path)
            lines = output_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(lines), 2)


if __name__ == "__main__":
    unittest.main()
