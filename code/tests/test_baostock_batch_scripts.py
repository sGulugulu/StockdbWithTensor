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

    def test_rebuild_full_master_for_year_script_runs_cleanup_fetch_build_and_checks(self) -> None:
        script_text = (REPO_ROOT / "code" / "data" / "rebuild_full_master_for_year.ps1").read_text(
            encoding="utf-8"
        )
        self.assertIn('Remove-Item -Recurse -Force $yearDir -ErrorAction SilentlyContinue', script_text)
        self.assertIn('run_baostock_master_fields_year.sh $Year $MaxParallelMonths', script_text)
        self.assertIn('build_full_master_for_existing_year.ps1 $Year', script_text)
        self.assertIn('check_full_master_year.py --year $Year', script_text)
        self.assertIn('reconcile_full_master_year.py --year $Year', script_text)

    def test_rebuild_full_master_for_year_generates_tdx_base_before_fetch(self) -> None:
        script_text = (REPO_ROOT / "code" / "data" / "rebuild_full_master_for_year.ps1").read_text(
            encoding="utf-8"
        )
        fetch_index = script_text.index('run_baostock_master_fields_year.sh $Year $MaxParallelMonths')
        build_slice_index = script_text.index('build_tdx_year_slice.py')
        build_base_index = script_text.index('build_tdx_full_master_base.py')
        self.assertLess(build_slice_index, fetch_index)
        self.assertLess(build_base_index, fetch_index)


if __name__ == "__main__":
    unittest.main()
