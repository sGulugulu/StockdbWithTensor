from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .config import SplitConfig
from .dataset import TensorDataset, slice_tensor_dataset


@dataclass(slots=True)
class DatasetPartition:
    name: str
    dataset: TensorDataset
    stock_codes: list[str]
    dates: list[str]


@dataclass(slots=True)
class SplitPlan:
    strategy: str
    metadata: dict[str, object]
    partitions: dict[str, DatasetPartition]


def _allocate_counts(total: int, ratios: tuple[float, float, float]) -> tuple[int, int, int]:
    if total <= 0:
        return 0, 0, 0

    raw_counts = [total * ratio for ratio in ratios]
    counts = [int(count) for count in raw_counts]
    remainder = total - sum(counts)
    ranked = sorted(
        range(len(raw_counts)),
        key=lambda index: (raw_counts[index] - counts[index], -index),
        reverse=True,
    )
    for index in ranked[:remainder]:
        counts[index] += 1

    positive_buckets = [index for index, ratio in enumerate(ratios) if ratio > 0]
    if total >= len(positive_buckets):
        for index in positive_buckets:
            if counts[index] == 0:
                donor = max(range(len(counts)), key=lambda donor_index: counts[donor_index])
                if counts[donor] <= 1:
                    break
                counts[donor] -= 1
                counts[index] += 1
    return counts[0], counts[1], counts[2]


def _split_sequence(items: list[str], ratios: tuple[float, float, float]) -> dict[str, list[str]]:
    train_count, validation_count, test_count = _allocate_counts(len(items), ratios)
    train_items = items[:train_count]
    validation_items = items[train_count:train_count + validation_count]
    test_items = items[train_count + validation_count:train_count + validation_count + test_count]
    return {
        "train": train_items,
        "validation": validation_items,
        "test": test_items,
    }


def describe_splits(
    dataset: TensorDataset,
    config: SplitConfig,
    *,
    label_column: str | None,
) -> dict[str, object]:
    return materialize_splits(dataset, config, label_column=label_column).metadata


def materialize_splits(
    dataset: TensorDataset,
    config: SplitConfig,
    *,
    label_column: str | None,
) -> SplitPlan:
    ratios = (config.train_ratio, config.validation_ratio, config.test_ratio)
    metadata: dict[str, object] = {
        "strategy": config.strategy,
        "ratios": {
            "train": config.train_ratio,
            "validation": config.validation_ratio,
            "test": config.test_ratio,
        },
        "label_column": label_column,
        "label_role": "evaluation_only",
        "input_tensor_excludes_labels": True,
    }

    if config.strategy in {"time", "hybrid"}:
        date_split = _split_sequence(dataset.dates, ratios)
        metadata["date_split"] = {
            key: {"count": len(value), "items": value}
            for key, value in date_split.items()
        }
    else:
        metadata["date_split"] = {
            "train": {"count": len(dataset.dates), "items": dataset.dates},
            "validation": {"count": len(dataset.dates), "items": dataset.dates},
            "test": {"count": len(dataset.dates), "items": dataset.dates},
        }

    if config.strategy in {"stock", "hybrid"}:
        stock_split = _split_sequence(dataset.stock_codes, ratios)
        metadata["stock_split"] = {
            key: {"count": len(value), "items": value}
            for key, value in stock_split.items()
        }
    else:
        metadata["stock_split"] = {
            "train": {"count": len(dataset.stock_codes), "items": dataset.stock_codes},
            "validation": {"count": len(dataset.stock_codes), "items": dataset.stock_codes},
            "test": {"count": len(dataset.stock_codes), "items": dataset.stock_codes},
        }

    partitions: dict[str, DatasetPartition] = {}
    for partition_name in ("train", "validation", "test"):
        stock_codes = list(metadata["stock_split"][partition_name]["items"])
        dates = list(metadata["date_split"][partition_name]["items"])
        partition_dataset = slice_tensor_dataset(
            dataset,
            stock_codes=stock_codes,
            dates=dates,
        )
        label_observation_count = int((~np.isnan(partition_dataset.returns)).sum())
        metadata.setdefault("partitions", {})[partition_name] = {
            "stock_count": len(stock_codes),
            "date_count": len(dates),
            "tensor_shape": list(partition_dataset.tensor.shape),
            "label_observation_count": label_observation_count,
            "stocks": stock_codes,
            "dates": dates,
        }
        partitions[partition_name] = DatasetPartition(
            name=partition_name,
            dataset=partition_dataset,
            stock_codes=stock_codes,
            dates=dates,
        )
    return SplitPlan(
        strategy=config.strategy,
        metadata=metadata,
        partitions=partitions,
    )
