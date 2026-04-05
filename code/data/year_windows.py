from __future__ import annotations

from datetime import date


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
