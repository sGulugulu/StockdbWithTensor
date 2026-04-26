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
        self.assertEqual(config.market.end_date, "2026-03-30")
        self.assertIn("universes/hs300_history.csv", str(config.market.universe_path).replace("\\", "/"))
        self.assertIn("factors/hs300_factor_panel.csv", str(config.data.path).replace("\\", "/"))

    def test_formal_sz50_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_sz50.yaml")
        self.assertEqual(config.market.universe_id, "SZ50")
        self.assertEqual(config.market.end_date, "2026-03-30")
        self.assertIn("universes/sz50_history.csv", str(config.market.universe_path).replace("\\", "/"))
        self.assertIn("factors/sz50_factor_panel.csv", str(config.data.path).replace("\\", "/"))

    def test_formal_zz500_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_zz500.yaml")
        self.assertEqual(config.market.universe_id, "ZZ500")
        self.assertEqual(config.market.end_date, "2026-03-30")
        self.assertIn("universes/zz500_history.csv", str(config.market.universe_path).replace("\\", "/"))
        self.assertIn("factors/zz500_factor_panel.csv", str(config.data.path).replace("\\", "/"))
        self.assertIn("index_daily/zz500_index_daily.csv", str(config.evaluation.benchmark_path).replace("\\", "/"))
        if config.evaluation.benchmark_path.exists():
            benchmark_lines = config.evaluation.benchmark_path.read_text(encoding="utf-8").splitlines()
            self.assertGreater(len(benchmark_lines), 1)
            self.assertIn("000905.SH", benchmark_lines[1])

    def test_formal_hs300_extended_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_hs300_extended.yaml")
        self.assertEqual(config.market.universe_id, "HS300")
        self.assertIn("factors/hs300_factor_panel_extended.csv", str(config.data.path).replace("\\", "/"))
        self.assertIn("pit_roe_avg", config.data.factor_columns)
        self.assertIn("market_return_1d", config.data.factor_columns)
        self.assertIn("forecast_flag", config.data.factor_columns)

    def test_formal_sz50_extended_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_sz50_extended.yaml")
        self.assertEqual(config.market.universe_id, "SZ50")
        self.assertIn("factors/sz50_factor_panel_extended.csv", str(config.data.path).replace("\\", "/"))
        self.assertIn("perf_express_flag", config.data.factor_columns)
        self.assertIn("market_momentum_5d", config.data.factor_columns)

    def test_formal_zz500_extended_profile(self) -> None:
        config = load_config(ROOT / "configs" / "formal_zz500_extended.yaml")
        self.assertEqual(config.market.universe_id, "ZZ500")
        self.assertIn("factors/zz500_factor_panel_extended.csv", str(config.data.path).replace("\\", "/"))
        self.assertIn("pit_eps_ttm", config.data.factor_columns)
        self.assertIn("forecast_direction", config.data.factor_columns)
        self.assertIn("index_daily/zz500_index_daily.csv", str(config.evaluation.benchmark_path).replace("\\", "/"))
        if config.evaluation.benchmark_path.exists():
            benchmark_lines = config.evaluation.benchmark_path.read_text(encoding="utf-8").splitlines()
            self.assertGreater(len(benchmark_lines), 1)
            self.assertIn("000905.SH", benchmark_lines[1])


if __name__ == "__main__":
    unittest.main()
