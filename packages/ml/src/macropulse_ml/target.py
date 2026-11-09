"""Technical-recession target.

At an as-of quarter t the label for horizon H is 1 when at least one pair of *consecutive* quarters
with *negative* real-GDP q/q growth lies entirely inside t+1 … t+H, else 0. Zero is not negative.
A label exists only when every quarter of the window has been observed: a window that reaches past
the last observed quarter is *censored*, and a window with a missing quarter is *missing* — neither
is ever turned into a 0.

Labels use the latest revised GDP, not the first release (no vintages are stored).
NBER recession dates are an external reference and are never used here.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from itertools import pairwise

from macropulse_economics.periods import shift

HORIZONS = (2, 4)


class LabelStatus(StrEnum):
    OBSERVED = "observed"
    CENSORED = "censored"  # the window ends after the last observed quarter
    MISSING = "missing"  # a quarter inside the window has no growth value


@dataclass(frozen=True, slots=True)
class Label:
    value: int | None
    status: LabelStatus
    window: tuple[str, ...]


def quarter_index(period: str) -> int:
    """'2026-Q3' -> 2026*4 + 2. Comparable and steppable."""
    year, q = period.split("-Q")
    return int(year) * 4 + int(q) - 1


def technical_recession_label(
    gdp_qoq: dict[str, float], as_of: str, horizon: int, last_observed: str
) -> Label:
    if horizon < 2:
        raise ValueError("A pair of consecutive quarters needs a horizon of at least 2")
    window = tuple(shift(as_of, k) for k in range(1, horizon + 1))
    if quarter_index(window[-1]) > quarter_index(last_observed):
        return Label(None, LabelStatus.CENSORED, window)
    values = [gdp_qoq.get(p) for p in window]
    if any(v is None for v in values):
        return Label(None, LabelStatus.MISSING, window)
    observed = [v for v in values if v is not None]
    event = any(a < 0 and b < 0 for a, b in pairwise(observed))
    return Label(int(event), LabelStatus.OBSERVED, window)


def technical_recessions(gdp_qoq: dict[str, float]) -> list[tuple[str, str]]:
    """Runs of two or more consecutive negative quarters, as (first, last) quarter — for event
    dating and documentation. A missing quarter breaks a run."""
    runs: list[tuple[str, str]] = []
    start: str | None = None
    prev: str | None = None
    for period in sorted(gdp_qoq, key=quarter_index):
        negative = gdp_qoq[period] < 0
        contiguous = prev is not None and quarter_index(period) == quarter_index(prev) + 1
        if negative and start is not None and contiguous:
            prev = period
            continue
        if start is not None and prev is not None and prev != start:
            runs.append((start, prev))
        start = period if negative else None
        prev = period
    if start is not None and prev is not None and prev != start:
        runs.append((start, prev))
    return runs
