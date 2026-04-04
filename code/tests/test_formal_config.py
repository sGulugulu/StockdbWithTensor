from pathlib import Path
import sys
import tempfile
import unittest

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from stock_tensor.pipeline import run_experiment


ROOT = Path(__file__).resolve().parents[1]


class FormalConfigTests(unittest.TestCase):
    def test_formal_default_config_fails_without_real_data(self) -> None:
        with self.assertRaises(FileNotFoundError):
            run_experiment(ROOT / "configs" / "default.yaml")

    def test_formal_hs300_config_runs_with_real_local_inputs(self) -> None:
        source_root = ROOT / "data" / "formal" / "baostock_fg_test"
        if not source_root.exists():
            self.skipTest("baostock_fg_test fixtures are not available")

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_root = Path(temp_dir)
            history_src = source_root / "index_memberships" / "hs300_snapshots.csv"
            kline_src = temp_root / "kline.csv"
            industry_src = source_root / "metadata" / "stock_industry.csv"
            history_out = temp_root / "hs300_history.csv"
            panel_out = temp_root / "hs300_factor_panel.csv"
            config_out = temp_root / "formal_hs300.yaml"

            from data.build_baostock_member_history import build_member_history
            from data.build_formal_factor_panel import build_formal_factor_panel

            # Reuse the first 10 symbols to keep the fixture run fast and deterministic.
            selected_codes = []
            with (source_root / "metadata" / "selected_codes.csv").open("r", encoding="utf-8", newline="") as handle:
                import csv

                for row in csv.DictReader(handle):
                    selected_codes.append(row["code"])
                    if len(selected_codes) >= 10:
                        break

            # Build a small synthetic kline panel for the selected hs300 constituents.
            import csv
            with kline_src.open("w", encoding="utf-8", newline="") as dst:
                writer = csv.DictWriter(
                    dst,
                    fieldnames=[
                        "date",
                        "code",
                        "open",
                        "high",
                        "low",
                        "close",
                        "preclose",
                        "volume",
                        "amount",
                        "adjustflag",
                        "turn",
                        "tradestatus",
                        "pctChg",
                        "peTTM",
                        "pbMRQ",
                        "psTTM",
                        "pcfNcfTTM",
                        "isST",
                    ],
                )
                writer.writeheader()
                for code in selected_codes:
                    for offset, price in enumerate([10.0, 10.4, 10.8, 11.0, 11.3, 11.7], start=1):
                        writer.writerow(
                            {
                                "date": f"2026-03-{offset:02d}",
                                "code": code,
                                "open": price - 0.1,
                                "high": price + 0.2,
                                "low": price - 0.2,
                                "close": price,
                                "preclose": price - 0.1,
                                "volume": 100000,
                                "amount": 1000000,
                                "adjustflag": 3,
                                "turn": 0.1,
                                "tradestatus": 1,
                                "pctChg": 0.01,
                                "peTTM": 10,
                                "pbMRQ": 2,
                                "psTTM": 3,
                                "pcfNcfTTM": 4,
                                "isST": 0,
                            }
                        )

            build_member_history(history_src, history_out, horizon_date="2026-04-04")
            build_formal_factor_panel(
                kline_path=kline_src,
                industry_path=industry_src,
                membership_path=history_out,
                output_path=panel_out,
            )

            config_data = yaml.safe_load((ROOT / "configs" / "formal_hs300.yaml").read_text(encoding="utf-8"))
            config_data["market"]["universe_path"] = str(history_out)
            config_data["data"]["path"] = str(panel_out)
            config_data["output"]["root_dir"] = str(temp_root)
            config_data["output"]["experiment_name"] = "formal_hs300_test_run"
            config_out.write_text(yaml.safe_dump(config_data, sort_keys=False, allow_unicode=True), encoding="utf-8")

            output_dir = run_experiment(config_out)
            self.assertTrue((output_dir / "run_manifest.json").exists())
            self.assertTrue((output_dir / "selection_candidates.json").exists())


if __name__ == "__main__":
    unittest.main()
