Task: write the ALFRED (FRED real-time / vintage) client of the data package.

## Files
- CREATE `packages/economics/src/macropulse_economics/connectors/alfred.py` — the only file you write.
- CONTEXT (provided below, do not change):
  `packages/economics/tests/test_alfred.py` — the specification; read every assertion.
  `packages/economics/src/macropulse_economics/connectors/fred.py` — the existing key-free FRED connector:
  follow its style, docstring conventions and imports.
  `packages/economics/src/macropulse_economics/connectors/base.py`, `.../connectors/http.py`,
  `packages/economics/src/macropulse_economics/redact.py`, `packages/economics/src/macropulse_economics/periods.py`.

## Background
ALFRED keeps every published version of a FRED series. `GET https://api.stlouisfed.org/fred/series/observations`
with `realtime_start=1776-07-04&realtime_end=9999-12-31&file_type=json` returns one row per (observation date,
real-time period in which that value was the published one):
`{"realtime_start": "2008-10-30", "realtime_end": "2008-11-25", "date": "2008-07-01", "value": "11712.4"}`.
`"9999-12-31"` as realtime_end means "still the current value". `"."` is FRED's missing marker. The response
has `count`, `offset`, `limit` and `observations`. Docs:
https://fred.stlouisfed.org/docs/api/fred/series_observations.html and https://alfred.stlouisfed.org/

## API (module level)
```python
ALFRED_OBSERVATIONS = "https://api.stlouisfed.org/fred/series/observations"
REALTIME_START = "1776-07-04"
REALTIME_END = "9999-12-31"
PAGE_SIZE = 100_000  # the API's maximum limit


@dataclass(frozen=True, slots=True)
class VintageObservation:
    period: str  # our label: "2008-Q3" / "2020-04" (via periods.normalise_fred_date)
    value: float | None  # None for "." (not available in that vintage)
    realtime_start: date  # first day this value was the published one
    realtime_end: date | None  # last day; None when REALTIME_END (still current)


@dataclass(slots=True)
class VintageFetch:
    request: SeriesRequest
    observations: list[VintageObservation]
    url: str  # first page URL with the key redacted (redact_secrets)
    retrieved_at: datetime  # timezone-aware UTC


def parse_vintage_page(
    payload: dict[str, Any], request: SeriesRequest
) -> tuple[list[VintageObservation], int]: ...
def fetch_vintages(
    fetcher: Fetcher, request: SeriesRequest, api_key: str | None, *, page_size: int = PAGE_SIZE
) -> VintageFetch: ...
```

## Rules
1. `parse_vintage_page` returns (rows, count). Raise `ConnectorError` whose message starts with
   `f"ALFRED {request.dataset}: "` when: `observations` is missing or not a list; `count` missing or not an
   int; a row lacks any of the four keys; the date is not a valid period start (`PeriodError`); the value is
   neither "." nor a float; a date is not ISO `YYYY-MM-DD`; realtime_end < realtime_start.
2. `fetch_vintages`:
   - `request.source_id != "fred"` → `ConnectorError("ALFRED serves FRED series only: ...")` (no request).
   - `api_key` None/blank → `ConnectorError("ALFRED needs FRED_API_KEY (server-side) — not configured")`
     before any request.
   - Loop with `offset = 0, page_size, 2*page_size, …`; each request: `fetcher.get(ALFRED_OBSERVATIONS,
     params={"series_id": request.dataset, "api_key": api_key.strip(), "file_type": "json",
     "realtime_start": REALTIME_START, "realtime_end": REALTIME_END, "limit": str(page_size),
     "offset": str(offset)})`. Stop when the collected rows reach `count`. A page with zero rows before
     `count` is reached → `ConnectorError` (never loop forever).
   - `url` = `redact_secrets(str(first_response.url))`. Never put the key into an exception message;
     `Fetcher.get` errors already omit query strings, re-raise them unchanged.
   - Response JSON that is not an object → `ConnectorError`.
3. Python 3.12, `from __future__ import annotations`, full type hints (mypy --strict), ruff (line length 100,
   rules E F W I B UP N S SIM RUF PTH DTZ PL). Use `datetime.now(UTC)`. No new dependencies.
4. Module docstring: what ALFRED is, that the key is server-side only and redacted from stored URLs, and the
   docs link.

Output only the file, in ONE fenced code block (three backticks, language python) — do not nest fences.
