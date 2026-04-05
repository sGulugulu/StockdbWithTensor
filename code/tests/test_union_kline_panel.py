from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_union_kline_panel import build_union_kline_panel


class UnionKlinePanelTests(unittest.TestCase):
    def test_build_union_kline_panel_merges_unique_rows_and_keeps_exact_code_union(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            left = root / "left.csv"
            right = root / "right.csv"
            left.write_text(
                (
                    "date,code,close\n"
                    "2026-03-02,sh.600000,10\n"
                    "2026-03-03,sh.600000,11\n"
                    "2026-03-02,sz.000001,12\n"
                ),
                encoding="utf-8",
            )
            right.write_text(
                (
                    "date,code,close\n"
                    "2026-03-02,sz.000001,13\n"
                    "2026-03-03,sz.000001,14\n"
                    "2026-03-02,sh.600010,15\n"
                ),
                encoding="utf-8",
            )
            out = root / "union.csv"
            codes = root / "codes.csv"
            build_union_kline_panel(
                input_paths=[left, right],
                output_path=out,
                selected_codes_output=codes,
            )
            union_rows = out.read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(union_rows), 6)
            self.assertEqual(
                union_rows,
                [
                    "date,code,close",
                    "2026-03-02,sh.600000,10",
                    "2026-03-02,sh.600010,15",
                    "2026-03-02,sz.000001,13",
                    "2026-03-03,sh.600000,11",
                    "2026-03-03,sz.000001,14",
                ],
            )
            codes_text = codes.read_text(encoding="utf-8")
            self.assertEqual(
                codes_text.strip().splitlines(),
                ["code", "sh.600000", "sh.600010", "sz.000001"],
            )


if __name__ == "__main__":
    unittest.main()
