from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import load_config
from stock_tensor.dataset import build_tensor_dataset
from stock_tensor.market import create_market_adapter


ROOT = Path(__file__).resolve().parents[1]


class DatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(ROOT / "configs" / "default.yaml")

    def test_loads_wide_factor_records(self) -> None:
        adapter = create_market_adapter(self.config.market)
        records = adapter.load_records(self.config.data)
        self.assertEqual(len(records), 96)
        self.assertEqual(records[0].stock_code, "000001.SZ")
        self.assertEqual(records[0].factor_name, "value_factor")

    def test_build_tensor_dataset(self) -> None:
        adapter = create_market_adapter(self.config.market)
        records = adapter.load_records(self.config.data)
        filtered_records, actual_start, actual_end = adapter.filter_records(records)
        dataset = build_tensor_dataset(filtered_records, self.config.preprocess)
        self.assertEqual(dataset.tensor.shape, (3, 4, 6))
        self.assertFalse((dataset.tensor != dataset.tensor).any())
        self.assertEqual(dataset.returns.shape, (3, 6))
        self.assertEqual(actual_start, "2026-01-02")
        self.assertEqual(actual_end, "2026-01-09")


if __name__ == "__main__":
    unittest.main()
