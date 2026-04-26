from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from data.build_extended_factor_panel import build_extended_factor_panel


class ExtendedFactorPanelTests(unittest.TestCase):
    def test_build_extended_factor_panel_merges_pit_and_event_features(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            base_panel = root / "base.csv"
            profit_data = root / "profit.csv"
            perf_dir = root / "performance_express_report"
            perf_dir.mkdir(parents=True, exist_ok=True)
            perf_data = perf_dir / "2026.csv"
            output_path = root / "extended.csv"

            base_panel.write_text(
                "\n".join(
                    [
                        "stock_code,trade_date,industry,value_factor,momentum_factor,quality_factor,volatility_factor,turn_factor,ps_ttm,future_return",
                        "600000.SH,2026-03-25,Bank,0.5,0.1,0.2,0.3,0.4,1.0,0.02",
                        "600000.SH,2026-03-30,Bank,0.5,0.1,0.2,0.3,0.4,1.0,0.02",
                    ]
                ),
                encoding="utf-8",
            )
            profit_data.write_text(
                "\n".join(
                    [
                        "code,pubDate,statDate,roeAvg,npMargin,gpMargin,netProfit,epsTTM,MBRevenue,totalShare,liqaShare,dataset,query_year,query_quarter",
                        "sh.600000,2026-03-24,2025-12-31,0.11,0.22,0.33,1,0.44,1,1,1,profit_data,2025,4",
                    ]
                ),
                encoding="utf-8",
            )
            perf_data.write_text(
                "\n".join(
                    [
                        "code,performanceExpPubDate,performanceExpStatDate,performanceExpUpdateDate,performanceExpressTotalAsset,performanceExpressNetAsset,performanceExpressEPSChgPct,performanceExpressROEWa,performanceExpressEPSDiluted,performanceExpressGRYOY,performanceExpressOPYOY,dataset,query_year",
                        "sh.600000,2026-03-26,2025-12-31,2026-03-26,1,1,0.55,6.7,1,0.66,0.77,performance_express_report,2026",
                    ]
                ),
                encoding="utf-8",
            )

            build_extended_factor_panel(
                base_panel_path=base_panel,
                profit_data_path=profit_data,
                performance_express_path=perf_dir,
                output_path=output_path,
            )

            content = output_path.read_text(encoding="utf-8")
            self.assertIn("pit_roe_avg", content)
            self.assertIn("perf_express_eps_chg_pct", content)
            self.assertIn("perf_express_flag", content)
            self.assertIn("0.11", content)
            self.assertIn("0.55", content)


if __name__ == "__main__":
    unittest.main()
