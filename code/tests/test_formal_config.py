from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.pipeline import run_experiment


ROOT = Path(__file__).resolve().parents[1]


class FormalConfigTests(unittest.TestCase):
    def test_formal_default_config_fails_without_real_data(self) -> None:
        with self.assertRaises(FileNotFoundError):
            run_experiment(ROOT / "configs" / "default.yaml")

    def test_formal_hs300_config_runs_with_committed_local_inputs(self) -> None:
        history_path = ROOT / "data" / "formal" / "hs300_history.csv"
        panel_path = ROOT / "data" / "formal" / "hs300_factor_panel.csv"
        if not history_path.exists() or not panel_path.exists():
            self.skipTest("committed hs300 formal inputs are not available")

        output_dir = run_experiment(ROOT / "configs" / "formal_hs300.yaml")
        self.assertTrue((output_dir / "run_manifest.json").exists())
        self.assertTrue((output_dir / "selection_candidates.json").exists())

    def test_formal_sz50_config_runs_with_committed_local_inputs(self) -> None:
        history_path = ROOT / "data" / "formal" / "sz50_history.csv"
        panel_path = ROOT / "data" / "formal" / "sz50_factor_panel.csv"
        if not history_path.exists() or not panel_path.exists():
            self.skipTest("committed sz50 formal inputs are not available")

        output_dir = run_experiment(ROOT / "configs" / "formal_sz50.yaml")
        self.assertTrue((output_dir / "run_manifest.json").exists())
        self.assertTrue((output_dir / "selection_candidates.json").exists())


if __name__ == "__main__":
    unittest.main()
