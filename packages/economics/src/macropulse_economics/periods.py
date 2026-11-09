"""Period labels used across sources: "2026-Q3" (quarterly), "2026-10" (monthly) and
"2026-09-16" (daily or event-dated). Helpers parse them to start dates and step them for lagged
transforms."""

from __future__ import annotations

import re
from datetime import date, timedelta

_QUARTER = re.compile(r"^(\d{4})-Q([1-4])$")
_MONTH = re.compile(r"^(\d{4})-(\d{2})$")
_DAY = re.compile(r"^(\d{4})-(\d{2})-(\d{2})$")


class PeriodError(ValueError):
    pass


def period_start(period: str) -> date:
    """First calendar day covered by the period."""
    if m := _QUARTER.match(period):
        return date(int(m[1]), (int(m[2]) - 1) * 3 + 1, 1)
    if m := _MONTH.match(period):
        return date(int(m[1]), int(m[2]), 1)
    if m := _DAY.match(period):
        return date(int(m[1]), int(m[2]), int(m[3]))
    raise PeriodError(f"Unrecognised period label: {period!r}")


def period_end(period: str) -> date:
    """Last calendar day covered by the period (a day label is its own end)."""
    if _QUARTER.match(period) or _MONTH.match(period):
        return period_start(shift(period, 1)) - timedelta(days=1)
    return period_start(period)


def days_since_end(period: str, today: date) -> int:
    """Age of a period measured from its end, the earliest moment it could have been published."""
    return (today - period_end(period)).days


def quarter_of(d: date) -> str:
    return f"{d.year}-Q{(d.month - 1) // 3 + 1}"


def month_of(d: date) -> str:
    return f"{d.year}-{d.month:02d}"


def shift(period: str, steps: int) -> str:
    """Move a quarterly or monthly label by `steps` periods (negative = earlier)."""
    if m := _QUARTER.match(period):
        idx = int(m[1]) * 4 + int(m[2]) - 1 + steps
        return f"{idx // 4}-Q{idx % 4 + 1}"
    if m := _MONTH.match(period):
        idx = int(m[1]) * 12 + int(m[2]) - 1 + steps
        return f"{idx // 12}-{idx % 12 + 1:02d}"
    raise PeriodError(f"Only quarterly/monthly periods can be shifted: {period!r}")


def normalise_fred_date(raw: str, frequency: str) -> str:
    """FRED dates every observation by its period's first day; map to our labels."""
    d = date.fromisoformat(raw)
    if frequency == "quarterly":
        if d.month not in (1, 4, 7, 10) or d.day != 1:
            raise PeriodError(f"Not a quarter start: {raw}")
        return quarter_of(d)
    if frequency == "monthly":
        if d.day != 1:
            raise PeriodError(f"Not a month start: {raw}")
        return month_of(d)
    return d.isoformat()
