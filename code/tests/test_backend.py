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
        import httpx
        import anyio

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = ROOT / "configs" / "sample_cn_smoke.yaml"
            config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            config_data["market"]["universe_path"] = str((ROOT / "data" / "sample_csi_a500_history.csv").resolve())
            config_data["data"]["path"] = str((ROOT / "data" / "sample_a_share_factors.csv").resolve())
            temp_config = Path(temp_dir) / "api_config.yaml"
            temp_config.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")

            async def run_case() -> None:
                app = create_app(output_root=Path(temp_dir), default_config_path=temp_config)
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.post(
                        "/api/runs",
                        json={"run_id": "api_test_run", "run_sync": False, "config_path": str(temp_config)},
                        timeout=60.0,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(response.json()["status"], {"queued", "running", "completed"})

                    detail_payload = None
                    for _ in range(50):
                        response = await client.get("/api/runs/api_test_run", timeout=10.0)
                        detail_payload = response.json()
                        if detail_payload["status"]["status"] == "completed":
                            break
                        await anyio.sleep(0.1)
                    self.assertIsNotNone(detail_payload)
                    self.assertEqual(detail_payload["status"]["status"], "completed")

                    response = await client.get("/api/runs", timeout=10.0)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(any(run["run_id"] == "api_test_run" for run in response.json()))

                    response = await client.get("/api/runs/api_test_run", timeout=10.0)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["status"]["status"], "completed")
                    self.assertIn("factor_associations", response.json())

                    response = await client.get("/api/markets", timeout=10.0)
                    self.assertEqual(response.status_code, 200)
                    market_payload = response.json()
                    option_ids = [item["option_id"] for item in market_payload]
                    self.assertEqual(len(option_ids), len(set(option_ids)))
                    self.assertTrue(any(item["config_profile"] == "formal_hs300" for item in market_payload))

                    response = await client.get(
                        "/api/runs/api_test_run/selection",
                        params={"trade_date": "2026-01-09", "top_n": 2},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertLessEqual(len(response.json()), 2)
                    self.assertEqual(response.json()[0]["model_count"], 3)

                    queued_dir = Path(temp_dir) / "queued_run"
                    queued_dir.mkdir(parents=True, exist_ok=True)
                    (queued_dir / "run_status.json").write_text(
                        '{"run_id":"queued_run","status":"queued","created_at":"x","updated_at":"x"}',
                        encoding="utf-8",
                    )
                    response = await client.get("/api/runs/queued_run/metrics", timeout=10.0)
                    self.assertEqual(response.status_code, 409)

                    response = await client.post(
                        "/api/runs",
                        json={
                            "run_id": "api_test_run_override",
                            "run_sync": False,
                            "market_id": "us_equity",
                            "selection_top_n": 7,
                            "models_enabled": {"cp": True, "tucker": False, "pca": True},
                            "model_ranks": {"cp": [2], "pca": [2]},
                        },
                        timeout=60.0,
                    )
                    self.assertEqual(response.status_code, 200)
                    detail = None
                    for _ in range(50):
                        response = await client.get("/api/runs/api_test_run_override", timeout=10.0)
                        detail = response.json()
                        if detail["status"]["status"] == "completed":
                            break
                        await anyio.sleep(0.1)
                    self.assertIsNotNone(detail)
                    self.assertEqual(detail["manifest"]["market_id"], "us_equity")
                    self.assertEqual(detail["manifest"]["selection_top_n"], 7)

                    response = await client.post(
                        "/api/runs",
                        json={
                            "run_id": "formal_hs300_config_check",
                            "run_sync": False,
                            "config_profile": "formal_hs300",
                            "market_id": "cn_a",
                            "universe_id": "CSI_A500",
                            "start_date": "2015-01-01",
                            "end_date": "2026-12-31",
                        },
                        timeout=60.0,
                    )
                    self.assertEqual(response.status_code, 200)
                    submitted_config = yaml.safe_load(
                        (Path(temp_dir) / "formal_hs300_config_check" / "submitted_config.yaml").read_text(encoding="utf-8")
                    )
                    self.assertEqual(submitted_config["market"]["universe_id"], "HS300")
                    self.assertEqual(submitted_config["output"]["root_dir"], "..")
                    self.assertTrue(str(submitted_config["market"]["universe_path"]).endswith("hs300_history.csv"))
                    self.assertTrue(str(submitted_config["data"]["path"]).endswith("hs300_factor_panel.csv"))

                    formal_history = ROOT / "data" / "formal" / "hs300_history.csv"
                    formal_panel = ROOT / "data" / "formal" / "hs300_factor_panel.csv"
                    if formal_history.exists() and formal_panel.exists():
                        response = await client.post(
                            "/api/runs",
                            json={
                                "run_id": "formal_hs300_real_run",
                                "run_sync": False,
                                "config_profile": "formal_hs300",
                            },
                            timeout=60.0,
                        )
                        self.assertEqual(response.status_code, 200)
                        formal_detail = None
                        for _ in range(200):
                            response = await client.get("/api/runs/formal_hs300_real_run", timeout=10.0)
                            formal_detail = response.json()
                            if formal_detail["status"]["status"] == "completed":
                                break
                            await anyio.sleep(0.1)
                        self.assertIsNotNone(formal_detail)
                        self.assertEqual(formal_detail["status"]["status"], "completed")

                    formal_profiles = [
                        ("formal_sz50", "SZ50"),
                        ("formal_zz500", "ZZ500"),
                    ]
                    for profile_name, universe_id in formal_profiles:
                        formal_history = ROOT / "data" / "formal" / f"{universe_id.lower()}_history.csv"
                        formal_panel = ROOT / "data" / "formal" / f"{universe_id.lower()}_factor_panel.csv"
                        if not formal_history.exists() or not formal_panel.exists():
                            continue
                        run_id = f"{profile_name}_real_run"
                        response = await client.post(
                            "/api/runs",
                            json={
                                "run_id": run_id,
                                "run_sync": False,
                                "config_profile": profile_name,
                            },
                            timeout=60.0,
                        )
                        self.assertEqual(response.status_code, 200)
                        detail_payload = None
                        for _ in range(200):
                            response = await client.get(f"/api/runs/{run_id}", timeout=10.0)
                            detail_payload = response.json()
                            if detail_payload["status"]["status"] == "completed":
                                break
                            await anyio.sleep(0.1)
                        self.assertIsNotNone(detail_payload)
                        self.assertEqual(detail_payload["status"]["status"], "completed")
                        self.assertEqual(detail_payload["manifest"]["universe_id"], universe_id)
                        submitted_config = yaml.safe_load(
                            (Path(temp_dir) / run_id / "submitted_config.yaml").read_text(encoding="utf-8")
                        )
                        self.assertEqual(submitted_config["market"]["universe_id"], universe_id)
                        self.assertEqual(submitted_config["output"]["root_dir"], "..")
                        self.assertTrue(
                            str(submitted_config["market"]["universe_path"]).endswith(
                                f"{universe_id.lower()}_history.csv"
                            )
                        )
                        self.assertTrue(
                            str(submitted_config["data"]["path"]).endswith(
                                f"{universe_id.lower()}_factor_panel.csv"
                            )
                        )

            anyio.run(run_case)


if __name__ == "__main__":
    unittest.main()
