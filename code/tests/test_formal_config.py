from pathlib import Path
import sys
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.pipeline import run_experiment


ROOT = Path(__file__).resolve().parents[1]


class FormalConfigTests(unittest.TestCase):
    def _assert_project_paths_are_relative(self, output_dir: Path) -> None:
        manifest_text = (output_dir / "run_manifest.json").read_text(encoding="utf-8")
        snapshot = yaml.safe_load((output_dir / "config_snapshot.yaml").read_text(encoding="utf-8"))
        run_log = (output_dir / "run.log").read_text(encoding="utf-8")

        self.assertNotIn("/mnt/d/Personal folders/Desktop/宋田琦/毕设", manifest_text)
        self.assertNotIn("/mnt/d/Personal folders/Desktop/宋田琦/毕设", run_log)
        self.assertEqual(snapshot["output"]["root_dir"], "code/outputs")
        self.assertFalse(Path(snapshot["market"]["universe_path"]).is_absolute())
        self.assertFalse(Path(snapshot["data"]["path"]).is_absolute())

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
        self._assert_project_paths_are_relative(output_dir)

    def test_formal_sz50_config_runs_with_committed_local_inputs(self) -> None:
        history_path = ROOT / "data" / "formal" / "sz50_history.csv"
        panel_path = ROOT / "data" / "formal" / "sz50_factor_panel.csv"
        if not history_path.exists() or not panel_path.exists():
            self.skipTest("committed sz50 formal inputs are not available")

        output_dir = run_experiment(ROOT / "configs" / "formal_sz50.yaml")
        self.assertTrue((output_dir / "run_manifest.json").exists())
        self.assertTrue((output_dir / "selection_candidates.json").exists())
        self._assert_project_paths_are_relative(output_dir)

    def test_formal_zz500_config_runs_with_committed_local_inputs(self) -> None:
        history_path = ROOT / "data" / "formal" / "zz500_history.csv"
        panel_path = ROOT / "data" / "formal" / "zz500_factor_panel.csv"
        if not history_path.exists() or not panel_path.exists():
            self.skipTest("committed zz500 formal inputs are not available")

        output_dir = run_experiment(ROOT / "configs" / "formal_zz500.yaml")
        self.assertTrue((output_dir / "run_manifest.json").exists())
        self.assertTrue((output_dir / "selection_candidates.json").exists())
        self._assert_project_paths_are_relative(output_dir)


if __name__ == "__main__":
    unittest.main()
