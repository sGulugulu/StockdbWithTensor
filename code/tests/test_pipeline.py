from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from stock_tensor.pipeline import run_experiment
from web.backend.app import get_run_detail, get_selection_for_date


ROOT = Path(__file__).resolve().parents[1]


class PipelineTests(unittest.TestCase):
    def test_pipeline_writes_outputs(self) -> None:
        config_path = ROOT / "configs" / "sample_cn_smoke.yaml"
        config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp_dir:
            config_data["market"]["universe_path"] = str((ROOT / "data" / "sample_csi_a500_history.csv").resolve())
            config_data["data"]["path"] = str((ROOT / "data" / "sample_a_share_factors.csv").resolve())
            config_data["output"]["root_dir"] = temp_dir
            config_data["output"]["experiment_name"] = "pipeline_test"
            temp_config = Path(temp_dir) / "test_config.yaml"
            temp_config.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")

            output_dir = run_experiment(temp_config)
            self.assertTrue((output_dir / "metrics.csv").exists())
            self.assertTrue((output_dir / "summary.md").exists())
            self.assertTrue((output_dir / "model_explained_variance.svg").exists())
            self.assertTrue((output_dir / "run_manifest.json").exists())
            self.assertTrue((output_dir / "selection_cp.json").exists())
            self.assertTrue((output_dir / "selection_candidates.json").exists())
            self.assertTrue((output_dir / "factor_summary_cp.json").exists())
            self.assertTrue((output_dir / "portfolio_metrics.json").exists())
            self.assertTrue((output_dir / "group_returns_cp.json").exists())
            self.assertTrue((output_dir / "drawdown_cp.json").exists())
            self.assertTrue((output_dir / "exposure_cp.json").exists())
            self.assertTrue((output_dir / "group_returns_overview.svg").exists())
            self.assertTrue((output_dir / "drawdown_overview.svg").exists())
            manifest = yaml.safe_load((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["split"]["strategy"], "time")
            self.assertEqual(manifest["split"]["label_role"], "evaluation_only")
            self.assertTrue(manifest["split"]["input_tensor_excludes_labels"])
            portfolio_metrics = yaml.safe_load((output_dir / "portfolio_metrics.json").read_text(encoding="utf-8"))
            self.assertEqual(len(portfolio_metrics), 3)
            self.assertEqual(portfolio_metrics[0]["top_n"], 20)
            metric_by_model = {row["model"]: row for row in portfolio_metrics}
            self.assertEqual(set(metric_by_model), {"cp", "tucker", "pca"})

            for model_name in ("cp", "tucker", "pca"):
                group_returns = yaml.safe_load((output_dir / f"group_returns_{model_name}.json").read_text(encoding="utf-8"))
                drawdowns = yaml.safe_load((output_dir / f"drawdown_{model_name}.json").read_text(encoding="utf-8"))
                self.assertGreater(len(group_returns), 0)
                self.assertEqual(len(group_returns), metric_by_model[model_name]["observation_count"])
                self.assertEqual(group_returns[0]["turnover"], 1.0)
                self.assertEqual(
                    sorted(row["trade_date"] for row in group_returns),
                    [row["trade_date"] for row in group_returns],
                )
                self.assertAlmostEqual(
                    group_returns[-1]["cumulative_nav"] - 1.0,
                    metric_by_model[model_name]["cumulative_return"],
                    places=6,
                )
                self.assertAlmostEqual(
                    min(row["drawdown"] for row in drawdowns),
                    metric_by_model[model_name]["max_drawdown"],
                    places=6,
                )
                for row in group_returns:
                    self.assertEqual(row["model"], model_name)
                    self.assertEqual(set(row.keys()), {
                        "trade_date",
                        "model",
                        "top_n",
                        "daily_return",
                        "cumulative_nav",
                        "turnover",
                        "drawdown",
                    })
                for row in drawdowns:
                    self.assertEqual(row["model"], model_name)
                    self.assertEqual(set(row.keys()), {"trade_date", "model", "cumulative_nav", "drawdown"})

            detail = get_run_detail(Path(temp_dir), "pipeline_test")
            self.assertEqual(detail["manifest"]["market_id"], "cn_a")
            self.assertEqual(detail["status"]["status"], "unknown")
            selections = get_selection_for_date(Path(temp_dir), "pipeline_test", "2026-01-09", 3)
            self.assertEqual(len(selections), 3)
            self.assertIn("stock_code", selections[0])
            self.assertIn("cluster_label", selections[0])
            self.assertEqual(selections[0]["model_count"], 3)

    def test_pipeline_selection_top_n_truncates_candidate_pool_per_date(self) -> None:
        config_path = ROOT / "configs" / "sample_cn_smoke.yaml"
        config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))

        with tempfile.TemporaryDirectory() as temp_dir:
            config_data["market"]["universe_path"] = str((ROOT / "data" / "sample_csi_a500_history.csv").resolve())
            config_data["data"]["path"] = str((ROOT / "data" / "sample_a_share_factors.csv").resolve())
            config_data["output"]["root_dir"] = temp_dir
            config_data["output"]["experiment_name"] = "pipeline_topn_test"
            config_data["runtime"]["selection_top_n"] = 1
            temp_config = Path(temp_dir) / "topn_config.yaml"
            temp_config.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")

            output_dir = run_experiment(temp_config)
            candidate_rows = yaml.safe_load((output_dir / "selection_candidates.json").read_text(encoding="utf-8"))
            trade_dates = {row["trade_date"] for row in candidate_rows}
            self.assertEqual(len(candidate_rows), len(trade_dates))
            selections = get_selection_for_date(Path(temp_dir), "pipeline_topn_test", sorted(trade_dates)[0], 5)
            self.assertEqual(len(selections), 1)


if __name__ == "__main__":
    unittest.main()
