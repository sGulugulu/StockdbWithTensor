from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Iterable
import sys

CODE_ROOT = Path(__file__).resolve().parents[1]
if str(CODE_ROOT) not in sys.path:
    sys.path.insert(0, str(CODE_ROOT))


def _normalize_cn_a_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if "." in cleaned:
        left, right = cleaned.split(".", 1)
        if left in {"SH", "SZ", "BJ"} and right.isdigit():
            return f"{right}.{left}"
        if right in {"SH", "SZ", "BJ"} and left.isdigit():
            return f"{left}.{right}"
        return cleaned
    if cleaned.startswith(("6", "9")):
        return f"{cleaned}.SH"
    return f"{cleaned}.SZ"


def _load_akshare():
    import akshare as ak

    return ak


def _to_float(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def _safe_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() == "nan":
        return ""
    return text


def _parse_any_date(value: object) -> str | None:
    text = _safe_text(value)
    if not text:
        return None
    if len(text) == 8 and text.isdigit():
        return date(int(text[:4]), int(text[4:6]), int(text[6:8])).isoformat()
    if "年" in text and "月" in text:
        normalized = text.replace("年", "-").replace("月", "-").replace("日", "")
        parts = [part for part in normalized.split("-") if part]
        if len(parts) >= 2:
            year = int(parts[0])
            month = int(parts[1])
            day = int(parts[2]) if len(parts) >= 3 else 1
            return date(year, month, day).isoformat()
    try:
        return date.fromisoformat(text[:10]).isoformat()
    except ValueError:
        return None


def _next_trade_date_after(reference_date: str, trade_dates: list[str]) -> str | None:
    for trade_date in trade_dates:
        if trade_date > reference_date:
            return trade_date
    return None


def _source_available_date(pub_date: str, trade_dates: list[str]) -> str:
    # 窗口前事件保留原公告日，避免历史信息被误判为首个交易日刚发生。
    if trade_dates and pub_date < trade_dates[0]:
        return pub_date
    return _next_trade_date_after(pub_date, trade_dates) or ""


def _iter_target_symbols(history_paths: Iterable[Path]) -> list[str]:
    symbols: set[str] = set()
    for path in history_paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                stock_code = row.get("stock_code") or row.get("code")
                if stock_code:
                    symbols.add(_normalize_cn_a_symbol(stock_code))
    return sorted(symbols)


def _iter_trade_dates(panel_paths: Iterable[Path], *, max_trade_date: str) -> list[str]:
    trade_dates: set[str] = set()
    for path in panel_paths:
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                trade_date = row.get("trade_date")
                if trade_date and trade_date <= max_trade_date:
                    trade_dates.add(trade_date)
    return sorted(trade_dates)


def _write_rows(path: Path, fieldnames: list[str], rows: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


MAJOR_NOTICE_TYPE_MARKERS = (
    "重大",
    "风险",
    "重组",
    "再融资",
    "增持",
    "减持",
    "权益变动",
    "股份质押",
    "冻结",
    "诉讼",
    "处罚",
    "停牌",
    "复牌",
    "担保",
)


def _is_major_notice_type(notice_type: str) -> bool:
    if not notice_type:
        return False
    # 重大事件只按公告分类识别，标题关键词只用于强度打分，避免普通公告污染重大事件特征。
    return any(marker in notice_type for marker in MAJOR_NOTICE_TYPE_MARKERS)


def _notice_identity(row: dict[str, object]) -> tuple[str, str, str, str, str]:
    return (
        str(row.get("stock_code", "")),
        str(row.get("notice_type", "")),
        str(row.get("pub_date", "")),
        str(row.get("title_text", "")),
        str(row.get("url", "")),
    )


def _macro_rows_from_common_table(*, source_api: str, metric_id: str, metric_name: str, rows: list[dict[str, object]], trade_dates: list[str]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for row in rows:
        pub_date = _parse_any_date(row.get("日期"))
        if not pub_date:
            continue
        available_date = _source_available_date(pub_date, trade_dates)
        result.append(
            {
                "source_api": source_api,
                "metric_id": metric_id,
                "metric_name": metric_name,
                "pub_date": pub_date,
                "available_date": available_date,
                "value": _to_float(row.get("今值")) or 0.0,
                "expected_value": _to_float(row.get("预测值")) or 0.0,
                "previous_value": _to_float(row.get("前值")) or 0.0,
            }
        )
    return result


def build_macro_interest_rate_rows(*, trade_dates: list[str]) -> list[dict[str, object]]:
    ak = _load_akshare()
    rows: list[dict[str, object]] = []
    policy_df = ak.macro_bank_china_interest_rate()
    rows.extend(
        _macro_rows_from_common_table(
            source_api="akshare.macro_bank_china_interest_rate",
            metric_id="policy_rate_current",
            metric_name="china_policy_rate",
            rows=policy_df.to_dict("records"),
            trade_dates=trade_dates,
        )
    )
    lpr_df = ak.macro_china_lpr()
    for row in lpr_df.to_dict("records"):
        pub_date = _parse_any_date(row.get("TRADE_DATE"))
        if not pub_date:
            continue
        available_date = _source_available_date(pub_date, trade_dates)
        for metric_id, metric_name, source_field in (
            ("lpr_1y", "china_lpr_1y", "LPR1Y"),
            ("lpr_5y", "china_lpr_5y", "LPR5Y"),
            ("loan_rate_1", "china_loan_rate_1", "RATE_1"),
            ("loan_rate_2", "china_loan_rate_2", "RATE_2"),
        ):
            value = _to_float(row.get(source_field))
            if value is None:
                continue
            rows.append(
                {
                    "source_api": "akshare.macro_china_lpr",
                    "metric_id": metric_id,
                    "metric_name": metric_name,
                    "pub_date": pub_date,
                    "available_date": available_date,
                    "value": value,
                    "expected_value": 0.0,
                    "previous_value": 0.0,
                }
            )
    rows.sort(key=lambda item: (str(item["pub_date"]), str(item["metric_id"])))
    return rows


def build_macro_monthly_rows(*, trade_dates: list[str]) -> list[dict[str, object]]:
    ak = _load_akshare()
    rows: list[dict[str, object]] = []
    for source_api, metric_id, metric_name, loader in (
        ("akshare.macro_china_cpi_monthly", "cpi_mom", "china_cpi_monthly", ak.macro_china_cpi_monthly),
        ("akshare.macro_china_m2_yearly", "m2_yoy", "china_m2_yearly", ak.macro_china_m2_yearly),
        ("akshare.macro_china_industrial_production_yoy", "industrial_production_yoy", "china_industrial_production_yoy", ak.macro_china_industrial_production_yoy),
        ("akshare.macro_china_exports_yoy", "exports_yoy", "china_exports_yoy", ak.macro_china_exports_yoy),
        ("akshare.macro_china_imports_yoy", "imports_yoy", "china_imports_yoy", ak.macro_china_imports_yoy),
    ):
        rows.extend(
            _macro_rows_from_common_table(
                source_api=source_api,
                metric_id=metric_id,
                metric_name=metric_name,
                rows=loader().to_dict("records"),
                trade_dates=trade_dates,
            )
        )
    rows.sort(key=lambda item: (str(item["pub_date"]), str(item["metric_id"])))
    return rows


def build_dividend_rows(*, symbols: list[str], trade_dates: list[str]) -> list[dict[str, object]]:
    ak = _load_akshare()
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        query_symbol = symbol.split(".")[0]
        try:
            dividend_df = ak.stock_dividend_cninfo(symbol=query_symbol)
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch dividend rows for {symbol}") from exc
        for row in dividend_df.to_dict("records"):
            pub_date = _parse_any_date(row.get("实施方案公告日期"))
            if not pub_date:
                continue
            available_date = _source_available_date(pub_date, trade_dates)
            rows.append(
                {
                    "stock_code": symbol,
                    "report_period": _safe_text(row.get("报告时间")),
                    "dividend_type": _safe_text(row.get("分红类型")),
                    "pub_date": pub_date,
                    "available_date": available_date,
                    "record_date": _parse_any_date(row.get("股权登记日")) or "",
                    "ex_date": _parse_any_date(row.get("除权日")) or "",
                    "pay_date": _parse_any_date(row.get("派息日")) or "",
                    "bonus_ratio": _to_float(row.get("送股比例")) or 0.0,
                    "transfer_ratio": _to_float(row.get("转增比例")) or 0.0,
                    "cash_ratio": _to_float(row.get("派息比例")) or 0.0,
                    "plan_text": _safe_text(row.get("实施方案分红说明")),
                    "source_api": "akshare.stock_dividend_cninfo",
                }
            )
    rows.sort(key=lambda item: (str(item["stock_code"]), str(item["pub_date"])))
    return rows


def build_notice_rows(
    *,
    symbols: list[str],
    trade_dates: list[str],
    start_date: str,
    end_date: str,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    ak = _load_akshare()
    allowed_codes = {symbol.split(".")[0] for symbol in symbols}
    all_rows: list[dict[str, object]] = []
    major_rows: list[dict[str, object]] = []
    seen_notice_keys: set[tuple[str, str, str, str, str]] = set()
    current_date = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    keyword_scores = {
        "回购": 1.0,
        "增持": 1.0,
        "减持": -1.0,
        "重组": 1.5,
        "诉讼": -1.2,
        "处罚": -1.5,
        "分红": 0.6,
    }
    while current_date <= end:
        try:
            notice_df = ak.stock_notice_report(symbol="全部", date=current_date.strftime("%Y%m%d"))
        except Exception as exc:
            raise RuntimeError(f"Failed to fetch notice rows for {current_date.isoformat()}") from exc
        for row in notice_df.to_dict("records"):
            raw_code = _safe_text(row.get("代码"))
            if raw_code not in allowed_codes:
                continue
            pub_date = _parse_any_date(row.get("公告日期"))
            if not pub_date:
                continue
            available_date = _source_available_date(pub_date, trade_dates)
            title = _safe_text(row.get("公告标题"))
            notice_type = _safe_text(row.get("公告类型"))
            keyword_score = 0.0
            lowered_title = title.lower()
            for keyword, score in keyword_scores.items():
                if keyword.lower() in lowered_title:
                    keyword_score += score
            normalized = {
                "stock_code": _normalize_cn_a_symbol(raw_code),
                "notice_type": notice_type,
                "pub_date": pub_date,
                "available_date": available_date,
                "title_text": title,
                "title_length": len(title),
                "keyword_score": keyword_score,
                "url": _safe_text(row.get("网址")),
                "source_api": "akshare.stock_notice_report",
            }
            notice_key = _notice_identity(normalized)
            if notice_key in seen_notice_keys:
                continue
            seen_notice_keys.add(notice_key)
            all_rows.append(normalized)
            if _is_major_notice_type(notice_type):
                major_rows.append(
                    {
                        **normalized,
                        "severity_score": 1.0 + abs(keyword_score),
                    }
                )
        current_date += timedelta(days=1)
    all_rows.sort(key=lambda item: (str(item["stock_code"]), str(item["pub_date"]), str(item["notice_type"])))
    major_rows.sort(key=lambda item: (str(item["stock_code"]), str(item["pub_date"]), str(item["notice_type"])))
    return all_rows, major_rows


@dataclass(frozen=True, slots=True)
class ExtendedSourceBuildResult:
    macro_interest_rate_path: Path
    macro_monthly_path: Path
    dividend_events_path: Path
    major_event_notice_path: Path
    announcement_text_path: Path
    snapshot_metadata_path: Path


def build_formal_extended_sources(
    *,
    formal_root: Path,
    max_trade_date: str,
    notice_lookback_days: int = 30,
    panel_paths: Iterable[Path] | None = None,
) -> ExtendedSourceBuildResult:
    normalized_root = formal_root.resolve()
    history_paths = [
        normalized_root / "universes" / "hs300_history.csv",
        normalized_root / "universes" / "sz50_history.csv",
        normalized_root / "universes" / "zz500_history.csv",
    ]
    default_panel_paths = [normalized_root / "factors" / filename for filename in ("hs300_factor_panel.csv", "sz50_factor_panel.csv", "zz500_factor_panel.csv")]
    symbols = _iter_target_symbols(history_paths)
    trade_dates = _iter_trade_dates(panel_paths or default_panel_paths, max_trade_date=max_trade_date)
    if not trade_dates:
        raise ValueError("No trade dates found in baseline factor panels.")
    start_trade_date = date.fromisoformat(trade_dates[0])
    notice_start_date = (start_trade_date - timedelta(days=notice_lookback_days)).isoformat()
    external_dir = normalized_root / "external"
    events_dir = normalized_root / "events"

    macro_interest_rate_path = external_dir / "macro_interest_rate.csv"
    macro_monthly_path = external_dir / "macro_monthly_indicator.csv"
    dividend_events_path = events_dir / "dividend_event.csv"
    major_event_notice_path = events_dir / "major_event_notice.csv"
    announcement_text_path = events_dir / "announcement_text.csv"
    snapshot_metadata_path = events_dir / "extended_source_snapshot.json"

    _write_rows(
        macro_interest_rate_path,
        ["source_api", "metric_id", "metric_name", "pub_date", "available_date", "value", "expected_value", "previous_value"],
        build_macro_interest_rate_rows(trade_dates=trade_dates),
    )
    _write_rows(
        macro_monthly_path,
        ["source_api", "metric_id", "metric_name", "pub_date", "available_date", "value", "expected_value", "previous_value"],
        build_macro_monthly_rows(trade_dates=trade_dates),
    )
    _write_rows(
        dividend_events_path,
        [
            "stock_code",
            "report_period",
            "dividend_type",
            "pub_date",
            "available_date",
            "record_date",
            "ex_date",
            "pay_date",
            "bonus_ratio",
            "transfer_ratio",
            "cash_ratio",
            "plan_text",
            "source_api",
        ],
        build_dividend_rows(symbols=symbols, trade_dates=trade_dates),
    )
    announcement_rows, major_rows = build_notice_rows(
        symbols=symbols,
        trade_dates=trade_dates,
        start_date=notice_start_date,
        end_date=max_trade_date,
    )
    _write_rows(
        announcement_text_path,
        ["stock_code", "notice_type", "pub_date", "available_date", "title_text", "title_length", "keyword_score", "url", "source_api"],
        announcement_rows,
    )
    _write_rows(
        major_event_notice_path,
        ["stock_code", "notice_type", "pub_date", "available_date", "title_text", "title_length", "keyword_score", "severity_score", "url", "source_api"],
        major_rows,
    )
    snapshot_metadata_path.write_text(
        json.dumps(
            {
                "max_trade_date": max_trade_date,
                "notice_start_date": notice_start_date,
                "notice_end_date": max_trade_date,
                "notice_lookback_days": notice_lookback_days,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return ExtendedSourceBuildResult(
        macro_interest_rate_path=macro_interest_rate_path,
        macro_monthly_path=macro_monthly_path,
        dividend_events_path=dividend_events_path,
        major_event_notice_path=major_event_notice_path,
        announcement_text_path=announcement_text_path,
        snapshot_metadata_path=snapshot_metadata_path,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build normalized macro and event source tables for formal extended inputs.")
    parser.add_argument("--formal-root", type=Path, default=Path(__file__).resolve().parent / "formal")
    parser.add_argument("--max-trade-date", type=str, default="2026-03-30")
    parser.add_argument("--notice-lookback-days", type=int, default=30)
    args = parser.parse_args()

    result = build_formal_extended_sources(
        formal_root=args.formal_root,
        max_trade_date=args.max_trade_date,
        notice_lookback_days=args.notice_lookback_days,
    )
    for path in (
        result.macro_interest_rate_path,
        result.macro_monthly_path,
        result.dividend_events_path,
        result.major_event_notice_path,
        result.announcement_text_path,
    ):
        print(path.as_posix())


if __name__ == "__main__":
    main()
