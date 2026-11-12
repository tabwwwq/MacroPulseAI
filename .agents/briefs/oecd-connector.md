Task: write the OECD SDMX connector (Composite leading indicators dataflow, CSV output).

## Files
- CREATE `packages/economics/src/macropulse_economics/connectors/oecd.py` — the only file you write.
- CONTEXT (provided below, do not change): `packages/economics/tests/test_oecd.py` (the specification —
  read every assertion), the two fixtures it reads (genuine OECD responses),
  `packages/economics/src/macropulse_economics/connectors/ecb.py` (the closest existing connector: copy its
  structure and style), `connectors/base.py` (types), `connectors/http.py` (`Fetcher.get`).

## Public API (module-level)
    BASE = "https://sdmx.oecd.org/public/rest/data"
    AGENCY = "OECD.SDD.STES"
    VERSIONS: dict[str, str] = {"DSD_STES@DF_CLI": "4.1"}   # dataflow -> version, verified 2026-11-12
    KEY_DIMENSIONS: tuple[str, ...] = ("REF_AREA", "FREQ", "MEASURE", "UNIT_MEASURE", "ACTIVITY",
                                       "ADJUSTMENT", "TRANSFORMATION", "TIME_HORIZ", "METHODOLOGY")
    def parse_csv(text: str, request: SeriesRequest) -> tuple[list[FetchedObservation], str | None]: ...
    def fetch(fetcher: Fetcher, request: SeriesRequest) -> FetchResult: ...

## parse_csv rules (every error is a `ConnectorError` whose message starts with "OECD " and names the key)
1. Strip a leading BOM ("﻿"), read with `csv.DictReader`. No rows → message contains "empty response".
2. The header must contain TIME_PERIOD, OBS_VALUE and every name in KEY_DIMENSIONS; otherwise the message
   contains "missing column" and the missing names.
3. `request.series_key.split(".")` must have exactly `len(KEY_DIMENSIONS)` parts, else the message contains
   "dimensions" (check this before reading rows' values).
4. For every row, the KEY_DIMENSIONS values joined with "." must equal `request.series_key`; otherwise the
   message contains "unexpected series" and the offending key.
5. `UNIT_MULT` must be empty or "0" (values are published in units); anything else → "unit multiplier".
6. Empty OBS_VALUE → skip the row (never fill). Otherwise `float(value)` and `period_start(period)` must
   succeed, else "bad observation" with the period and raw value (catch `PeriodError` and `ValueError`).
7. A period that appears twice → "duplicate period".
8. `obs_status` = stripped OBS_STATUS or None. Sort by `period_start(period)`.
9. Return `(observations, unit)` where unit = the first row's stripped UNIT_MEASURE or None.

## fetch
`version = VERSIONS.get(request.dataset)`; None → `ConnectorError` containing "unknown OECD dataflow"
(raise before any request). URL `f"{BASE}/{AGENCY},{request.dataset},{version}/{request.series_key}"`,
`fetcher.get(url, params={"format": "csvfile"})`, then `FetchResult(request=request, observations=...,
url=str(response.url), retrieved_at=datetime.now(UTC), unit_label=unit)`.

Module docstring: OECD Data Explorer SDMX REST, docs https://data-explorer.oecd.org/ ; anonymous access is
rate-limited, so the shared Fetcher's per-host throttle and 429 handling apply; the composite leading
indicator exists only for some countries (BE and NL publish confidence indices only, finding F-002).

## Rules
mypy --strict, ruff (line length 100), `from __future__ import annotations`, no new dependencies.
Output only the file, in ONE fenced code block (three backticks, language python) — do not nest fences.
