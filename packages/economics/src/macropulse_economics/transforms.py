"""Derived indicators computed from native observations — transparent, testable, never filled.

A growth rate exists only where both the period and its lag period were officially published;
gaps propagate as missing values (no interpolation, no carrying forward).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from macropulse_economics.periods import shift

Point = tuple[str, float]


@dataclass(frozen=True, slots=True)
class Transform:
    kind: str  # "identity" | "growth"
    lag: int = 0
    description: str = ""


IDENTITY = Transform("identity", description="As published by the source.")

# (indicator, native source) -> transform. Anything not listed is shown as published.
TRANSFORMS: dict[tuple[str, str], Transform] = {
    ("real_gdp_qoq", "eurostat"): Transform(
        "growth", 1, "Quarter-on-quarter % change of real GDP levels (consecutive quarters only)."
    ),
    ("real_gdp_qoq", "fred"): Transform(
        "growth", 1, "Quarter-on-quarter % change of real GDP levels (not annualised)."
    ),
    ("real_gdp_yoy", "eurostat"): Transform(
        "growth", 4, "Year-on-year % change of real GDP levels."
    ),
    ("real_gdp_yoy", "fred"): Transform("growth", 4, "Year-on-year % change of real GDP levels."),
    ("inflation_yoy", "fred"): Transform("growth", 12, "12-month % change of the CPI index."),
}


def transform_for(indicator_id: str, source_id: str) -> Transform:
    return TRANSFORMS.get((indicator_id, source_id), IDENTITY)


def pct_change(points: Sequence[Point], lag: int) -> list[Point]:
    """Percentage change versus the period `lag` steps earlier, only where both exist and the base
    is non-zero. Works on quarterly and monthly labels."""
    by_period = dict(points)
    out: list[Point] = []
    for period, value in points:
        base = by_period.get(shift(period, -lag))
        if base is None or base == 0:
            continue
        out.append((period, (value / base - 1.0) * 100.0))
    return out


def apply(transform: Transform, points: Sequence[Point]) -> list[Point]:
    if transform.kind == "growth":
        return pct_change(points, transform.lag)
    return list(points)
