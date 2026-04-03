from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import load_config
from stock_tensor.market import SymbolNormalizer, create_market_adapter


ROOT = Path(__file__).resolve().parents[1]


class MarketTests(unittest.TestCase):
    def test_normalize_symbol_supports_cn_a_and_us(self) -> None:
        self.assertEqual(SymbolNormalizer("cn_a").normalize("600000"), "600000.SH")
        self.assertEqual(SymbolNormalizer("cn_a").normalize("000001"), "000001.SZ")
        self.assertEqual(SymbolNormalizer("us_equity").normalize("aapl"), "AAPL")

    def test_universe_provider_filters_records(self) -> None:
        config = load_config(ROOT / "configs" / "default.yaml")
        adapter = create_market_adapter(config.market)
        self.assertIsNotNone(adapter.universe_provider)
        records = adapter.load_records(config.data)
        filtered_records, _, _ = adapter.filter_records(records)
        self.assertTrue(all(record.stock_code.endswith((".SZ", ".SH")) for record in filtered_records))
        self.assertLess(len(filtered_records), len(records))


if __name__ == "__main__":
    unittest.main()
