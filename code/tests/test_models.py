from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import load_config
from stock_tensor.compute_backend import resolve_device
from stock_tensor.dataset import build_tensor_dataset
from stock_tensor.market import create_market_adapter
from stock_tensor.models import fit_cp_model, fit_pca_model, fit_tucker_model


ROOT = Path(__file__).resolve().parents[1]


class ModelTests(unittest.TestCase):
    def setUp(self) -> None:
        config = load_config(ROOT / "configs" / "sample_cn_smoke.yaml")
        records = create_market_adapter(config.market).load_records(config.data)
        self.dataset = build_tensor_dataset(records, config.preprocess)
        self.config = config

    def test_cp_model_reconstructs_tensor_shape(self) -> None:
        result = fit_cp_model(
            self.dataset.tensor,
            rank=2,
            max_iter=self.config.models.cp.max_iter,
            tol=self.config.models.cp.tol,
            seed=self.config.models.seed,
            device_context=resolve_device(self.config.runtime.device),
        )
        self.assertEqual(result.reconstruction.shape, self.dataset.tensor.shape)
        self.assertEqual(result.factor_loadings.shape[0], len(self.dataset.factor_names))
        self.assertEqual(result.selection_signal.shape, (len(self.dataset.stock_codes), len(self.dataset.dates)))

    def test_tucker_model_reconstructs_tensor_shape(self) -> None:
        result = fit_tucker_model(
            self.dataset.tensor,
            rank=(2, 2, 2),
            max_iter=self.config.models.tucker.max_iter,
            tol=self.config.models.tucker.tol,
            device_context=resolve_device(self.config.runtime.device),
        )
        self.assertEqual(result.reconstruction.shape, self.dataset.tensor.shape)
        self.assertEqual(result.time_loadings.shape[0], len(self.dataset.dates))
        self.assertEqual(result.time_regime_score.shape[0], len(self.dataset.dates))

    def test_pca_model_reconstructs_tensor_shape(self) -> None:
        result = fit_pca_model(
            self.dataset.tensor,
            rank=2,
            device_context=resolve_device(self.config.runtime.device),
        )
        self.assertEqual(result.reconstruction.shape, self.dataset.tensor.shape)
        self.assertEqual(result.stock_loadings.shape[0], len(self.dataset.stock_codes))
        self.assertEqual(result.stock_cluster.shape[0], len(self.dataset.stock_codes))


if __name__ == "__main__":
    unittest.main()
