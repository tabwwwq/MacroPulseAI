"""Revision analytics on ALFRED vintages: what was known when, first release versus today.

A *vintage* is one real-time snapshot of a series: for every observation period, ALFRED records
which value was the published one during each real-time window. The same period therefore appears
once per vintage in which it was published, and its value can change across vintages (a revision).

Growth transforms are computed from both levels taken from the *same* vintage (the same ``on``
date). Comparing a level from one vintage against a level from another is meaningless because the
base year and the benchmark revisions differ between vintages, so the base period is always
resolved at the same real-time date as the current period.

Nothing is ever estimated: a derived value is ``None`` whenever any input level is missing or the
base is zero, and periods whose first release cannot be derived are left out of the revision
history rather than filled in.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date

from macropulse_economics.connectors.alfred import VintageObservation
from macropulse_economics.periods import period_start, shift
from macropulse_economics.transforms import Transform


@dataclass(frozen=True, slots=True)
class RevisionPoint:
    """One period's first published derived value versus its current (latest) value."""

    period: str
    first_published: date
    first_value: float
    latest_value: float | None
    revision: float | None  # latest_value - first_value, None when latest_value is None


@dataclass(frozen=True, slots=True)
class RevisionSummary:
    """Aggregate statistics over a list of :class:`RevisionPoint`."""

    count: int  # points with a revision (latest_value not None)
    mean_abs_revision: float | None
    max_abs_revision: float | None
    max_abs_period: str | None
    # periods where (first_value < 0) != (latest_value < 0); zero is not negative
    sign_changes: list[str]


def _index(rows: Sequence[VintageObservation]) -> dict[str, list[VintageObservation]]:
    """Group rows by period, preserving the order in which each period's rows appear."""
    by_period: dict[str, list[VintageObservation]] = {}
    for row in rows:
        by_period.setdefault(row.period, []).append(row)
    return by_period


def value_as_of(rows: Sequence[VintageObservation], period: str, on: date | None) -> float | None:
    """The value of ``period`` whose real-time window contains ``on``.

    ``on=None`` selects the current vintage (the row whose ``realtime_end`` is ``None``). Returns
    the row's value (which may be ``None`` for a "." marker) or ``None`` when no row matches.
    """
    return _pick([r for r in rows if r.period == period], on)


def first_release_dates(rows: Sequence[VintageObservation]) -> dict[str, date]:
    """For each period, the earliest ``realtime_start`` among its rows with a non-None value.

    Periods that never had a value are absent.
    """
    result: dict[str, date] = {}
    for row in rows:
        if row.value is None:
            continue
        current = result.get(row.period)
        if current is None or row.realtime_start < current:
            result[row.period] = row.realtime_start
    return result


def derived_as_of(
    rows: Sequence[VintageObservation],
    period: str,
    on: date | None,
    transform: Transform,
) -> float | None:
    """The derived value of ``period`` as of real-time date ``on`` under ``transform``.

    Identity returns the value itself. Growth with lag ``k`` returns ``(v / base - 1) * 100``
    where both ``v`` and ``base`` are resolved from the same date ``on``. Returns ``None`` when
    either level is missing or the base is zero. Any other transform kind raises ``ValueError``.
    """
    return _derived_from_index(_index(rows), period, on, transform)


def revision_history(
    rows: Sequence[VintageObservation], transform: Transform
) -> list[RevisionPoint]:
    """One :class:`RevisionPoint` per period whose first release can be derived.

    Periods are sorted by period start. A period is skipped (never estimated) when its first
    release cannot be derived.
    """
    by_period = _index(rows)
    releases = first_release_dates(rows)
    ordered = sorted(releases, key=lambda p: (period_start(p), p))

    points: list[RevisionPoint] = []
    for period in ordered:
        first_date = releases[period]
        first = _derived_from_index(by_period, period, first_date, transform)
        if first is None:
            continue
        latest = _derived_from_index(by_period, period, None, transform)
        revision = None if latest is None else latest - first
        points.append(
            RevisionPoint(
                period=period,
                first_published=first_date,
                first_value=first,
                latest_value=latest,
                revision=revision,
            )
        )
    return points


def _derived_from_index(
    by_period: dict[str, list[VintageObservation]],
    period: str,
    on: date | None,
    transform: Transform,
) -> float | None:
    """Like :func:`derived_as_of` but reading from a pre-built per-period index."""
    if transform.kind == "identity":
        return _value_from_index(by_period, period, on)
    if transform.kind == "growth":
        v = _value_from_index(by_period, period, on)
        if v is None:
            return None
        base = _value_from_index(by_period, shift(period, -transform.lag), on)
        if base is None or base == 0:
            return None
        return (v / base - 1.0) * 100.0
    raise ValueError(f"Unknown transform kind: {transform.kind!r}")


def _value_from_index(
    by_period: dict[str, list[VintageObservation]], period: str, on: date | None
) -> float | None:
    return _pick(by_period.get(period, ()), on)


def _pick(rows: Sequence[VintageObservation], on: date | None) -> float | None:
    """Value of the row (of one period) whose real-time window contains ``on``; ends inclusive."""
    for row in rows:
        if on is None:
            if row.realtime_end is None:
                return row.value
        elif row.realtime_start <= on and (row.realtime_end is None or on <= row.realtime_end):
            return row.value
    return None


def revision_summary(points: Sequence[RevisionPoint]) -> RevisionSummary:
    """Aggregate statistics over ``points``.

    Statistics are computed only over points whose ``revision`` is not ``None``. ``max_abs_period``
    is the period of the largest absolute revision (the first one on ties). Sign changes are
    reported in period order. An empty input yields count 0, ``None`` statistics and an empty list.
    """
    # (point, revision, latest) for points with a revision; the tuple keeps the types narrowed.
    revised = [
        (p, p.revision, p.latest_value)
        for p in points
        if p.revision is not None and p.latest_value is not None
    ]
    if not revised:
        return RevisionSummary(0, None, None, None, [])

    abs_revisions = [abs(r) for _, r, _ in revised]
    mean_abs = sum(abs_revisions) / len(abs_revisions)
    max_abs = max(abs_revisions)
    max_abs_period = next(p.period for p, r, _ in revised if abs(r) == max_abs)
    sign_changes = [p.period for p, _, latest in revised if (p.first_value < 0) != (latest < 0)]

    return RevisionSummary(
        count=len(revised),
        mean_abs_revision=mean_abs,
        max_abs_revision=max_abs,
        max_abs_period=max_abs_period,
        sign_changes=sign_changes,
    )
