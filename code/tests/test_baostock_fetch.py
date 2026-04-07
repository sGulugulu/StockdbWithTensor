from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.fetch_baostock_data import (
    _all_a_codes_from_stock_basic_rows,
    _derive_change_rows,
    _group_quarters_by_year,
    _is_cn_a_equity_row,
    _iter_quarters,
    _load_completed_units_from_output,
    _resolve_stage2_codes,
    _select_query_names,
    _stage2_dataset_output_path,
    _to_baostock_code,
    fetch_baostock_bundle,
    build_all_a_tradable_history_rows,
)


class BaostockFetchTests(unittest.TestCase):
    def test_iter_quarters_covers_full_year_range(self) -> None:
        self.assertEqual(
            _iter_quarters(2024, 2025),
            [
                (2024, 1),
                (2024, 2),
                (2024, 3),
                (2024, 4),
                (2025, 1),
                (2025, 2),
                (2025, 3),
                (2025, 4),
            ],
        )

    def test_group_quarters_by_year_groups_each_year_separately(self) -> None:
        self.assertEqual(
            _group_quarters_by_year([(2025, 1), (2025, 2), (2026, 1)]),
            {
                2025: [(2025, 1), (2025, 2)],
                2026: [(2026, 1)],
            },
        )

    def test_select_query_names_validates_requested_datasets(self) -> None:
        self.assertEqual(
            _select_query_names(["profit_data", "growth_data"], "profit_data"),
            ["profit_data"],
        )
        with self.assertRaises(ValueError):
            _select_query_names(["profit_data"], "unknown_data")

    def test_stage2_dataset_output_path_uses_dataset_and_year_subdirectories(self) -> None:
        self.assertEqual(
            _stage2_dataset_output_path(
                output_root=Path("code/data/formal/baostock"),
                stage="financial",
                dataset="profit_data",
                year=2015,
            ).as_posix(),
            "code/data/formal/baostock/financial/profit_data/2015.csv",
        )

    def test_load_completed_units_from_output_reads_existing_dataset_year_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            path = root / "financial" / "profit_data" / "2015.csv"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "\n".join(
                    [
                        "code,dataset,query_year,query_quarter",
                        "sh.600000,profit_data,2015,1",
                        "sh.600000,profit_data,2015,2",
                        "sz.000001,profit_data,2015,1",
                    ]
                ),
                encoding="utf-8",
            )
            self.assertEqual(
                _load_completed_units_from_output(path, 2015),
                {"sh.600000|2015", "sz.000001|2015"},
            )

    def test_derive_change_rows_detects_add_and_remove(self) -> None:
        rows = [
            {"index_id": "hs300", "snapshot_date": "2024-01-02", "effective_date": "2024-01-02", "code": "sh.600000", "code_name": "A"},
            {"index_id": "hs300", "snapshot_date": "2024-01-02", "effective_date": "2024-01-02", "code": "sh.600001", "code_name": "B"},
            {"index_id": "hs300", "snapshot_date": "2024-01-03", "effective_date": "2024-01-03", "code": "sh.600000", "code_name": "A"},
            {"index_id": "hs300", "snapshot_date": "2024-01-03", "effective_date": "2024-01-03", "code": "sh.600002", "code_name": "C"},
        ]
        changes = _derive_change_rows(rows)
        self.assertEqual(len(changes), 4)
        self.assertEqual(changes[0]["change_type"], "add")
        self.assertEqual(changes[1]["change_type"], "add")
        self.assertEqual(changes[2]["change_type"], "add")
        self.assertEqual(changes[3]["change_type"], "remove")
        self.assertEqual(changes[3]["code"], "sh.600001")

    def test_is_cn_a_equity_row_filters_supported_a_share_codes(self) -> None:
        self.assertTrue(_is_cn_a_equity_row({"code": "sh.600000", "type": "1"}))
        self.assertTrue(_is_cn_a_equity_row({"code": "sh.688001", "type": "1"}))
        self.assertTrue(_is_cn_a_equity_row({"code": "sz.300001", "type": "1"}))
        self.assertFalse(_is_cn_a_equity_row({"code": "bj.430001", "type": "1"}))
        self.assertFalse(_is_cn_a_equity_row({"code": "hk.000001", "type": "1"}))
        self.assertFalse(_is_cn_a_equity_row({"code": "sh.600000", "type": "2"}))

    def test_build_all_a_tradable_history_rows_uses_ipo_and_out_dates(self) -> None:
        rows = [
            {"code": "sh.600000", "ipoDate": "1999-11-10", "outDate": "", "type": "1", "status": "1"},
            {"code": "sz.300001", "ipoDate": "2010-01-08", "outDate": "2026-03-31", "type": "1", "status": "1"},
            {"code": "bj.430001", "ipoDate": "2015-01-01", "outDate": "", "type": "1", "status": "1"},
            {"code": "sh.600010", "ipoDate": "", "outDate": "", "type": "1", "status": "1"},
        ]
        history_rows = build_all_a_tradable_history_rows(rows, horizon_date="2026-04-01")
        self.assertEqual(
            history_rows,
            [
                {
                    "market_id": "cn_a",
                    "universe_id": "ALL_A",
                    "stock_code": "300001.SZ",
                    "start_date": "2010-01-08",
                    "end_date": "2026-03-31",
                },
                {
                    "market_id": "cn_a",
                    "universe_id": "ALL_A",
                    "stock_code": "600000.SH",
                    "start_date": "1999-11-10",
                    "end_date": "2026-04-01",
                },
            ],
        )

    def test_resolve_stage2_codes_expands_to_all_a_when_requested(self) -> None:
        stock_basic_rows = [
            {"code": "sh.600000", "ipoDate": "1999-11-10", "outDate": "", "type": "1", "status": "1"},
            {"code": "sz.300001", "ipoDate": "2010-01-08", "outDate": "", "type": "1", "status": "1"},
            {"code": "bj.430001", "ipoDate": "2015-01-01", "outDate": "", "type": "1", "status": "1"},
        ]
        resolved = _resolve_stage2_codes(
            stage2_scope="all_a",
            selected_codes=["600000.SH"],
            stock_basic_rows=stock_basic_rows,
            output_root=Path("."),
        )
        self.assertEqual(resolved, ["sh.600000", "sz.300001"])

    def test_resolve_stage2_codes_keeps_selected_scope(self) -> None:
        resolved = _resolve_stage2_codes(
            stage2_scope="selected",
            selected_codes=["600000.SH"],
            stock_basic_rows=[],
            output_root=Path("."),
        )
        self.assertEqual(resolved, ["600000.SH"])

    def test_to_baostock_code_converts_cn_a_symbols(self) -> None:
        self.assertEqual(_to_baostock_code("600000.SH"), "sh.600000")
        self.assertEqual(_to_baostock_code("000001.SZ"), "sz.000001")
        self.assertEqual(_to_baostock_code("SH.600000"), "sh.600000")
        self.assertEqual(_to_baostock_code("sz.300001"), "sz.300001")

    def test_all_a_codes_from_stock_basic_rows_returns_raw_baostock_codes(self) -> None:
        rows = [
            {"code": "sh.600000", "ipoDate": "1999-11-10", "outDate": "", "type": "1", "status": "1"},
            {"code": "sz.300001", "ipoDate": "2010-01-08", "outDate": "", "type": "1", "status": "1"},
            {"code": "bj.430001", "ipoDate": "2015-01-01", "outDate": "", "type": "1", "status": "1"},
        ]
        self.assertEqual(_all_a_codes_from_stock_basic_rows(rows), ["sh.600000", "sz.300001"])

    def test_all_a_history_output_requires_all_a_metadata_scope(self) -> None:
        with self.assertRaises(ValueError):
            fetch_baostock_bundle(
                output_root=Path("."),
                start_date="2015-01-01",
                end_date="2026-04-01",
                indices=["hs300"],
                financial_start_year=2015,
                financial_end_year=2026,
                max_codes=None,
                sleep_seconds=0.0,
                skip_financials=True,
                skip_reports=True,
                skip_index_memberships=True,
                skip_metadata=True,
                metadata_scope="selected",
                stage2_scope="selected",
                financial_datasets=None,
                report_datasets=None,
                all_a_history_output=Path("code/data/formal/universes/all_a_tradable_history.csv"),
                selected_codes_file=Path("code/data/formal/baostock/metadata/selected_codes.csv"),
                resume=False,
            )


if __name__ == "__main__":
    unittest.main()
