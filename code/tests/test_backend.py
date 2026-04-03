from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from web.backend.app import create_app


ROOT = Path(__file__).resolve().parents[1]


class BackendTests(unittest.TestCase):
    @unittest.skipUnless(__import__("importlib").util.find_spec("fastapi") is not None, "fastapi not installed")
    def test_run_api_and_selection_routes(self) -> None:
        from fastapi.testclient import TestClient

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = ROOT / "configs" / "sample_cn_smoke.yaml"
            config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            config_data["market"]["universe_path"] = str((ROOT / "data" / "sample_csi_a500_history.csv").resolve())
            config_data["data"]["path"] = str((ROOT / "data" / "sample_a_share_factors.csv").resolve())
            temp_config = Path(temp_dir) / "api_config.yaml"
            temp_config.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")

            app = create_app(output_root=Path(temp_dir), default_config_path=temp_config)
            with TestClient(app) as client:
                response = client.post("/api/runs", json={"run_id": "api_test_run", "run_sync": True})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "completed")

                response = client.get("/api/runs")
                self.assertEqual(response.status_code, 200)
                self.assertTrue(any(run["run_id"] == "api_test_run" for run in response.json()))

                response = client.get("/api/runs/api_test_run")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"]["status"], "completed")

                response = client.get("/api/runs/api_test_run/selection", params={"trade_date": "2026-01-09", "top_n": 2})
                self.assertEqual(response.status_code, 200)
                self.assertLessEqual(len(response.json()), 2)
                self.assertEqual(response.json()[0]["model_count"], 3)

                queued_dir = Path(temp_dir) / "queued_run"
                queued_dir.mkdir(parents=True, exist_ok=True)
                (queued_dir / "run_status.json").write_text(
                    '{"run_id":"queued_run","status":"queued","created_at":"x","updated_at":"x"}',
                    encoding="utf-8",
                )
                response = client.get("/api/runs/queued_run/metrics")
                self.assertEqual(response.status_code, 409)

                response = client.post(
                    "/api/runs",
                    json={
                        "run_id": "api_test_run_override",
                        "run_sync": True,
                        "market_id": "cn_a",
                        "universe_id": "CSI_A500",
                        "start_date": "2026-01-02",
                        "end_date": "2026-01-07",
                    },
                )
                self.assertEqual(response.status_code, 200)
                detail = client.get("/api/runs/api_test_run_override").json()
                self.assertEqual(detail["manifest"]["market_id"], "cn_a")
                self.assertEqual(detail["manifest"]["universe_id"], "CSI_A500")
                self.assertEqual(detail["manifest"]["requested_end_date"], "2026-01-07")


if __name__ == "__main__":
    unittest.main()
