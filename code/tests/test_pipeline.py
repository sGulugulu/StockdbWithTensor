from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.pipeline import run_experiment


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_outputs(self) -> None:
        config_path = ROOT / "configs" / "default.yaml"
        config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp_dir:
            config_data["data"]["path"] = str((ROOT / "data" / "sample_a_share_factors.csv").resolve())
            config_data["output"]["root_dir"] = temp_dir
            config_data["output"]["experiment_name"] = "pipeline_test"
            temp_config = Path(temp_dir) / "test_config.yaml"
            temp_config.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")

            output_dir = run_experiment(temp_config)
            self.assertTrue((output_dir / "metrics.csv").exists())
            self.assertTrue((output_dir / "summary.md").exists())
            self.assertTrue((output_dir / "model_explained_variance.svg").exists())


if __name__ == "__main__":
    unittest.main()
