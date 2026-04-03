from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import load_config
from stock_tensor.dataset import build_tensor_dataset, load_factor_records


ROOT = Path(__file__).resolve().parents[1]


class DatasetTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = load_config(ROOT / "configs" / "default.yaml")

    def test_loads_wide_factor_records(self) -> None:
        records = load_factor_records(self.config.data)
        self.assertEqual(len(records), 96)
        self.assertEqual(records[0].stock_code, "000001.SZ")
        self.assertEqual(records[0].factor_name, "value_factor")

    def test_build_tensor_dataset(self) -> None:
        records = load_factor_records(self.config.data)
        dataset = build_tensor_dataset(records, self.config.preprocess)
        self.assertEqual(dataset.tensor.shape, (4, 4, 6))
        self.assertFalse((dataset.tensor != dataset.tensor).any())
        self.assertEqual(dataset.returns.shape, (4, 6))


if __name__ == "__main__":
    unittest.main()
