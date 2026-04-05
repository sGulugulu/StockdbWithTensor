from __future__ import annotations

import csv
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.refresh_formal_baostock_manifest import refresh_manifest


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


class RefreshFormalBaostockManifestTests(unittest.TestCase):
    def test_refresh_manifest_rebuilds_shared_union_outputs_from_formal_kline_sources(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            canonical_root = root / "canonical"
            formal_root = root / "formal"
            source_roots = {
                "hs300": root / "hs300_src",
                "sz50": root / "sz50_src",
                "zz500": root / "zz500_src",
            }

            for universe_id, source_root in source_roots.items():
                source_root.mkdir(parents=True, exist_ok=True)
                (source_root / "manifest.json").write_text(
                    json.dumps({"source": universe_id}, ensure_ascii=False),
                    encoding="utf-8",
                )
                _write_csv(
                    source_root / "metadata" / "selected_codes.csv",
                    ["code"],
                    [{"code": "sh.999999"}],
                )

            _write_csv(
                formal_root / "hs300_kline_panel.csv",
                ["date", "code", "close"],
                [
                    {"date": "2026-03-02", "code": "sh.600000", "close": "10"},
                    {"date": "2026-03-03", "code": "sh.600000", "close": "11"},
                ],
            )
            _write_csv(
                formal_root / "sz50_kline_panel.csv",
                ["date", "code", "close"],
                [
                    {"date": "2026-03-02", "code": "sh.600010", "close": "12"},
                    {"date": "2026-03-03", "code": "sh.600010", "close": "13"},
                ],
            )
            _write_csv(
                formal_root / "zz500_kline_panel.csv",
                ["date", "code", "close"],
                [
                    {"date": "2026-03-02", "code": "sz.000001", "close": "14"},
                    {"date": "2026-03-03", "code": "sz.000001", "close": "15"},
                ],
            )

            for universe_id, stock_code in {
                "hs300": "600000.SH",
                "sz50": "600010.SH",
                "zz500": "000001.SZ",
            }.items():
                _write_csv(
                    formal_root / f"{universe_id}_history.csv",
                    ["stock_code", "start_date", "end_date"],
                    [{"stock_code": stock_code, "start_date": "2026-03-02", "end_date": "2026-03-03"}],
                )
                _write_csv(
                    formal_root / f"{universe_id}_factor_panel.csv",
                    ["stock_code", "trade_date", "value_factor"],
                    [
                        {"stock_code": stock_code, "trade_date": "2026-03-02", "value_factor": "1.0"},
                        {"stock_code": stock_code, "trade_date": "2026-03-03", "value_factor": "1.1"},
                    ],
                )

            manifest_path = refresh_manifest(
                canonical_root=canonical_root,
                hs300_src=source_roots["hs300"],
                sz50_src=source_roots["sz50"],
                zz500_src=source_roots["zz500"],
                formal_root=formal_root,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(
                manifest["stages"]["stage_3_formal_outputs"]["shared_selected_codes"]["selected_codes_rows"],
                3,
            )
            self.assertEqual(
                manifest["stages"]["stage_3_formal_outputs"]["shared_kline_panel"]["kline_panel_rows"],
                6,
            )

            selected_codes_path = canonical_root / "metadata" / "selected_codes.csv"
            selected_lines = selected_codes_path.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(selected_lines, ["code", "sh.600000", "sh.600010", "sz.000001"])

            union_lines = (canonical_root / "kline_panel.csv").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(union_lines), 7)
            self.assertIn("2026-03-02,sh.600000,10", union_lines)
            self.assertIn("2026-03-03,sz.000001,15", union_lines)

    def test_refresh_manifest_does_not_depend_on_legacy_fixture_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            canonical_root = root / "canonical"
            formal_root = root / "formal"
            canonical_root.mkdir(parents=True, exist_ok=True)
            (canonical_root / "manifest.json").write_text(json.dumps({"source": "canonical"}), encoding="utf-8")
            _write_csv(
                canonical_root / "metadata" / "stock_basic.csv",
                ["code", "ipoDate", "outDate", "type", "status"],
                [{"code": "sh.600000", "ipoDate": "1999-11-10", "outDate": "", "type": "1", "status": "1"}],
            )
            _write_csv(
                formal_root / "master" / "shared_kline_panel.csv",
                ["date", "code", "close"],
                [{"date": "2026-03-02", "code": "sh.600000", "close": "10"}],
            )
            _write_csv(
                formal_root / "universes" / "hs300_history.csv",
                ["stock_code", "start_date", "end_date"],
                [{"stock_code": "600000.SH", "start_date": "2026-03-02", "end_date": "2026-03-02"}],
            )
            _write_csv(
                formal_root / "factors" / "hs300_factor_panel.csv",
                ["stock_code", "trade_date", "value_factor"],
                [{"stock_code": "600000.SH", "trade_date": "2026-03-02", "value_factor": "1.0"}],
            )
            _write_csv(
                formal_root / "universes" / "sz50_history.csv",
                ["stock_code", "start_date", "end_date"],
                [],
            )
            _write_csv(
                formal_root / "factors" / "sz50_factor_panel.csv",
                ["stock_code", "trade_date", "value_factor"],
                [],
            )
            _write_csv(
                formal_root / "universes" / "zz500_history.csv",
                ["stock_code", "start_date", "end_date"],
                [],
            )
            _write_csv(
                formal_root / "factors" / "zz500_factor_panel.csv",
                ["stock_code", "trade_date", "value_factor"],
                [],
            )

            manifest_path = refresh_manifest(
                canonical_root=canonical_root,
                hs300_src=canonical_root,
                sz50_src=canonical_root,
                zz500_src=canonical_root,
                formal_root=formal_root,
            )

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            self.assertEqual(manifest["source"], "baostock")
            stock_basic_text = (canonical_root / "metadata" / "stock_basic.csv").read_text(encoding="utf-8")
            self.assertIn("sh.600000", stock_basic_text)


if __name__ == "__main__":
    unittest.main()
