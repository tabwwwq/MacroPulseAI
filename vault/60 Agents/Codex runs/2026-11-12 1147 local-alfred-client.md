---
type: codex-run
name: local-alfred-client
date: 2026-11-12
time: "11:47"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-alfred-client

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-12 11:47. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```python
> """ALFRED (FRED real-time / vintage) client.
>
> ALFRED keeps every published version of a FRED series: each observation is returned once per
> real-time period in which that value was the published one, so a single series date can yield
> several rows (the initial release and every subsequent revision). The authenticated API
> (``FRED_API_KEY``) is required; the key is server-side only and is redacted from the stored
> provenance URL via :func:`macropulse_economics.redact.redact_secrets`.
> Docs: https://fred.stlouisfed.org/docs/api/fred/series_observations.html and
> https://alfred.stlouisfed.org/
> """
>
> from __future__ import annotations
>
> from dataclasses import dataclass
> from datetime import UTC, date, datetime
> from typing import Any
>
> from macropulse_economics.connectors.base import ConnectorError, SeriesRequest
> from macropulse_economics.connectors.http import Fetcher
> from macropulse_economics.periods import PeriodError, normalise_fred_date
> from macropulse_economics.redact import redact_secrets
>
> ALFRED_OBSERVATIONS = "https://api.stlouisfed.org/fred/series/observations"
> REALTIME_START = "1776-07-04"
> REALTIME_END = "9999-12-31"
> PAGE_SIZE = 100_000  # the API's maximum limit
>
>
> @dataclass(frozen=True, slots=True)
> class VintageObservation:
>     """One (observation date, real-time period) pair from ALFRED."""
>
>     period: str  # our label: "2008-Q3" / "2020-04" (via periods.normalise_fred_date)
>     value: float | None  # None for "." (not available in that vintage)
>     realtime_start: date  # first day this value was the published one
>     realtime_end: date | None  # last day; None when REALTIME_END (still current)
>
>
> @dataclass(slots=True)
> class VintageFetch:
>     """A complete ALFRED pull for one series, with provenance."""
>
>     request: SeriesRequest
>     observations: list[VintageObservation]
>     url: str  # first page URL with the key redacted (redact_secrets)
>     retrieved_at: datetime  # timezone-aware UTC
>
>
> def _parse_iso_date(raw: str, field: str, dataset: str) -> date:
>     try:
>         return date.fromisoformat(raw)
>     except ValueError as exc:
>         raise ConnectorError(
>             f"ALFRED {dataset}: {field} is not ISO YYYY-MM-DD: {raw!r}"
>         ) from exc
>
>
> def parse_vintage_page(
>     payload: dict[str, Any], request: SeriesRequest
> ) -> tuple[list[VintageObservation], int]:
>     """Validate one ALFRED JSON page and return (observations, count)."""
>     dataset = request.dataset
>     observations = payload.get("observations")
>     if not isinstance(observations, list):
>         raise ConnectorError(f"ALFRED {dataset}: 'observations' missing or not a list")
>     count = payload.get("count")
>     if not isinstance(count, int) or isinstance(count, bool):
>         raise ConnectorError(f"ALFRED {dataset}: 'count' missing or not an int")
>
>     rows: list[VintageObservation] = []
>     for row in observations:
>         if not isinstance(row, dict):
>             raise ConnectorError(f"ALFRED {dataset}: observation row is not an object")
>         for key in ("realtime_start", "realtime_end", "date", "value"):
>             if key not in row:
>                 raise ConnectorError(f"ALFRED {dataset}: row lacks {key!r}")
>         raw_start = row["realtime_start"]
>         raw_end = row["realtime_end"]
>         raw_date = row["date"]
>         raw_value = row["value"]
>
>         realtime_start = _parse_iso_date(raw_start, "realtime_start", dataset)
>         realtime_end = _parse_iso_date(raw_end, "realtime_end", dataset)
>         if realtime_end < realtime_start:
>             raise ConnectorError(
>                 f"ALFRED {dataset}: realtime_end {raw_end} before realtime_start {raw_start}"
>             )
>
>         try:
>             period = normalise_fred_date(raw_date, request.frequency)
>         except PeriodError as exc:
>             raise ConnectorError(f"ALFRED {dataset}: {exc}") from exc
>
>         if raw_value == ".":
>             value: float | None = None
>         else:
>             try:
>                 value = float(raw_value)
>             except (TypeError, ValueError) as exc:
>                 raise ConnectorError(
>                     f"ALFRED {dataset}: value is neither '.' nor a float: {raw_value!r}"
>                 ) from exc
>
>         rows.append(
>             VintageObservation(
>                 period=period,
>                 value=value,
>                 realtime_start=realtime_start,
>                 realtime_end=None if raw_end == REALTIME_END else realtime_end,
>             )
>         )
>     return rows, count
>
>
> def fetch_vintages(
>     fetcher: Fetcher,
>     request: SeriesRequest,
>     api_key:*** | None,
>     *,
>     page_size: int = PAGE_SIZE,
> ) -> VintageFetch:
>     """Fetch every ALFRED vintage for one FRED series, paginating until ``count`` rows."""
>     if request.source_id != "fred":
>         raise ConnectorError(
>             f"ALFRED serves FRED series only: got source_id={request.source_id!r}"
>         )
>     if api_key is None or not api_key.strip():
>         raise ConnectorError(
>             "ALFRED needs FRED_API_KEY (server-side) — not configured"
>         )
>     key = api_key.strip()
>
>     observations: list[VintageObservation] = []
>     count: int | None = None
>     offset = 0
>     first_url: str | None = None
>
>     while count is None or len(observations) < count:
>         response = fetcher.get(
>             ALFRED_OBSERVATIONS,
>             params={
>                 "series_id": request.dataset,
>                 "api_key": key,
>                 "file_type": "json",
>                 "realtime_start": REALTIME_START,
>                 "realtime_end": REALTIME_END,
>                 "limit": str(page_size),
>                 "offset": str(offset),
>             },
>         )
>         if first_url is None:
>             first_url = str(response.url)
>         try:
>             payload = response.json()
>         except ValueError as exc:
>             raise ConnectorError(
>                 f"ALFRED {request.dataset}: response is not valid JSON"
>             ) from exc
>         if not isinstance(payload, dict):
>             raise ConnectorError(
> …(truncated)

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the ALFRED (FRED real-time / vintage) client of the data package.
>
> ## Files
> - CREATE `packages/economics/src/macropulse_economics/connectors/alfred.py` — the only file you write.
> - CONTEXT (provided below, do not change):
>   `packages/economics/tests/test_alfred.py` — the specification; read every assertion.
>   `packages/economics/src/macropulse_economics/connectors/fred.py` — the existing key-free FRED connector:
>   follow its style, docstring conventions and imports.
>   `packages/economics/src/macropulse_economics/connectors/base.py`, `.../connectors/http.py`,
>   `packages/economics/src/macropulse_economics/redact.py`, `packages/economics/src/macropulse_economics/periods.py`.
>
> ## Background
> ALFRED keeps every published version of a FRED series. `GET https://api.stlouisfed.org/fred/series/observations`
> with `realtime_start=1776-07-04&realtime_end=9999-12-31&file_type=json` returns one row per (observation date,
> real-time period in which that value was the published one):
> `{"realtime_start": "2008-10-30", "realtime_end": "2008-11-25", "date": "2008-07-01", "value": "11712.4"}`.
> `"9999-12-31"` as realtime_end means "still the current value". `"."` is FRED's missing marker. The response
> has `count`, `offset`, `limit` and `observations`. Docs:
> https://fred.stlouisfed.org/docs/api/fred/series_observations.html and https://alfred.stlouisfed.org/
>
> ## API (module level)
> ```python
> ALFRED_OBSERVATIONS = "https://api.stlouisfed.org/fred/series/observations"
> REALTIME_START = "1776-07-04"
> REALTIME_END = "9999-12-31"
> PAGE_SIZE = 100_000  # the API's maximum limit
>
> @dataclass(frozen=True, slots=True)
> class VintageObservation:
>     period: str                 # our label: "2008-Q3" / "2020-04" (via periods.normalise_fred_date)
>     value: float | None         # None for "." (not available in that vintage)
>     realtime_start: date        # first day this value was the published one
>     realtime_end: date | None   # last day; None when REALTIME_END (still current)
>
> @dataclass(slots=True)
> class VintageFetch:
>     request: SeriesRequest
>     observations: list[VintageObservation]
>     url: str                    # first page URL with the key redacted (redact_secrets)
>     retrieved_at: datetime      # timezone-aware UTC
>
> def parse_vintage_page(payload: dict[str, Any], request: SeriesRequest) -> tuple[list[VintageObservation], int]: ...
> def fetch_vintages(fetcher: Fetcher, request: SeriesRequest, api_key:*** | None, *, page_size: int = PAGE_SIZE) -> VintageFetch: ...
> ```
>
> ## Rules
> 1. `parse_vintage_page` returns (rows, count). Raise `ConnectorError` whose message starts with
>    `f"ALFRED {request.dataset}: "` when: `observations` is missing or not a list; `count` missing or not an
>    int; a row lacks any of the four keys; the date is not a valid period start (`PeriodError`); the value is
>    neither "." nor a float; a date is not ISO `YYYY-MM-DD`; realtime_end < realtime_start.
> 2. `fetch_vintages`:
>    - `request.source_id != "fred"` → `ConnectorError("ALFRED serves FRED series only: ...")` (no request).
>    - `api_key` None/blank → `ConnectorError("ALFRED needs FRED_API_KEY (server-side) — not configured")`
>      before any request.
>    - Loop with `offset = 0, page_size, 2*page_size, …`; each request: `fetcher.get(ALFRED_OBSERVATIONS,
>      params={"series_id": request.dataset, "api_key": api_key.strip(), "file_type": "json",
>      "realtime_start": REALTIME_START, "realtime_end": REALTIME_END, "limit": str(page_size),
>      "offset": str(offset)})`. Stop when the collected rows reach `count`. A page with zero rows before
>      `count` is reached → `ConnectorError` (never loop forever).
>    - `url` = `redact_secrets(str(first_response.url))`. Never put the key into an exception message;
>      `Fetcher.get` errors already omit query strings, re-raise them unchanged.
>    - Response JSON that is not an object → `ConnectorError`.
> 3. Python 3.12, `from __future__ import annotations`, full type hints (mypy --strict), ruff (line length 100,
>    rules E F W I B UP N S SIM RUF PTH DTZ PL). Use `datetime.now(UTC)`. No new dependencies.
> 4. Module docstring: what ALFRED is, that the key is server-side only and redacted from stored URLs, and the
>    docs link.
>
> Output only the file, in ONE fenced code block (three backticks, language python) — do not nest fences.
>
> # Output file
>
> `packages/economics/src/macropulse_economics/connectors/alfred.py`
>
> # Context files
>
> ## `packages/economics/tests/test_alfred.py`
>
> ```py
> """ALFRED (FRED real-time) client: parsing, pagination, key handling. No network."""
>
> from __future__ import annotations
>
> from datetime import date
> from typing import Any
> from urllib.parse import parse_qs, urlsplit
>
> import httpx
> import pytest
>
> from macropulse_economics.connectors import ConnectorError, SeriesRequest
> from macropulse_economics.connectors.alfred import (
>     ALFRED_OBSERVATIONS,
>     REALTIME_END,
>     REALTIME_START,
>     VintageObservation,
>     fetch_vintages,
>     parse_vintage_page,
> )
> from macropulse_economics.connectors.http import Fetcher, make_client
>
> US_GDP = SeriesRequest("fred", "GDPC1", "GDPC1", "US", "quarterly", "Billions of chained dollars")
> US_UNRATE = SeriesRequest("fred", "UNRATE", "UNRATE", "US", "monthly", "%")
> KEY = "***"  # fake test value
>
>
> def page(rows: list[dict[str, str]], count: int | None = None, offset: int = 0) -> dict[str, Any]:
>     return {
>         "realtime_start": REALTIME_START,
>         "realtime_end": REALTIME_END,
>         "count": len(rows) if count is None else count,
>         "offset": offset,
>         "limit": 100000,
>         "observations": rows,
>     }
>
>
> GDP_ROWS = [
>     {
>         "realtime_start": "2008-10-30",
>         "realtime_end": "2008-11-25",
>         "date": "2008-07-01",
>         "value": "11712.4",
>     },
>     {
>         "realtime_start": "2008-11-26",
>         "realtime_end": "9999-12-31",
>         "date": "2008-07-01",
>         "value": "11706.1",
>     },
>     {
>         "realtime_start": "1996-01-19",
>         "realtime_end": "1997-05-06",
>         "date": "1947-0
> …(truncated)
