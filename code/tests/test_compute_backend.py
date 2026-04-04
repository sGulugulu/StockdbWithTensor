from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.compute_backend import compute_abs_contribution, resolve_device


class ComputeBackendTests(unittest.TestCase):
    def test_auto_device_resolves_to_cpu_or_cuda(self) -> None:
        context = resolve_device("auto")
        self.assertIn(context.resolved_device, {"cpu", "cuda"})

    def test_invalid_device_raises(self) -> None:
        with self.assertRaises(ValueError):
            resolve_device("gpu0")

    def test_abs_contribution_preserves_shape(self) -> None:
        context = resolve_device("cpu")
        array = np.array([[[1.0, -2.0], [3.0, -4.0]]], dtype=float)
        contribution = compute_abs_contribution(array, context)
        self.assertEqual(contribution.shape, array.shape)
        self.assertAlmostEqual(float(contribution[:, :, 0].sum()), 1.0)


if __name__ == "__main__":
    unittest.main()
