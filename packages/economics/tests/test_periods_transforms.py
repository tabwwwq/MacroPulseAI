from __future__ import annotations

from datetime import date

import pytest

from macropulse_economics.periods import (
    PeriodError,
    days_since_end,
    normalise_fred_date,
    period_end,
    period_start,
    shift,
)
from macropulse_economics.transforms import IDENTITY, apply, pct_change, transform_for


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("2026-Q1", date(2026, 1, 1)),
        ("2026-Q4", date(2026, 10, 1)),
        ("2026-10", date(2026, 10, 1)),
        ("2026-09-16", date(2026, 9, 16)),
    ],
)
def test_period_start(label: str, expected: date) -> None:
    assert period_start(label) == expected


@pytest.mark.parametrize("label", ["2026-Q5", "2026Q1", "26-01", "2026-1", ""])
def test_period_start_rejects_unknown_labels(label: str) -> None:
    with pytest.raises(PeriodError):
        period_start(label)


@pytest.mark.parametrize(
    ("label", "steps", "expected"),
    [
        ("2026-Q1", -1, "2025-Q4"),
        ("2025-Q4", 1, "2026-Q1"),
        ("2026-Q3", -4, "2025-Q3"),
        ("2026-01", -1, "2025-12"),
        ("2026-10", -12, "2025-10"),
        ("2025-12", 1, "2026-01"),
    ],
)
def test_shift_crosses_year_boundaries(label: str, steps: int, expected: str) -> None:
    assert shift(label, steps) == expected


def test_daily_labels_cannot_be_shifted() -> None:
    with pytest.raises(PeriodError):
        shift("2026-09-16", 1)


def test_fred_dates_map_to_period_labels() -> None:
    assert normalise_fred_date("2026-07-01", "quarterly") == "2026-Q3"
    assert normalise_fred_date("2026-10-01", "monthly") == "2026-10"
    assert normalise_fred_date("2026-11-06", "daily") == "2026-11-06"
    with pytest.raises(PeriodError):
        normalise_fred_date("2026-08-01", "quarterly")  # not a quarter start
    with pytest.raises(PeriodError):
        normalise_fred_date("2026-10-15", "monthly")


def test_pct_change_needs_both_periods_and_never_fills_gaps() -> None:
    points = [("2025-Q1", 100.0), ("2025-Q2", 101.0), ("2025-Q4", 103.0), ("2026-Q1", 102.0)]
    growth = dict(pct_change(points, 1))
    assert set(growth) == {"2025-Q2", "2026-Q1"}  # Q3 missing -> no Q3 and no Q4 growth
    assert growth["2025-Q2"] == pytest.approx(1.0)
    assert growth["2026-Q1"] == pytest.approx(-0.970873786, rel=1e-6)


def test_pct_change_skips_zero_base_and_year_on_year_uses_lag_four() -> None:
    assert pct_change([("2025-01", 0.0), ("2025-02", 5.0)], 1) == []
    quarters = [(f"{y}-Q{q}", float(y * 10 + q)) for y in (2024, 2025) for q in (1, 2, 3, 4)]
    yoy = pct_change(quarters, 4)
    assert [p for p, _ in yoy] == ["2025-Q1", "2025-Q2", "2025-Q3", "2025-Q4"]
    assert yoy[0][1] == pytest.approx((20251 / 20241 - 1) * 100)


def test_zero_growth_stays_zero_not_negative() -> None:
    ((period, value),) = pct_change([("2025-Q1", 50.0), ("2025-Q2", 50.0)], 1)
    assert period == "2025-Q2"
    assert value == 0.0


def test_transform_registry() -> None:
    assert transform_for("real_gdp_qoq", "eurostat").lag == 1
    assert transform_for("real_gdp_yoy", "fred").lag == 4
    assert transform_for("inflation_yoy", "fred").lag == 12  # CPI index -> 12-month change
    # Eurostat publishes the HICP annual rate directly: shown as published.
    assert transform_for("inflation_yoy", "eurostat") is IDENTITY
    assert apply(IDENTITY, [("2026-10", 3.8)]) == [("2026-10", 3.8)]


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("2026-Q2", date(2026, 6, 30)),
        ("2025-Q4", date(2025, 12, 31)),
        ("2024-02", date(2024, 2, 29)),
        ("2026-12", date(2026, 12, 31)),
        ("2026-09-16", date(2026, 9, 16)),
    ],
)
def test_period_end(label: str, expected: date) -> None:
    assert period_end(label) == expected


def test_age_is_measured_from_the_end_of_the_period() -> None:
    assert days_since_end("2026-Q2", date(2026, 11, 9)) == 132
    assert days_since_end("2026-10", date(2026, 11, 9)) == 9
