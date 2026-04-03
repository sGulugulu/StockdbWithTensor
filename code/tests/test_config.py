from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import load_config


ROOT = Path(__file__).resolve().parents[1]


class ConfigTests(unittest.TestCase):
    def test_load_default_config(self) -> None:
        config = load_config(ROOT / "configs" / "default.yaml")
        self.assertEqual(config.market.market_id, "cn_a")
        self.assertEqual(config.market.universe_id, "CSI_A500")
        self.assertEqual(config.market.start_date, "2015-01-01")
        self.assertEqual(config.data.format, "wide")
        self.assertEqual(config.models.cp.ranks, [2, 3])
        self.assertEqual(config.output.experiment_name, "formal_a_share_run")


if __name__ == "__main__":
    unittest.main()
