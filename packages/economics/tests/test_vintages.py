"""Revision analytics on ALFRED vintages: what was known when, first release versus today."""

from __future__ import annotations

from datetime import date

import pytest
from macropulse_economics.vintages import (
    RevisionPoint,
    derived_as_of,
    first_release_dates,
    revision_history,
    revision_summary,
    value_as_of,
)

from macropulse_economics.connectors.alfred import VintageObservation as V
from macropulse_economics.transforms import IDENTITY, Transform

QOQ = Transform("growth", 1)

# Tiny GDP level history with revisions (values are illustrative test numbers).
ROWS = [
    # 2007-Q4 appears in no vintage with a value: "." only
    V("2007-Q4", None, date(2008, 1, 30), None),
    # 2008-Q1: first 100.0, revised to 100.5 on 2008-05-29
    V("2008-Q1", 100.0, date(2008, 4, 30), date(2008, 5, 28)),
    V("2008-Q1", 100.5, date(2008, 5, 29), None),
    # 2008-Q2: first 101.0, revised down to 100.0 on 2008-08-28
    V("2008-Q2", 101.0, date(2008, 7, 31), date(2008, 8, 27)),
    V("2008-Q2", 100.0, date(2008, 8, 28), None),
    # 2008-Q3: first 100.0, unchanged since
    V("2008-Q3", 100.0, date(2008, 10, 30), None),
]


class TestValueAsOf:
    def test_returns_the_value_published_on_that_day(self) -> None:
        assert value_as_of(ROWS, "2008-Q1", date(2008, 5, 1)) == 100.0
        assert value_as_of(ROWS, "2008-Q1", date(2008, 5, 28)) == 100.0  # end day is inclusive
        assert value_as_of(ROWS, "2008-Q1", date(2008, 5, 29)) == 100.5

    def test_none_before_first_publication(self) -> None:
        assert value_as_of(ROWS, "2008-Q2", date(2008, 7, 30)) is None

    def test_none_for_an_unknown_period_or_a_missing_marker(self) -> None:
        assert value_as_of(ROWS, "1999-Q1", date(2020, 1, 1)) is None
        assert value_as_of(ROWS, "2007-Q4", date(2020, 1, 1)) is None

    def test_on_none_means_the_current_vintage(self) -> None:
        assert value_as_of(ROWS, "2008-Q2", None) == 100.0


class TestFirstReleaseDates:
    def test_earliest_vintage_with_a_value_per_period(self) -> None:
        assert first_release_dates(ROWS) == {
            "2008-Q1": date(2008, 4, 30),
            "2008-Q2": date(2008, 7, 31),
            "2008-Q3": date(2008, 10, 30),
        }  # 2007-Q4 was never published with a value


class TestDerivedAsOf:
    def test_identity_is_the_value_itself(self) -> None:
        assert derived_as_of(ROWS, "2008-Q2", date(2008, 8, 1), IDENTITY) == 101.0

    def test_growth_uses_both_levels_from_the_same_vintage(self) -> None:
        # On 2008-07-31: Q2 = 101.0 and Q1 (already revised) = 100.5
        assert derived_as_of(ROWS, "2008-Q2", date(2008, 7, 31), QOQ) == pytest.approx(
            (101.0 / 100.5 - 1) * 100
        )

    def test_growth_is_none_when_the_base_period_is_missing_in_that_vintage(self) -> None:
        assert derived_as_of(ROWS, "2008-Q1", date(2008, 4, 30), QOQ) is None

    def test_growth_is_none_for_a_zero_base(self) -> None:
        rows = [
            V("2008-Q1", 0.0, date(2008, 4, 30), None),
            V("2008-Q2", 1.0, date(2008, 7, 31), None),
        ]
        assert derived_as_of(rows, "2008-Q2", date(2008, 8, 1), QOQ) is None


class TestRevisionHistory:
    def test_first_release_versus_current_vintage_per_period(self) -> None:
        points = revision_history(ROWS, QOQ)
        # 2008-Q1 has no derivable first release (2007-Q4 missing) and is left out, not estimated.
        assert [p.period for p in points] == ["2008-Q2", "2008-Q3"]
        q2, q3 = points
        assert q2.first_published == date(2008, 7, 31)
        assert q2.first_value == pytest.approx(0.497512, abs=1e-6)  # 101 / 100.5 - 1
        assert q2.latest_value == pytest.approx(-0.497512, abs=1e-6)  # 100 / 100.5 - 1
        assert q2.revision == pytest.approx(-0.995025, abs=1e-6)
        assert q3.first_value == pytest.approx(0.0)  # 100 / 100 (Q2 already revised on 2008-10-30)
        assert q3.revision == pytest.approx(0.0)

    def test_sorted_by_period_whatever_the_row_order(self) -> None:
        assert [p.period for p in revision_history(list(reversed(ROWS)), QOQ)] == [
            "2008-Q2",
            "2008-Q3",
        ]

    def test_latest_value_is_none_when_the_current_vintage_cannot_derive_it(self) -> None:
        rows = [
            V(
                "2008-Q1", 100.0, date(2008, 4, 30), date(2009, 7, 30)
            ),  # dropped from later vintages
            V("2008-Q2", 101.0, date(2008, 7, 31), None),
        ]
        (point,) = revision_history(rows, QOQ)
        assert point.first_value == pytest.approx(1.0)
        assert point.latest_value is None
        assert point.revision is None


class TestRevisionSummary:
    def test_counts_mean_and_largest_absolute_revision(self) -> None:
        summary = revision_summary(revision_history(ROWS, QOQ))
        assert summary.count == 2
        assert summary.mean_abs_revision == pytest.approx(0.995025 / 2, abs=1e-6)
        assert summary.max_abs_revision == pytest.approx(0.995025, abs=1e-6)
        assert summary.max_abs_period == "2008-Q2"

    def test_sign_changes_list_periods_whose_sign_flipped(self) -> None:
        # zero is not negative: 0.0 -> 0.0 is no flip; +0.50 -> -0.50 is.
        assert revision_summary(revision_history(ROWS, QOQ)).sign_changes == ["2008-Q2"]

    def test_points_without_a_latest_value_do_not_count(self) -> None:
        points = [
            RevisionPoint("2008-Q2", date(2008, 7, 31), 1.0, None, None),
            RevisionPoint("2008-Q3", date(2008, 10, 30), 1.0, 1.5, 0.5),
        ]
        summary = revision_summary(points)
        assert summary.count == 1
        assert summary.mean_abs_revision == pytest.approx(0.5)

    def test_empty_history_has_no_statistics(self) -> None:
        summary = revision_summary([])
        assert summary.count == 0
        assert summary.mean_abs_revision is None
        assert summary.max_abs_revision is None
        assert summary.max_abs_period is None
        assert summary.sign_changes == []
