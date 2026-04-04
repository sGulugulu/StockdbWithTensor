from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.fetch_baostock_data import _derive_change_rows, _iter_quarters


class BaostockFetchTests(unittest.TestCase):
    def test_iter_quarters_covers_full_year_range(self) -> None:
        self.assertEqual(
            _iter_quarters(2024, 2025),
            [
                (2024, 1),
                (2024, 2),
                (2024, 3),
                (2024, 4),
                (2025, 1),
                (2025, 2),
                (2025, 3),
                (2025, 4),
            ],
        )

    def test_derive_change_rows_detects_add_and_remove(self) -> None:
        rows = [
            {"index_id": "hs300", "snapshot_date": "2024-01-02", "effective_date": "2024-01-02", "code": "sh.600000", "code_name": "A"},
            {"index_id": "hs300", "snapshot_date": "2024-01-02", "effective_date": "2024-01-02", "code": "sh.600001", "code_name": "B"},
            {"index_id": "hs300", "snapshot_date": "2024-01-03", "effective_date": "2024-01-03", "code": "sh.600000", "code_name": "A"},
            {"index_id": "hs300", "snapshot_date": "2024-01-03", "effective_date": "2024-01-03", "code": "sh.600002", "code_name": "C"},
        ]
        changes = _derive_change_rows(rows)
        self.assertEqual(len(changes), 4)
        self.assertEqual(changes[0]["change_type"], "add")
        self.assertEqual(changes[1]["change_type"], "add")
        self.assertEqual(changes[2]["change_type"], "add")
        self.assertEqual(changes[3]["change_type"], "remove")
        self.assertEqual(changes[3]["code"], "sh.600001")


if __name__ == "__main__":
    unittest.main()
