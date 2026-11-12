---
type: codex-run
name: local-vintage-series
date: 2026-11-12
time: "14:47"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-vintage-series

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-12 14:47. Sandbox `local-single-file`, network off, exit code 0.
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
>     # periods where (first_value < 0) != (latest_value < 0); zero is not negative
>     sign_changes: list[str]
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
> def value_as_of(rows: Sequence[VintageObservation], period: str, on: date | None) -> float | None:
>     """The value of ``period`` whose real-time window contains ``on``.
>
>     ``on=None`` selects the current vintage (the row whose ``realtime_end`` is ``None``). Returns
>     the row's value (which may be ``None`` for a "." marker) or ``None`` when no row matches.
>     """
>     return _pick([r for r in rows if r.period == period], on)
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
>     return _derived_from_index(_index(rows), period, on, transform)
>
>
> def vintage_series(
>     rows: Sequence[VintageObservation], on: date | None, transform: Transform
> ) -> dict[str, float]:
>     """The whole series as a user could have downloaded it on day ``on``.
>
>     For every period whose value is non-None in the vintage valid on ``on`` (``on=None`` is the
>     current vintage) and whose derivation is defined, the derived value is returned. The result
>     is keyed by period and ordered by ``period_start``. Nothing published after ``on`` appears.
>     """
>     by_period = _index(rows)
>     values: dict[str, float] = {}
>     for period in sorted(by_period, key=lambda p: (period_start(p), p)):
>         v = _pick(by_period[period], on)
>         if v is None:
>             continue
>         if transform.kind == "identity":
>             values[period] = v
>         elif transform.kind == "growth":
>             base = _pick(by_period.get(shift(period, -transform.lag), ()), on)
>             if base is None or base == 0:
>                 continue
>             values[period] = (v / base - 1.0) * 100.0
>         else:
>             raise ValueError(f"Unknown transform kind: {transform.kind!r}")
>     return values
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
> …(truncated)

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: add one function to the vintage analytics module: a whole series as published on one day.
>
> ## Files
> - EDIT `packages/economics/src/macropulse_economics/vintages.py` — the only file you write. Return the
>   COMPLETE file: everything that is there now, unchanged, plus the new function.
> - CONTEXT (provided below, do not change): `packages/economics/tests/test_vintage_series.py` (the specification),
>   the current `vintages.py`, and `packages/economics/src/macropulse_economics/transforms.py`.
>
> ## API (add after `derived_as_of`)
>     def vintage_series(
>         rows: Sequence[VintageObservation], on: date | None, transform: Transform
>     ) -> dict[str, float]:
>
> ## Rules
> 1. Result: period -> derived value for every period that has a non-None value in the vintage valid on `on`
>    (same window rule as `value_as_of`; `on=None` = current vintage) AND whose derivation is defined.
> 2. identity: the value itself. growth with lag k: `(v / base - 1) * 100` with `base` = the value of
>    `shift(period, -k)` in the SAME vintage; skip the period when the base is missing or 0.
>    Any other `transform.kind` raises `ValueError` whose message contains "transform".
> 3. Must give exactly what `derived_as_of(rows, period, on, transform)` gives for every period, but in one pass:
>    build `_index(rows)` once, pick each period's value once with `_pick`, then derive from that dict. Never
>    call `derived_as_of` inside the loop. Insertion order: by `period_start` of the period.
> 4. Docstring: this is the series a user could have downloaded on day `on` — nothing published later.
> 5. Keep mypy --strict and ruff (line length 100) clean. Do not change any existing function.
>
> Output only the file, in ONE fenced code block (three backticks, language python) — do not nest fences.
>
> # Output file
>
> `packages/economics/src/macropulse_economics/vintages.py`
>
> # Context files
>
> ## `packages/economics/tests/test_vintage_series.py`
>
> ```py
> """A whole series as it was published on one day (one vintage), derived like the live data."""
>
> from __future__ import annotations
>
> from datetime import date
>
> import pytest
>
> from macropulse_economics.connectors.alfred import VintageObservation as V
> from macropulse_economics.transforms import IDENTITY, Transform
> from macropulse_economics.vintages import vintage_series
>
> QOQ = Transform("growth", 1)
> YOY_Q = Transform("growth", 4)
>
> LEVELS = [
>     V("2007-Q4", 98.0, date(2008, 1, 30), None),
>     V("2008-Q1", 100.0, date(2008, 4, 30), date(2008, 5, 28)),
>     V("2008-Q1", 100.5, date(2008, 5, 29), None),
>     V("2008-Q2", 101.0, date(2008, 7, 31), date(2008, 8, 27)),
>     V("2008-Q2", 100.0, date(2008, 8, 28), None),
>     V("2008-Q3", None, date(2008, 10, 30), date(2008, 11, 25)),  # "." in that vintage
>     V("2008-Q3", 99.0, date(2008, 11, 26), None),
> ]
>
>
> def test_levels_as_published_on_a_day() -> None:
>     assert vintage_series(LEVELS, date(2008, 8, 1), IDENTITY) == {
>         "2007-Q4": 98.0,
>         "2008-Q1": 100.5,
>         "2008-Q2": 101.0,
>     }
>
>
> def test_growth_uses_levels_from_that_same_day() -> None:
>     got = vintage_series(LEVELS, date(2008, 8, 1), QOQ)
>     assert set(got) == {"2008-Q1", "2008-Q2"}  # 2007-Q4 has no base in this vintage
>     assert got["2008-Q1"] == pytest.approx((100.5 / 98.0 - 1) * 100)
>     assert got["2008-Q2"] == pytest.approx((101.0 / 100.5 - 1) * 100)
>
>
> def test_nothing_published_after_the_day_leaks_in() -> None:
>     assert "2008-Q3" not in vintage_series(LEVELS, date(2008, 11, 1), IDENTITY)  # only "."
>     assert vintage_series(LEVELS, date(2008, 11, 26), IDENTITY)["2008-Q3"] == 99.0
>     assert vintage_series(LEVELS, date(2008, 1, 29), IDENTITY) == {}
>
>
> def test_missing_marker_and_zero_base_give_no_value() -> None:
>     rows = [
>         V("2020-01", 0.0, date(2020, 2, 13), None),
>         V("2020-02", 5.0, date(2020, 3, 11), None),
>         V("2020-03", None, date(2020, 4, 10), None),
>     ]
>     assert vintage_series(rows, date(2020, 5, 1), Transform("growth", 1)) == {}
>     assert vintage_series(rows, date(2020, 5, 1), IDENTITY) == {"2020-01": 0.0, "2020-02": 5.0}
>
>
> def test_on_none_is_the_current_vintage() -> None:
>     assert vintage_series(LEVELS, None, IDENTITY)["2008-Q2"] == 100.0
>
>
> def test_year_on_year_growth() -> None:
>     rows = [
>         V("2007-Q2", 90.0, date(2007, 7, 27), None),
>         V("2008-Q2", 99.0, date(2008, 7, 31), None),
>     ]
>     assert vintage_series(rows, date(2008, 8, 1), YOY_Q) == {"2008-Q2": pytest.approx(10.0)}
>
>
> def test_matches_derived_as_of_for_every_period() -> None:
>     from macropulse_economics.vintages import derived_as_of  # noqa: PLC0415
>
>     day = date(2008, 9, 1)
>     got = vintage_series(LEVELS, day, QOQ)
>     for period in {r.period for r in LEVELS}:
>         expected = derived_as_of(LEVELS, period, day, QOQ)
>         assert got.get(period) == (pytest.approx(expected) if expected is not None else None)
>
>
> def test_unknown_transform_kind_is_rejected() -> None:
>     with pytest.raises(ValueError, match="transform"):
>         vintage_series(LEVELS, date(2008, 9, 1), Transform("ratio", 1))
>
> ```
>
> ## `packages/economics/src/macropulse_economics/vintages.py`
>
> ```py
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
> base is zero, and periods whose first release cannot be derived are
> …(truncated)
