from __future__ import annotations

from datetime import date
import calendar


def iter_year_date_ranges(start_date: str, end_date: str) -> list[tuple[str, str, int]]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError(f"end_date must be on or after start_date: {start_date} > {end_date}")

    windows: list[tuple[str, str, int]] = []
    for year in range(start.year, end.year + 1):
        year_start = date(year, 1, 1)
        year_end = date(year, 12, 31)
        current_start = max(start, year_start)
        current_end = min(end, year_end)
        if current_start <= current_end:
            windows.append((current_start.isoformat(), current_end.isoformat(), year))
    return windows


def iter_month_date_ranges(start_date: str, end_date: str) -> list[tuple[str, str, int, int]]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    if end < start:
        raise ValueError(f"end_date must be on or after start_date: {start_date} > {end_date}")

    windows: list[tuple[str, str, int, int]] = []
    current_year = start.year
    current_month = start.month
    while True:
        month_start = date(current_year, current_month, 1)
        month_end = date(current_year, current_month, calendar.monthrange(current_year, current_month)[1])
        current_start = max(start, month_start)
        current_end = min(end, month_end)
        if current_start <= current_end:
            windows.append((current_start.isoformat(), current_end.isoformat(), current_year, current_month))
        if current_year == end.year and current_month == end.month:
            break
        if current_month == 12:
            current_year += 1
            current_month = 1
        else:
            current_month += 1
    return windows
