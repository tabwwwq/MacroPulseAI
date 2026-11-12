Task: add one function to the vintage analytics module: a whole series as published on one day.

## Files
- EDIT `packages/economics/src/macropulse_economics/vintages.py` — the only file you write. Return the
  COMPLETE file: everything that is there now, unchanged, plus the new function.
- CONTEXT (provided below, do not change): `packages/economics/tests/test_vintage_series.py` (the specification),
  the current `vintages.py`, and `packages/economics/src/macropulse_economics/transforms.py`.

## API (add after `derived_as_of`)
    def vintage_series(
        rows: Sequence[VintageObservation], on: date | None, transform: Transform
    ) -> dict[str, float]:

## Rules
1. Result: period -> derived value for every period that has a non-None value in the vintage valid on `on`
   (same window rule as `value_as_of`; `on=None` = current vintage) AND whose derivation is defined.
2. identity: the value itself. growth with lag k: `(v / base - 1) * 100` with `base` = the value of
   `shift(period, -k)` in the SAME vintage; skip the period when the base is missing or 0.
   Any other `transform.kind` raises `ValueError` whose message contains "transform".
3. Must give exactly what `derived_as_of(rows, period, on, transform)` gives for every period, but in one pass:
   build `_index(rows)` once, pick each period's value once with `_pick`, then derive from that dict. Never
   call `derived_as_of` inside the loop. Insertion order: by `period_start` of the period.
4. Docstring: this is the series a user could have downloaded on day `on` — nothing published later.
5. Keep mypy --strict and ruff (line length 100) clean. Do not change any existing function.

Output only the file, in ONE fenced code block (three backticks, language python) — do not nest fences.
