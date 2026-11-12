Task: write the pure revision-analytics module for ALFRED vintages.

## Files
- CREATE `packages/economics/src/macropulse_economics/vintages.py` — the only file you write.
- CONTEXT (provided below, do not change): `packages/economics/tests/test_vintages.py` (the specification —
  read every assertion), `packages/economics/src/macropulse_economics/transforms.py` (`Transform`: kind
  "identity" or "growth" with a `lag`), `packages/economics/src/macropulse_economics/periods.py` (`shift`),
  and the dataclass `VintageObservation(period, value, realtime_start, realtime_end)` from
  `macropulse_economics.connectors.alfred` (value None = not available in that vintage; realtime_end None =
  still current).

## API
```python
def value_as_of(rows: Sequence[VintageObservation], period: str, on: date | None) -> float | None
def first_release_dates(rows: Sequence[VintageObservation]) -> dict[str, date]
def derived_as_of(rows: Sequence[VintageObservation], period: str, on: date | None, transform: Transform) -> float | None
def revision_history(rows: Sequence[VintageObservation], transform: Transform) -> list[RevisionPoint]
def revision_summary(points: Sequence[RevisionPoint]) -> RevisionSummary

@dataclass(frozen=True, slots=True)
class RevisionPoint:
    period: str
    first_published: date
    first_value: float
    latest_value: float | None
    revision: float | None          # latest_value - first_value, None when latest_value is None

@dataclass(frozen=True, slots=True)
class RevisionSummary:
    count: int                      # points with a revision (latest_value not None)
    mean_abs_revision: float | None
    max_abs_revision: float | None
    max_abs_period: str | None
    sign_changes: list[str]         # periods where (first_value < 0) != (latest_value < 0); zero is not negative
```

## Rules
1. `value_as_of(rows, period, on)`: the value of the row for `period` whose real-time window contains `on`
   (`realtime_start <= on` and (`realtime_end is None` or `on <= realtime_end`), both ends inclusive).
   `on=None` means the current vintage: the row with `realtime_end is None`. Returns the row's value (which
   may be None for a "." marker) or None when no row matches.
2. `first_release_dates`: for each period, the earliest `realtime_start` among its rows with a non-None value.
   Periods that never had a value are absent.
3. `derived_as_of`: identity → `value_as_of(period, on)`. growth with lag k → `(v / base - 1) * 100` where
   `v = value_as_of(period, on)` and `base = value_as_of(shift(period, -k), on)` — BOTH from the same date `on`.
   None if either is None or `base == 0`. Any other transform kind → `ValueError`.
4. `revision_history`: for each period in `first_release_dates`, sorted by period start (use
   `periods.period_start`): `first = derived_as_of(rows, period, first_date, transform)`; skip the period when
   `first` is None (never estimate). `latest = derived_as_of(rows, period, None, transform)`.
5. `revision_summary`: statistics only over points whose `revision` is not None; `max_abs_period` is the
   period of the largest absolute revision (first one on ties); sign changes in period order. Empty → count 0,
   None statistics, empty list.
6. Build an index once per call (dict period → rows) instead of scanning all rows for every lookup inside
   `revision_history` — the real series have ~5,000 rows. Keep the public functions' behaviour identical.
7. Python 3.12, `from __future__ import annotations`, full type hints (mypy --strict), ruff (line length 100).
   Standard library only. Module docstring: what a vintage is, that growth uses both levels from the same
   vintage (base-year changes between vintages make cross-vintage level comparisons meaningless), and that
   nothing is estimated.

Output only the file, in ONE fenced code block (three backticks, language python) — do not nest fences.
