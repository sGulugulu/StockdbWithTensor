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


if __name__ == "__main__":
    unittest.main()
