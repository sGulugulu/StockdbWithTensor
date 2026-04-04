from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_union_kline_panel import build_union_kline_panel


class UnionKlinePanelTests(unittest.TestCase):
    def test_build_union_kline_panel_merges_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            left = root / "left.csv"
            right = root / "right.csv"
            left.write_text(
                "date,code,close\n2026-03-02,sh.600000,10\n2026-03-03,sh.600000,11\n",
                encoding="utf-8",
            )
            right.write_text(
                "date,code,close\n2026-03-02,sz.000001,12\n2026-03-03,sz.000001,13\n",
                encoding="utf-8",
            )
            out = root / "union.csv"
            codes = root / "codes.csv"
            build_union_kline_panel(
                input_paths=[left, right],
                output_path=out,
                selected_codes_output=codes,
            )
            union_text = out.read_text(encoding="utf-8")
            self.assertIn("sh.600000", union_text)
            self.assertIn("sz.000001", union_text)
            codes_text = codes.read_text(encoding="utf-8")
            self.assertIn("sh.600000", codes_text)
            self.assertIn("sz.000001", codes_text)


if __name__ == "__main__":
    unittest.main()
