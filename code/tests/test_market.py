from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import load_config
from stock_tensor.dataset import filter_records_for_market, load_factor_records
from stock_tensor.market import UniverseProvider, normalize_symbol


ROOT = Path(__file__).resolve().parents[1]


class MarketTests(unittest.TestCase):
    def test_normalize_symbol_supports_cn_a_and_us(self) -> None:
        self.assertEqual(normalize_symbol("600000", "cn_a"), "600000.SH")
        self.assertEqual(normalize_symbol("000001", "cn_a"), "000001.SZ")
        self.assertEqual(normalize_symbol("aapl", "us_equity"), "AAPL")

    def test_universe_provider_filters_records(self) -> None:
        config = load_config(ROOT / "configs" / "default.yaml")
        provider = UniverseProvider.from_config(config.market)
        self.assertIsNotNone(provider)
        records = load_factor_records(config.data, config.market)
        filtered_records, _, _ = filter_records_for_market(records, config.market, provider)
        self.assertTrue(all(record.stock_code.endswith((".SZ", ".SH")) for record in filtered_records))
        self.assertEqual(len(filtered_records), len(records))


if __name__ == "__main__":
    unittest.main()
