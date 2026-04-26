from pathlib import Path
import json
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_pattern_discovery_assets import build_pattern_discovery_assets


class PatternDiscoveryAssetsTests(unittest.TestCase):
    def test_build_pattern_discovery_assets_writes_svg_and_summary_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            panel_path = root / "factor_panel.csv"
            output_a = root / "formal_all_a_run"
            output_b = root / "formal_hs300_run"
            report_dir = root / "reports"
            output_a.mkdir()
            output_b.mkdir()
            panel_path.write_text(
                "\n".join(
                    [
                        "stock_code,trade_date,industry,value_factor,momentum_factor,quality_factor,volatility_factor,future_return",
                        "600000.SH,2026-03-30,J66货币金融服务,1,2,3,4,0.01",
                        "600001.SH,2026-03-30,C39电子,1,2,3,4,0.02",
                        "600002.SH,2026-03-30,C39电子,1,2,3,4,0.03",
                    ]
                ),
                encoding="utf-8",
            )
            (output_a / "config_snapshot.yaml").write_text(
                yaml.safe_dump({"data": {"path": str(panel_path)}}, allow_unicode=True),
                encoding="utf-8",
            )
            (output_a / "selection_tucker.json").write_text(
                json.dumps(
                    [
                        {"stock_code": "600000.SH", "cluster_label": 0, "total_score": 1.0},
                        {"stock_code": "600001.SH", "cluster_label": 1, "total_score": 1.2},
                        {"stock_code": "600002.SH", "cluster_label": 1, "total_score": 0.8},
                    ],
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            for output_dir, universe_id, rank_ic, nav in (
                (output_a, "ALL_A_ACTIVE", 0.05, 1.03),
                (output_b, "HS300", 0.02, 1.01),
            ):
                (output_dir / "run_manifest.json").write_text(
                    json.dumps({"market": {"universe_id": universe_id}}, ensure_ascii=False),
                    encoding="utf-8",
                )
                (output_dir / "metrics.json").write_text(
                    json.dumps(
                        [{"model": "tucker", "rank_ic_mean": rank_ic, "rolling_stability": 0.9}],
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )
                (output_dir / "group_returns_tucker.json").write_text(
                    json.dumps([{"trade_date": "2026-03-30", "cumulative_nav": nav}], ensure_ascii=False),
                    encoding="utf-8",
                )

            result = build_pattern_discovery_assets(
                project_root=root,
                anchor_output_dir=output_a,
                comparison_output_dirs=[output_a, output_b],
                output_dir=report_dir,
            )

            self.assertTrue(result.stock_structure_svg.exists())
            self.assertTrue(result.cluster_industry_svg.exists())
            self.assertTrue(result.boundary_comparison_svg.exists())
            summary = json.loads(result.summary_json.read_text(encoding="utf-8"))
            self.assertEqual(summary["stock_count"], 3)
            self.assertEqual(summary["comparison_run_count"], 2)
            self.assertIn("股票潜在结构图", result.summary_md.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
