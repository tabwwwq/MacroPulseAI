---
type: codex-run
name: local-vintages
date: 2026-11-12
time: "11:49"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-vintages

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-12 11:49. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```python
> """Revision analytics on ALFRED vintages: what was known when, first release versus today.
>
> A *vintage* is one real-time snapshot of a series: for every observation period, ALFRED records
> which value was the published one during each real-time window. The same period therefore appears
> once per vintage in which it was published, and its value can change across vintages (a revision).
>
> Growth transforms are computed from both levels taken from the *same* vintage (the same ``on``
> date). Comparing a level from one vintage against a level from another is meaningless because the
> base year and the benchmark revisions differ between vintages, so the base period is always
> resolved at the same real-time date as the current period.
>
> Nothing is ever estimated: a derived value is ``None`` whenever any input level is missing or the
> base is zero, and periods whose first release cannot be derived are left out of the revision
> history rather than filled in.
> """
>
> from __future__ import annotations
>
> from collections.abc import Sequence
> from dataclasses import dataclass
> from datetime import date
>
> from macropulse_economics.connectors.alfred import VintageObservation
> from macropulse_economics.periods import period_start, shift
> from macropulse_economics.transforms import Transform
>
>
> @dataclass(frozen=True, slots=True)
> class RevisionPoint:
>     """One period's first published derived value versus its current (latest) value."""
>
>     period: str
>     first_published: date
>     first_value: float
>     latest_value: float | None
>     revision: float | None  # latest_value - first_value, None when latest_value is None
>
>
> @dataclass(frozen=True, slots=True)
> class RevisionSummary:
>     """Aggregate statistics over a list of :class:`RevisionPoint`."""
>
>     count: int  # points with a revision (latest_value not None)
>     mean_abs_revision: float | None
>     max_abs_revision: float | None
>     max_abs_period: str | None
>     sign_changes: list[str]  # periods where (first_value < 0) != (latest_value < 0); zero is not negative
>
>
> def _index(rows: Sequence[VintageObservation]) -> dict[str, list[VintageObservation]]:
>     """Group rows by period, preserving the order in which each period's rows appear."""
>     by_period: dict[str, list[VintageObservation]] = {}
>     for row in rows:
>         by_period.setdefault(row.period, []).append(row)
>     return by_period
>
>
> def value_as_of(
>     rows: Sequence[VintageObservation], period: str, on: date | None
> ) -> float | None:
>     """The value of ``period`` whose real-time window contains ``on``.
>
>     ``on=None`` selects the current vintage (the row whose ``realtime_end`` is ``None``). Returns
>     the row's value (which may be ``None`` for a "." marker) or ``None`` when no row matches.
>     """
>     for row in rows:
>         if row.period != period:
>             continue
>         if on is None:
>             if row.realtime_end is None:
>                 return row.value
>         else:
>             if row.realtime_start <= on and (
>                 row.realtime_end is None or on <= row.realtime_end
>             ):
>                 return row.value
>     return None
>
>
> def first_release_dates(rows: Sequence[VintageObservation]) -> dict[str, date]:
>     """For each period, the earliest ``realtime_start`` among its rows with a non-None value.
>
>     Periods that never had a value are absent.
>     """
>     result: dict[str, date] = {}
>     for row in rows:
>         if row.value is None:
>             continue
>         current = result.get(row.period)
>         if current is None or row.realtime_start < current:
>             result[row.period] = row.realtime_start
>     return result
>
>
> def derived_as_of(
>     rows: Sequence[VintageObservation],
>     period: str,
>     on: date | None,
>     transform: Transform,
> ) -> float | None:
>     """The derived value of ``period`` as of real-time date ``on`` under ``transform``.
>
>     Identity returns the value itself. Growth with lag ``k`` returns ``(v / base - 1) * 100``
>     where both ``v`` and ``base`` are resolved from the same date ``on``. Returns ``None`` when
>     either level is missing or the base is zero. Any other transform kind raises ``ValueError``.
>     """
>     if transform.kind == "identity":
>         return value_as_of(rows, period, on)
>     if transform.kind == "growth":
>         v = value_as_of(rows, period, on)
>         if v is None:
>             return None
>         base = value_as_of(rows, shift(period, -transform.lag), on)
>         if base is None or base == 0:
>             return None
>         return (v / base - 1.0) * 100.0
>     raise ValueError(f"Unknown transform kind: {transform.kind!r}")
>
>
> def revision_history(
>     rows: Sequence[VintageObservation], transform: Transform
> ) -> list[RevisionPoint]:
>     """One :class:`RevisionPoint` per period whose first release can be derived.
>
>     Periods are sorted by period start. A period is skipped (never estimated) when its first
>     release cannot be derived.
>     """
>     by_period = _index(rows)
>     releases = first_release_dates(rows)
>     ordered = sorted(releases, key=lambda p: (period_start(p), p))
>
>     points: list[RevisionPoint] = []
>     for period in ordered:
>         first_date = releases[period]
>         first = _derived_from_index(by_period, period, first_date, transform)
>         if first is None:
>             continue
>         latest = _derived_from_index(by_period, period, None, transform)
>         revision = None if latest is None else latest - first
>         points.append(
>             RevisionPoint(
>                 period=period,
>                 first_published=first_date,
>                 first_value=first,
>                 latest_value=latest,
>                 revision=revision,
>             )
>         )
>     return points
>
>
> def _derived_from_index(
>     by_period: dict[str, list[VintageObservation]],
>     period: str,
>     on: date | None,
>     transform: Transform,
> ) -> float | None:
>     """Like :func:`derived_as_of` but reading from a pre-built per-period index."""
>     if transform.kind == "identity":
>         return _value_from_index(by_pe
> …(truncated)

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the pure revision-analytics module for ALFRED vintages.
>
> ## Files
> - CREATE `packages/economics/src/macropulse_economics/vintages.py` — the only file you write.
> - CONTEXT (provided below, do not change): `packages/economics/tests/test_vintages.py` (the specification —
>   read every assertion), `packages/economics/src/macropulse_economics/transforms.py` (`Transform`: kind
>   "identity" or "growth" with a `lag`), `packages/economics/src/macropulse_economics/periods.py` (`shift`),
>   and the dataclass `VintageObservation(period, value, realtime_start, realtime_end)` from
>   `macropulse_economics.connectors.alfred` (value None = not available in that vintage; realtime_end None =
>   still current).
>
> ## API
> ```python
> def value_as_of(rows: Sequence[VintageObservation], period: str, on: date | None) -> float | None
> def first_release_dates(rows: Sequence[VintageObservation]) -> dict[str, date]
> def derived_as_of(rows: Sequence[VintageObservation], period: str, on: date | None, transform: Transform) -> float | None
> def revision_history(rows: Sequence[VintageObservation], transform: Transform) -> list[RevisionPoint]
> def revision_summary(points: Sequence[RevisionPoint]) -> RevisionSummary
>
> @dataclass(frozen=True, slots=True)
> class RevisionPoint:
>     period: str
>     first_published: date
>     first_value: float
>     latest_value: float | None
>     revision: float | None          # latest_value - first_value, None when latest_value is None
>
> @dataclass(frozen=True, slots=True)
> class RevisionSummary:
>     count: int                      # points with a revision (latest_value not None)
>     mean_abs_revision: float | None
>     max_abs_revision: float | None
>     max_abs_period: str | None
>     sign_changes: list[str]         # periods where (first_value < 0) != (latest_value < 0); zero is not negative
> ```
>
> ## Rules
> 1. `value_as_of(rows, period, on)`: the value of the row for `period` whose real-time window contains `on`
>    (`realtime_start <= on` and (`realtime_end is None` or `on <= realtime_end`), both ends inclusive).
>    `on=None` means the current vintage: the row with `realtime_end is None`. Returns the row's value (which
>    may be None for a "." marker) or None when no row matches.
> 2. `first_release_dates`: for each period, the earliest `realtime_start` among its rows with a non-None value.
>    Periods that never had a value are absent.
> 3. `derived_as_of`: identity → `value_as_of(period, on)`. growth with lag k → `(v / base - 1) * 100` where
>    `v = value_as_of(period, on)` and `base = value_as_of(shift(period, -k), on)` — BOTH from the same date `on`.
>    None if either is None or `base == 0`. Any other transform kind → `ValueError`.
> 4. `revision_history`: for each period in `first_release_dates`, sorted by period start (use
>    `periods.period_start`): `first = derived_as_of(rows, period, first_date, transform)`; skip the period when
>    `first` is None (never estimate). `latest = derived_as_of(rows, period, None, transform)`.
> 5. `revision_summary`: statistics only over points whose `revision` is not None; `max_abs_period` is the
>    period of the largest absolute revision (first one on ties); sign changes in period order. Empty → count 0,
>    None statistics, empty list.
> 6. Build an index once per call (dict period → rows) instead of scanning all rows for every lookup inside
>    `revision_history` — the real series have ~5,000 rows. Keep the public functions' behaviour identical.
> 7. Python 3.12, `from __future__ import annotations`, full type hints (mypy --strict), ruff (line length 100).
>    Standard library only. Module docstring: what a vintage is, that growth uses both levels from the same
>    vintage (base-year changes between vintages make cross-vintage level comparisons meaningless), and that
>    nothing is estimated.
>
> Output only the file, in ONE fenced code block (three backticks, language python) — do not nest fences.
>
> # Output file
>
> `packages/economics/src/macropulse_economics/vintages.py`
>
> # Context files
>
> ## `packages/economics/tests/test_vintages.py`
>
> ```py
> """Revision analytics on ALFRED vintages: what was known when, first release versus today."""
>
> from __future__ import annotations
>
> from datetime import date
>
> import pytest
> from macropulse_economics.vintages import (
>     RevisionPoint,
>     derived_as_of,
>     first_release_dates,
>     revision_history,
>     revision_summary,
>     value_as_of,
> )
>
> from macropulse_economics.connectors.alfred import VintageObservation as V
> from macropulse_economics.transforms import IDENTITY, Transform
>
> QOQ = Transform("growth", 1)
>
> # Tiny GDP level history with revisions (values are illustrative test numbers).
> ROWS = [
>     # 2007-Q4 appears in no vintage with a value: "." only
>     V("2007-Q4", None, date(2008, 1, 30), None),
>     # 2008-Q1: first 100.0, revised to 100.5 on 2008-05-29
>     V("2008-Q1", 100.0, date(2008, 4, 30), date(2008, 5, 28)),
>     V("2008-Q1", 100.5, date(2008, 5, 29), None),
>     # 2008-Q2: first 101.0, revised down to 100.0 on 2008-08-28
>     V("2008-Q2", 101.0, date(2008, 7, 31), date(2008, 8, 27)),
>     V("2008-Q2", 100.0, date(2008, 8, 28), None),
>     # 2008-Q3: first 100.0, unchanged since
>     V("2008-Q3", 100.0, date(2008, 10, 30), None),
> ]
>
>
> class TestValueAsOf:
>     def test_returns_the_value_published_on_that_day(self) -> None:
>         assert value_as_of(ROWS, "2008-Q1", date(2008, 5, 1)) == 100.0
>         assert value_as_of(ROWS, "2008-Q1", date(2008, 5, 28)) == 100.0  # end day is inclusive
>         assert value_as_of(ROWS, "2008-Q1", date(2008, 5, 29)) == 100.5
>
>     def test_none_before_first_publication(self) -> None:
>         assert value_as_of(ROWS, "2008-Q2", date(2008, 7, 30)) is None
>
>     def test_none_for_an_unknown_period_or_a_missing_marker(self) -> None:
>         assert value_as_of(ROWS, "1999-Q1", date(2020, 1, 1)) is None
>         assert value_as_of(ROWS, "2007-Q4", date(2020, 1, 1)) is None
>
>     def test_on_none_means_the_current_vintage(self) -> None:
>         assert value_as_of(ROWS, "2008-Q2", None) == 100.0
>
>
> class Test
> …(truncated)
