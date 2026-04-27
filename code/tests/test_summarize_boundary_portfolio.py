from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.summarize_boundary_portfolio import summarize_boundary_portfolio


class SummarizeBoundaryPortfolioTests(unittest.TestCase):
    def test_summarize_boundary_portfolio_writes_json_and_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            run_dir = root / "formal_all_a_run"
            report_dir = root / "report"
            run_dir.mkdir()
            (run_dir / "run_manifest.json").write_text(
                json.dumps(
                    {
                        "universe_id": "ALL_A_ACTIVE",
                        "actual_start_date": "2026-03-25",
                        "actual_end_date": "2026-03-30",
                        "candidate_pool_size": 20,
                        "selection_top_n": 5,
                    },
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (run_dir / "metrics.json").write_text(
                json.dumps(
                    [
                        {"model": "cp", "rank_ic_mean": -0.1, "rolling_stability": 0.5},
                        {"model": "tucker", "rank_ic_mean": 0.2, "rolling_stability": 0.9},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (run_dir / "portfolio_metrics.json").write_text(
                json.dumps(
                    [
                        {
                            "model": "cp",
                            "cumulative_return": -0.02,
                            "annualized_volatility": 0.1,
                            "sharpe_ratio": -1.0,
                            "max_drawdown": -0.03,
                            "average_turnover": 0.2,
                        },
                        {
                            "model": "tucker",
                            "cumulative_return": 0.05,
                            "annualized_volatility": 0.2,
                            "sharpe_ratio": 2.0,
                            "max_drawdown": -0.01,
                            "average_turnover": 0.3,
                        },
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            (run_dir / "exposure_tucker.json").write_text(
                json.dumps(
                    [
                        {"model": "tucker", "exposure_type": "industry", "name": "C27医药制造业", "weight": 0.4},
                        {"model": "tucker", "exposure_type": "style", "name": "quality_factor", "weight": 1.0},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )

            result = summarize_boundary_portfolio(output_dirs=[run_dir], report_dir=report_dir, exposure_limit=2)

            self.assertTrue(result.summary_json.exists())
            self.assertTrue(result.summary_md.exists())
            summary = json.loads(result.summary_json.read_text(encoding="utf-8"))
            self.assertEqual(summary[0]["best_rank_ic_model"], "tucker")
            self.assertEqual(summary[0]["best_return_model"], "tucker")
            markdown = result.summary_md.read_text(encoding="utf-8")
            self.assertIn("ALL_A_ACTIVE", markdown)
            self.assertIn("C27医药制造业", markdown)
            self.assertIn("quality_factor", markdown)


if __name__ == "__main__":
    unittest.main()
