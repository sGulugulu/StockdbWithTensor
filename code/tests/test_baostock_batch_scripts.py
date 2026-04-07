from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]


class BaostockBatchScriptTests(unittest.TestCase):
    def test_run_baostock_full_routes_shared_kline_through_stable_progress_file(self) -> None:
        script_text = (REPO_ROOT / "code" / "data" / "run_baostock_full.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('SHARED_MASTER_PROGRESS="$FORMAL_ROOT/master/shared_kline_panel.progress.json"', script_text)
        self.assertIn('--progress-path "$SHARED_MASTER_PROGRESS"', script_text)
        self.assertIn('rm -f "$SHARED_MASTER_PATH" "$SHARED_MASTER_PROGRESS"', script_text)

    def test_run_baostock_full_runs_stage4_before_manifest_refresh(self) -> None:
        script_text = (REPO_ROOT / "code" / "data" / "run_baostock_full.sh").read_text(
            encoding="utf-8"
        )
        convert_index = script_text.index("code/data/convert_formal_csv_to_parquet.py")
        refresh_index = script_text.index("code/data/refresh_formal_baostock_manifest.py")
        self.assertLess(convert_index, refresh_index)

    def test_run_baostock_master_fields_year_prefers_tdx_year_codes(self) -> None:
        script_text = (REPO_ROOT / "code" / "data" / "run_baostock_master_fields_year.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn('TDX_BASE_PATH="code/data/formal/master/tdx_full_master_base_${YEAR}.csv"', script_text)
        self.assertIn('CODES_FILE="${BASE_DIR}/_codes_${YEAR}.csv"', script_text)
        self.assertIn('code/data/extract_tdx_year_codes.py', script_text)
        self.assertIn('--codes-file "$CODES_FILE"', script_text)


if __name__ == "__main__":
    unittest.main()
