from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from web.backend.app import create_app
from data.register_formal_duckdb_catalog import register_formal_duckdb_catalog


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
                    initial_status_payload = response.json()

                    detail_payload = None
                    for _ in range(50):
                        response = await client.get("/api/runs/api_test_run", timeout=10.0)
                        detail_payload = response.json()
                        if detail_payload["status"]["status"] == "completed":
                            break
                        await anyio.sleep(0.1)
                    self.assertIsNotNone(detail_payload)
                    self.assertEqual(detail_payload["status"]["status"], "completed")

                    response = await client.post(
                        "/api/runs",
                        json={
                            "run_id": "api_test_run_replay",
                            "run_sync": False,
                            "config_path": initial_status_payload["config_path"],
                        },
                        timeout=60.0,
                    )
                    self.assertEqual(response.status_code, 200)

                    response = await client.get("/api/runs", timeout=10.0)
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(any(run["run_id"] == "api_test_run" for run in response.json()))

                    external_symlink_target = Path(temp_dir).parent / "external_symlink_run_target"
                    external_symlink_target.mkdir(parents=True, exist_ok=True)
                    external_symlink = Path(temp_dir) / "external_symlink_run"
                    if not external_symlink.exists():
                        external_symlink.symlink_to(external_symlink_target, target_is_directory=True)
                    response = await client.get("/api/runs", timeout=10.0)
                    self.assertFalse(any(run["run_id"] == "external_symlink_run" for run in response.json()))

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
                    self.assertFalse(any(item["config_profile"] == "formal_cn_a" for item in market_payload))

                    response = await client.get(
                        "/api/runs/api_test_run/selection",
                        params={"trade_date": "2026-01-09", "top_n": 2},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertLessEqual(len(response.json()), 2)
                    self.assertEqual(response.json()[0]["model_count"], 3)

                    response = await client.get(
                        "/api/runs/api_test_run/selection",
                        params={"trade_date": "2026-01-09", "top_n": 0},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 422)
                    self.assertIn("top_n", response.json()["detail"])

                    response = await client.get("/api/runs/..\\invalid", timeout=10.0)
                    self.assertIn(response.status_code, {404, 422})

                    response = await client.post(
                        "/api/runs",
                        json={"run_id": "..\\invalid", "run_sync": False, "config_path": str(temp_config)},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 422)
                    self.assertIn("run_id", response.json()["detail"])

                    response = await client.post(
                        "/api/runs",
                        json={"run_id": 123, "run_sync": False, "config_path": str(temp_config)},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 422)
                    self.assertIn("run_id", response.json()["detail"])

                    response = await client.post(
                        "/api/runs",
                        json={"run_sync": False, "config_path": False},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 422)
                    self.assertIn("config_path", response.json()["detail"])

                    with tempfile.TemporaryDirectory() as outside_dir:
                        outside_config = Path(outside_dir) / "outside.yaml"
                        outside_config.write_text(
                            yaml.safe_dump(config_data, sort_keys=False),
                            encoding="utf-8",
                        )
                        response = await client.post(
                            "/api/runs",
                            json={
                                "run_id": "blocked_config_run",
                                "run_sync": False,
                                "config_path": str(outside_config),
                            },
                            timeout=10.0,
                        )
                        self.assertEqual(response.status_code, 422)
                        self.assertIn("config_path", response.json()["detail"])
                        self.assertFalse((Path(temp_dir) / "blocked_config_run").exists())

                    response = await client.post(
                        "/api/runs",
                        json={
                            "run_id": "invalid_selection_top_n",
                            "run_sync": False,
                            "config_path": str(temp_config),
                            "selection_top_n": 0,
                        },
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 422)
                    self.assertIn("selection_top_n", response.json()["detail"])
                    self.assertFalse((Path(temp_dir) / "invalid_selection_top_n").exists())

                    relative_variant_config = Path(temp_dir) / "variant.yaml"
                    relative_variant_config.write_text(
                        yaml.safe_dump(config_data, sort_keys=False),
                        encoding="utf-8",
                    )
                    response = await client.post(
                        "/api/runs",
                        json={
                            "run_id": "relative_variant_run",
                            "run_sync": False,
                            "config_path": "variant.yaml",
                        },
                        timeout=60.0,
                    )
                    self.assertEqual(response.status_code, 200)

                    response = await client.post(
                        "/api/runs",
                        json={
                            "run_id": "repo_relative_variant_run",
                            "run_sync": False,
                            "config_path": "code/configs/sample_cn_smoke.yaml",
                        },
                        timeout=60.0,
                    )
                    self.assertEqual(response.status_code, 200)

                    response = await client.post(
                        "/api/runs",
                        json={
                            "run_id": "fractional_selection_top_n",
                            "run_sync": False,
                            "config_path": str(temp_config),
                            "selection_top_n": 1.9,
                        },
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 422)
                    self.assertIn("selection_top_n", response.json()["detail"])
                    self.assertFalse((Path(temp_dir) / "fractional_selection_top_n").exists())

                    queued_dir = Path(temp_dir) / "queued_run"
                    queued_dir.mkdir(parents=True, exist_ok=True)
                    (queued_dir / "run_status.json").write_text(
                        '{"run_id":"queued_run","status":"queued","created_at":"x","updated_at":"x"}',
                        encoding="utf-8",
                    )
                    response = await client.get("/api/runs/queued_run/metrics", timeout=10.0)
                    self.assertEqual(response.status_code, 409)

                    legacy_dir = Path(temp_dir) / "legacy.run"
                    legacy_dir.mkdir(parents=True, exist_ok=True)
                    (legacy_dir / "run_status.json").write_text(
                        '{"run_id":"legacy.run","status":"completed","created_at":"x","updated_at":"x"}',
                        encoding="utf-8",
                    )
                    (legacy_dir / "run_manifest.json").write_text(
                        '{"market_id":"cn_a","universe_id":"HS300","selection_top_n":1}',
                        encoding="utf-8",
                    )
                    (legacy_dir / "metrics.json").write_text(
                        '[{"model":"cp","rank":"2","mse":0.1,"explained_variance":0.9}]',
                        encoding="utf-8",
                    )
                    (legacy_dir / "selection_candidates.json").write_text(
                        '[{"trade_date":"2026-01-09","stock_code":"600000.SH","total_score":0.9,"model_count":1,"cluster_label":"A","top_factor_1":"value","time_regime_score":0.3}]',
                        encoding="utf-8",
                    )
                    response = await client.get("/api/runs/legacy.run", timeout=10.0)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["run_id"], "legacy.run")
                    response = await client.get("/api/runs/%20legacy.run%20", timeout=10.0)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()["run_id"], "legacy.run")
                    response = await client.get(
                        "/api/runs/legacy.run/selection",
                        params={"trade_date": "2026-01-09", "top_n": 1},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(response.json()[0]["stock_code"], "600000.SH")

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
                    self.assertEqual(str(submitted_config["market"]["start_date"]), "2015-01-01")
                    self.assertEqual(str(submitted_config["market"]["end_date"]), "2026-04-01")
                    self.assertEqual(submitted_config["output"]["root_dir"], "..")
                    self.assertTrue(str(submitted_config["market"]["universe_path"]).endswith("universes/hs300_history.csv"))
                    self.assertTrue(str(submitted_config["data"]["path"]).endswith("factors/hs300_factor_panel.csv"))

                    formal_history = ROOT / "data" / "formal" / "universes" / "hs300_history.csv"
                    formal_panel = ROOT / "data" / "formal" / "factors" / "hs300_factor_panel.csv"
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
                        formal_history = ROOT / "data" / "formal" / "universes" / f"{universe_id.lower()}_history.csv"
                        formal_panel = ROOT / "data" / "formal" / "factors" / f"{universe_id.lower()}_factor_panel.csv"
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
                        self.assertEqual(str(submitted_config["market"]["start_date"]), "2015-01-01")
                        self.assertEqual(str(submitted_config["market"]["end_date"]), "2026-04-01")
                        self.assertEqual(submitted_config["output"]["root_dir"], "..")
                        self.assertTrue(
                            str(submitted_config["market"]["universe_path"]).endswith(
                                f"universes/{universe_id.lower()}_history.csv"
                            )
                        )
                        self.assertTrue(
                            str(submitted_config["data"]["path"]).endswith(
                                f"factors/{universe_id.lower()}_factor_panel.csv"
                            )
                        )

            anyio.run(run_case)

    @unittest.skipUnless(
        __import__("importlib").util.find_spec("fastapi") is not None
        and __import__("importlib").util.find_spec("duckdb") is not None,
        "fastapi/duckdb not installed",
    )
    def test_formal_duckdb_routes(self) -> None:
        import httpx
        import anyio

        with tempfile.TemporaryDirectory() as temp_dir:
            formal_root = Path(temp_dir) / "formal"
            (formal_root / "universes").mkdir(parents=True, exist_ok=True)
            (formal_root / "factors").mkdir(parents=True, exist_ok=True)
            (formal_root / "master").mkdir(parents=True, exist_ok=True)
            (formal_root / "baostock" / "financial" / "profit_data").mkdir(parents=True, exist_ok=True)
            (formal_root / "baostock" / "reports" / "forecast_report").mkdir(parents=True, exist_ok=True)

            (formal_root / "universes" / "hs300_history.csv").write_text(
                "\n".join(
                    [
                        "market_id,universe_id,stock_code,start_date,end_date",
                        "cn_a,HS300,600000.SH,2026-03-02,2026-03-03",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (formal_root / "factors" / "hs300_factor_panel.csv").write_text(
                "\n".join(
                    [
                        "stock_code,trade_date,industry,value_factor,momentum_factor,quality_factor,volatility_factor,future_return",
                        "600000.SH,2026-03-02,Bank,1,2,3,4,0.1",
                        "600000.SH,2026-03-03,Bank,1,2,3,4,0.2",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (formal_root / "master" / "shared_kline_panel.csv").write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2026-03-02,sh.600000,10,11,9,10,9.8,100,1000,3,0.2,1,2.0,6.4,0.45,1.85,-1.52,0",
                        "2026-03-03,sh.600000,10,11,9,10,9.8,100,1000,3,0.2,1,2.0,6.4,0.45,1.85,-1.52,0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (formal_root / "master" / "full_master_2026.csv").write_text(
                "\n".join(
                    [
                        "date,code,open,high,low,close,preclose,volume,amount,adjustflag,pctChg,source_price_vendor,source_file,turn,tradestatus,peTTM,pbMRQ,psTTM,pcfNcfTTM,isST",
                        "2026-03-02,sh.600000,10,11,9,10,9.8,100,1000,2,2.0,tongdaxin,a.day,0.2,1,6.4,0.45,1.85,-1.52,0",
                        "2026-03-03,sh.600000,10,11,9,10,9.8,100,1000,2,2.0,tongdaxin,a.day,0.2,1,6.4,0.45,1.85,-1.52,0",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (formal_root / "baostock" / "financial" / "profit_data" / "2025.csv").write_text(
                "\n".join(
                    [
                        "code,pubDate,statDate,dataset,query_year,query_quarter",
                        "sh.600000,2025-04-30,2025-03-31,profit_data,2025,1",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )
            (formal_root / "baostock" / "reports" / "forecast_report" / "2025.csv").write_text(
                "\n".join(
                    [
                        "code,profitForcastExpPubDate,profitForcastExpStatDate,dataset,query_year",
                        "sh.600000,2025-01-21,2024-12-31,forecast_report,2025",
                    ]
                )
                + "\n",
                encoding="utf-8",
            )

            catalog_path = formal_root / "catalog.duckdb"
            register_formal_duckdb_catalog(formal_root=formal_root, catalog_path=catalog_path)

            async def run_case() -> None:
                app = create_app(formal_root=formal_root, catalog_path=catalog_path)
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    response = await client.get("/api/formal/coverage", timeout=10.0)
                    self.assertEqual(response.status_code, 200)
                    coverage_payload = response.json()
                    self.assertEqual(coverage_payload["master"]["row_count"], 2)
                    self.assertEqual(coverage_payload["master"]["stock_count"], 1)
                    self.assertEqual(coverage_payload["factors"][0]["universe_id"], "HS300")
                    self.assertEqual(coverage_payload["financial"][0]["dataset_name"], "profit_data")
                    self.assertEqual(coverage_payload["reports"][0]["dataset_name"], "forecast_report")

                    response = await client.get(
                        "/api/formal/universes/HS300",
                        params={"trade_date": "2026-03-02"},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 200)
                    universe_payload = response.json()
                    self.assertEqual(len(universe_payload), 1)
                    self.assertEqual(universe_payload[0]["trade_date"], "2026-03-02")
                    self.assertEqual(universe_payload[0]["stock_code"], "600000.SH")
                    self.assertEqual(universe_payload[0]["universe_id"], "HS300")

                    response = await client.get(
                        "/api/formal/universes/UNKNOWN",
                        params={"trade_date": "2026-03-02"},
                        timeout=10.0,
                    )
                    self.assertEqual(response.status_code, 404)

            anyio.run(run_case)


if __name__ == "__main__":
    unittest.main()
