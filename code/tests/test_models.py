from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import load_config
from stock_tensor.dataset import build_tensor_dataset, load_factor_records
from stock_tensor.models import fit_cp_model, fit_pca_model, fit_tucker_model


ROOT = Path(__file__).resolve().parents[1]


class ModelTests(unittest.TestCase):
    def setUp(self) -> None:
        config = load_config(ROOT / "configs" / "default.yaml")
        records = load_factor_records(config.data, config.market)
        self.dataset = build_tensor_dataset(records, config.preprocess)
        self.config = config

    def test_cp_model_reconstructs_tensor_shape(self) -> None:
        result = fit_cp_model(
            self.dataset.tensor,
            rank=2,
            max_iter=self.config.models.cp.max_iter,
            tol=self.config.models.cp.tol,
            seed=self.config.models.seed,
        )
        self.assertEqual(result.reconstruction.shape, self.dataset.tensor.shape)
        self.assertEqual(result.factor_loadings.shape[0], len(self.dataset.factor_names))

    def test_tucker_model_reconstructs_tensor_shape(self) -> None:
        result = fit_tucker_model(
            self.dataset.tensor,
            rank=(2, 2, 2),
            max_iter=self.config.models.tucker.max_iter,
            tol=self.config.models.tucker.tol,
        )
        self.assertEqual(result.reconstruction.shape, self.dataset.tensor.shape)
        self.assertEqual(result.time_loadings.shape[0], len(self.dataset.dates))

    def test_pca_model_reconstructs_tensor_shape(self) -> None:
        result = fit_pca_model(self.dataset.tensor, rank=2)
        self.assertEqual(result.reconstruction.shape, self.dataset.tensor.shape)
        self.assertEqual(result.stock_loadings.shape[0], len(self.dataset.stock_codes))


if __name__ == "__main__":
    unittest.main()
