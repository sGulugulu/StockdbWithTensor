from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import load_config


ROOT = Path(__file__).resolve().parents[1]


class ConfigProfileTests(unittest.TestCase):
    def test_formal_hs300_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_hs300.yaml")
        self.assertEqual(config.market.universe_id, "HS300")
        self.assertTrue(str(config.market.universe_path).endswith("hs300_history.csv"))

    def test_formal_sz50_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_sz50.yaml")
        self.assertEqual(config.market.universe_id, "SZ50")
        self.assertTrue(str(config.market.universe_path).endswith("sz50_history.csv"))

    def test_formal_zz500_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_zz500.yaml")
        self.assertEqual(config.market.universe_id, "ZZ500")
        self.assertTrue(str(config.market.universe_path).endswith("zz500_history.csv"))


if __name__ == "__main__":
    unittest.main()
