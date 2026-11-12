"""A whole series as it was published on one day (one vintage), derived like the live data."""

from __future__ import annotations

from datetime import date

import pytest

from macropulse_economics.connectors.alfred import VintageObservation as V
from macropulse_economics.transforms import IDENTITY, Transform
from macropulse_economics.vintages import vintage_series

QOQ = Transform("growth", 1)
YOY_Q = Transform("growth", 4)

LEVELS = [
    V("2007-Q4", 98.0, date(2008, 1, 30), None),
    V("2008-Q1", 100.0, date(2008, 4, 30), date(2008, 5, 28)),
    V("2008-Q1", 100.5, date(2008, 5, 29), None),
    V("2008-Q2", 101.0, date(2008, 7, 31), date(2008, 8, 27)),
    V("2008-Q2", 100.0, date(2008, 8, 28), None),
    V("2008-Q3", None, date(2008, 10, 30), date(2008, 11, 25)),  # "." in that vintage
    V("2008-Q3", 99.0, date(2008, 11, 26), None),
]


def test_levels_as_published_on_a_day() -> None:
    assert vintage_series(LEVELS, date(2008, 8, 1), IDENTITY) == {
        "2007-Q4": 98.0,
        "2008-Q1": 100.5,
        "2008-Q2": 101.0,
    }


def test_growth_uses_levels_from_that_same_day() -> None:
    got = vintage_series(LEVELS, date(2008, 8, 1), QOQ)
    assert set(got) == {"2008-Q1", "2008-Q2"}  # 2007-Q4 has no base in this vintage
    assert got["2008-Q1"] == pytest.approx((100.5 / 98.0 - 1) * 100)
    assert got["2008-Q2"] == pytest.approx((101.0 / 100.5 - 1) * 100)


def test_nothing_published_after_the_day_leaks_in() -> None:
    assert "2008-Q3" not in vintage_series(LEVELS, date(2008, 11, 1), IDENTITY)  # only "."
    assert vintage_series(LEVELS, date(2008, 11, 26), IDENTITY)["2008-Q3"] == 99.0
    assert vintage_series(LEVELS, date(2008, 1, 29), IDENTITY) == {}


def test_missing_marker_and_zero_base_give_no_value() -> None:
    rows = [
        V("2020-01", 0.0, date(2020, 2, 13), None),
        V("2020-02", 5.0, date(2020, 3, 11), None),
        V("2020-03", None, date(2020, 4, 10), None),
    ]
    assert vintage_series(rows, date(2020, 5, 1), Transform("growth", 1)) == {}
    assert vintage_series(rows, date(2020, 5, 1), IDENTITY) == {"2020-01": 0.0, "2020-02": 5.0}


def test_on_none_is_the_current_vintage() -> None:
    assert vintage_series(LEVELS, None, IDENTITY)["2008-Q2"] == 100.0


def test_year_on_year_growth() -> None:
    rows = [
        V("2007-Q2", 90.0, date(2007, 7, 27), None),
        V("2008-Q2", 99.0, date(2008, 7, 31), None),
    ]
    assert vintage_series(rows, date(2008, 8, 1), YOY_Q) == {"2008-Q2": pytest.approx(10.0)}


def test_matches_derived_as_of_for_every_period() -> None:
    from macropulse_economics.vintages import derived_as_of  # noqa: PLC0415

    day = date(2008, 9, 1)
    got = vintage_series(LEVELS, day, QOQ)
    for period in {r.period for r in LEVELS}:
        expected = derived_as_of(LEVELS, period, day, QOQ)
        assert got.get(period) == (pytest.approx(expected) if expected is not None else None)


def test_unknown_transform_kind_is_rejected() -> None:
    with pytest.raises(ValueError, match="transform"):
        vintage_series(LEVELS, date(2008, 9, 1), Transform("ratio", 1))
