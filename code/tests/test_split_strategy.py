from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.config import SplitConfig, load_config
from stock_tensor.dataset import build_raw_tensor_dataset
from stock_tensor.market import create_market_adapter
from stock_tensor.preprocess import apply_preprocess_state, fit_preprocess_state
from stock_tensor.splits import materialize_splits


ROOT = Path(__file__).resolve().parents[1]


class SplitStrategyTests(unittest.TestCase):
    def test_stock_split_preserves_non_train_industries_after_preprocess(self) -> None:
        config = load_config(ROOT / "configs" / "sample_cn_smoke.yaml")
        adapter = create_market_adapter(config.market)
        records = adapter.load_records(config.data)
        filtered_records, _, _ = adapter.filter_records(records)
        raw_dataset = build_raw_tensor_dataset(filtered_records)

        split_config = SplitConfig(strategy="stock", train_ratio=0.5, validation_ratio=0.25, test_ratio=0.25)
        split_plan = materialize_splits(raw_dataset, split_config, label_column=config.data.return_column)
        train_raw_dataset = split_plan.partitions["train"].dataset
        validation_raw_dataset = split_plan.partitions["validation"].dataset

        state, _ = fit_preprocess_state(
            train_raw_dataset.tensor,
            train_raw_dataset.raw_tensor,
            train_raw_dataset.returns,
            train_raw_dataset.stock_codes,
            train_raw_dataset.factor_names,
            train_raw_dataset.dates,
            train_raw_dataset.industries,
            config.preprocess,
        )
        validation_preprocessed = apply_preprocess_state(
            validation_raw_dataset.tensor,
            validation_raw_dataset.raw_tensor,
            validation_raw_dataset.returns,
            validation_raw_dataset.stock_codes,
            validation_raw_dataset.factor_names,
            validation_raw_dataset.dates,
            validation_raw_dataset.industries,
            state,
            config.preprocess,
            partition_name="validation",
        )

        for stock_code in validation_preprocessed.stock_codes:
            self.assertEqual(
                validation_preprocessed.industries[stock_code],
                validation_raw_dataset.industries[stock_code],
            )


if __name__ == "__main__":
    unittest.main()
