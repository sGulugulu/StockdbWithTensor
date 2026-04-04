from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_baostock_member_history import build_member_history


class BaostockMemberHistoryTests(unittest.TestCase):
    def test_build_member_history_collapses_snapshot_dates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            snapshot_path = temp_root / "hs300_snapshots.csv"
            snapshot_path.write_text(
                "\n".join(
                    [
                        "index_id,snapshot_date,effective_date,code,code_name",
                        "hs300,2024-01-02,2024-01-02,sh.600000,A",
                        "hs300,2024-01-03,2024-01-02,sh.600000,A",
                        "hs300,2024-01-02,2024-01-02,sh.600001,B",
                        "hs300,2024-01-03,2024-01-03,sh.600002,C",
                    ]
                ),
                encoding="utf-8",
            )
            output_path = temp_root / "hs300_history.csv"
            build_member_history(snapshot_path, output_path)
            content = output_path.read_text(encoding="utf-8")
            self.assertIn("600000", content)
            self.assertIn("2024-01-02", content)
            self.assertIn("2024-01-03", content)


if __name__ == "__main__":
    unittest.main()
