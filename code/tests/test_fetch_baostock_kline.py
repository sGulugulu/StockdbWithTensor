from pathlib import Path
import csv
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data import fetch_baostock_kline


class FetchBaostockKlineTests(unittest.TestCase):
    def test_fetch_kline_panel_skips_codes_baostock_does_not_support(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            codes_path = root / "codes.csv"
            output_path = root / "kline.csv"
            progress_path = root / "progress.json"

            with codes_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=["code"])
                writer.writeheader()
                writer.writerow({"code": "bj.920000"})
                writer.writerow({"code": "sh.600000"})

            queried_codes: list[str] = []

            def fake_query(**kwargs: str) -> list[dict[str, str]]:
                queried_codes.append(kwargs["code"])
                return [
                    {
                        "date": "2024-08-01",
                        "code": kwargs["code"],
                        "close": "10.0",
                    }
                ]

            with (
                mock.patch.object(fetch_baostock_kline, "_safe_login"),
                mock.patch.object(fetch_baostock_kline, "_safe_logout"),
                mock.patch.object(fetch_baostock_kline, "_query_with_relogin", side_effect=fake_query),
            ):
                fetch_baostock_kline.fetch_kline_panel(
                    codes_path=codes_path,
                    output_path=output_path,
                    start_date="2024-08-01",
                    end_date="2024-08-31",
                    fields="date,code,close",
                    frequency="d",
                    adjustflag="2",
                    max_codes=None,
                    batch_size=25,
                    progress_path=progress_path,
                    resume=False,
                    stop_after_batches=None,
                    partition_by_year=False,
                )

            self.assertEqual(queried_codes, ["sh.600000"])
            self.assertTrue(output_path.exists())
            self.assertIn("2024-08-01,sh.600000,10.0", output_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
