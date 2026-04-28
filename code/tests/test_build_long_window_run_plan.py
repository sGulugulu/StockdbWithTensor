from pathlib import Path
import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_long_window_run_plan import build_long_window_run_plan


class BuildLongWindowRunPlanTests(unittest.TestCase):
    def test_build_long_window_run_plan_writes_yearly_commands(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            report_dir = root / "report"
            config = Path("code/configs/formal_all_a.yaml")

            result = build_long_window_run_plan(
                config_paths=[config],
                start_date="2024-06-01",
                end_date="2025-03-31",
                report_dir=report_dir,
            )

            rows = json.loads(result.plan_json.read_text(encoding="utf-8"))
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["start_date"], "2024-06-01")
            self.assertEqual(rows[0]["end_date"], "2024-12-31")
            self.assertEqual(rows[1]["start_date"], "2025-01-01")
            self.assertEqual(rows[1]["end_date"], "2025-03-31")
            self.assertIn("python3 code/main.py --config", rows[0]["command"])
            variant = Path(rows[0]["config_variant"])
            self.assertTrue(variant.exists())
            variant_text = variant.read_text(encoding="utf-8")
            self.assertIn("start_date: 2024-06-01", variant_text)
            self.assertIn("end_date: 2024-12-31", variant_text)
            self.assertIn("experiment_name: formal_all_a_2024_long_window_run", variant_text)
            self.assertIn("universe_path: \"", variant_text)
            self.assertIn("all_a_active_history.csv", variant_text)
            self.assertIn("all_a_factor_panel_long_window.csv", variant_text)
            self.assertIn("csi_a500_index_daily.csv", variant_text)
            self.assertIn("root_dir: \"", variant_text)
            self.assertIn("outputs", variant_text)
            self.assertIn("python3 code/main.py", result.plan_md.read_text(encoding="utf-8"))

    def test_build_long_window_run_plan_prefers_repo_relative_paths_for_report_artifacts(self) -> None:
        temp_parent = Path.cwd() / ".tmp"
        temp_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_parent) as temp_dir:
            report_dir = Path(temp_dir) / "report"
            config = Path("code/configs/formal_all_a.yaml")

            result = build_long_window_run_plan(
                config_paths=[config],
                start_date="2026-01-01",
                end_date="2026-03-31",
                report_dir=report_dir,
            )

            rows = json.loads(result.plan_json.read_text(encoding="utf-8"))
            self.assertEqual(rows[0]["config"], "code/configs/formal_all_a.yaml")
            self.assertFalse(str(rows[0]["config_variant"]).startswith("D:/"))
            self.assertFalse(str(rows[0]["command"]).startswith("python3 code/main.py --config D:/"))
            self.assertIn('python3 code/main.py --config "', rows[0]["command"])
            expected_variant = Path(os.path.relpath(report_dir / "configs" / "formal_all_a_2026_long_window_run.yaml", start=Path.cwd())).as_posix()
            self.assertEqual(rows[0]["config_variant"], expected_variant)
            variant_text = Path(rows[0]["config_variant"]).read_text(encoding="utf-8")
            self.assertIn("factors/long_window/all_a_factor_panel_long_window.csv", variant_text)

    def test_build_long_window_run_plan_rewrites_extended_factor_panel_paths(self) -> None:
        temp_parent = Path.cwd() / ".tmp"
        temp_parent.mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=temp_parent) as temp_dir:
            report_dir = Path(temp_dir) / "report"
            config = Path("code/configs/formal_hs300_extended.yaml")

            result = build_long_window_run_plan(
                config_paths=[config],
                start_date="2026-01-01",
                end_date="2026-03-31",
                report_dir=report_dir,
            )

            rows = json.loads(result.plan_json.read_text(encoding="utf-8"))
            variant_text = Path(rows[0]["config_variant"]).read_text(encoding="utf-8")
            self.assertIn(
                "factors/long_window/hs300_factor_panel_extended_long_window.csv",
                variant_text,
            )


if __name__ == "__main__":
    unittest.main()
