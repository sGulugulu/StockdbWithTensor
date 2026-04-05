from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.year_windows import iter_year_date_ranges


class YearWindowsTests(unittest.TestCase):
    def test_iter_year_date_ranges_splits_multi_year_window(self) -> None:
        self.assertEqual(
            iter_year_date_ranges("2024-12-30", "2026-01-02"),
            [
                ("2024-12-30", "2024-12-31", 2024),
                ("2025-01-01", "2025-12-31", 2025),
                ("2026-01-01", "2026-01-02", 2026),
            ],
        )

    def test_iter_year_date_ranges_keeps_single_year_window(self) -> None:
        self.assertEqual(
            iter_year_date_ranges("2026-03-01", "2026-04-01"),
            [("2026-03-01", "2026-04-01", 2026)],
        )


if __name__ == "__main__":
    unittest.main()
