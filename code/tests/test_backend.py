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
        import os
        import socket
        import subprocess
        import time

        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = ROOT / "configs" / "sample_cn_smoke.yaml"
            config_data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
            config_data["market"]["universe_path"] = str((ROOT / "data" / "sample_csi_a500_history.csv").resolve())
            config_data["data"]["path"] = str((ROOT / "data" / "sample_a_share_factors.csv").resolve())
            temp_config = Path(temp_dir) / "api_config.yaml"
            temp_config.write_text(yaml.safe_dump(config_data, sort_keys=False), encoding="utf-8")
            sock = socket.socket()
            sock.bind(("127.0.0.1", 0))
            port = sock.getsockname()[1]
            sock.close()

            env = dict(os.environ)
            env["PYTHONPATH"] = str(ROOT.parent / "code")
            env["OUTPUT_ROOT"] = temp_dir
            env["DEFAULT_CONFIG_PATH"] = str(temp_config)

            process = subprocess.Popen(
                [
                    str(ROOT.parent / ".venv" / "bin" / "python"),
                    "-m",
                    "uvicorn",
                    "web.backend.app:create_app",
                    "--factory",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    str(port),
                ],
                cwd=str(ROOT.parent),
                env=env,
            )
            try:
                ready = False
                for _ in range(30):
                    try:
                        response = httpx.get(f"http://127.0.0.1:{port}/api/markets", timeout=2.0)
                        if response.status_code == 200:
                            ready = True
                            break
                    except Exception:
                        time.sleep(0.5)
                self.assertTrue(ready)

                response = httpx.post(
                    f"http://127.0.0.1:{port}/api/runs",
                    json={"run_id": "api_test_run", "run_sync": True, "config_path": str(temp_config)},
                    timeout=60.0,
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"], "completed")

                response = httpx.get(f"http://127.0.0.1:{port}/api/runs", timeout=10.0)
                self.assertEqual(response.status_code, 200)
                self.assertTrue(any(run["run_id"] == "api_test_run" for run in response.json()))

                response = httpx.get(f"http://127.0.0.1:{port}/api/runs/api_test_run", timeout=10.0)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json()["status"]["status"], "completed")

                response = httpx.get(
                    f"http://127.0.0.1:{port}/api/runs/api_test_run/selection",
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
                response = httpx.get(f"http://127.0.0.1:{port}/api/runs/queued_run/metrics", timeout=10.0)
                self.assertEqual(response.status_code, 409)

                response = httpx.post(
                    f"http://127.0.0.1:{port}/api/runs",
                    json={
                        "run_id": "api_test_run_override",
                        "run_sync": True,
                        "market_id": "us_equity",
                        "selection_top_n": 7,
                        "models_enabled": {"cp": True, "tucker": False, "pca": True},
                        "model_ranks": {"cp": [2], "pca": [2]},
                    },
                    timeout=60.0,
                )
                self.assertEqual(response.status_code, 200)
                detail = httpx.get(f"http://127.0.0.1:{port}/api/runs/api_test_run_override", timeout=10.0).json()
                self.assertEqual(detail["manifest"]["market_id"], "us_equity")
                self.assertEqual(detail["manifest"]["selection_top_n"], 7)
            finally:
                process.terminate()
                process.wait(timeout=10)


if __name__ == "__main__":
    unittest.main()
