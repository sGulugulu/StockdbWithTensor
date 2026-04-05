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
        self.assertEqual(config.market.end_date, "2026-04-01")
        self.assertIn("universes/hs300_history.csv", str(config.market.universe_path).replace("\\", "/"))
        self.assertIn("factors/hs300_factor_panel.csv", str(config.data.path).replace("\\", "/"))

    def test_formal_sz50_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_sz50.yaml")
        self.assertEqual(config.market.universe_id, "SZ50")
        self.assertEqual(config.market.end_date, "2026-04-01")
        self.assertIn("universes/sz50_history.csv", str(config.market.universe_path).replace("\\", "/"))
        self.assertIn("factors/sz50_factor_panel.csv", str(config.data.path).replace("\\", "/"))

    def test_formal_zz500_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_zz500.yaml")
        self.assertEqual(config.market.universe_id, "ZZ500")
        self.assertEqual(config.market.end_date, "2026-04-01")
        self.assertIn("universes/zz500_history.csv", str(config.market.universe_path).replace("\\", "/"))
        self.assertIn("factors/zz500_factor_panel.csv", str(config.data.path).replace("\\", "/"))


if __name__ == "__main__":
    unittest.main()
