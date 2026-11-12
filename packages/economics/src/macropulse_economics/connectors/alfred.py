"""ALFRED (FRED real-time / vintage) client.

ALFRED keeps every published version of a FRED series: each observation is returned once per
real-time period in which that value was the published one, so a single series date can yield
several rows (the initial release and every subsequent revision). The authenticated API
(``FRED_API_KEY``) is required; the key is server-side only and is redacted from the stored
provenance URL via :func:`macropulse_economics.redact.redact_secrets`.
Docs: https://fred.stlouisfed.org/docs/api/fred/series_observations.html and
https://alfred.stlouisfed.org/
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from typing import Any

from macropulse_economics.connectors.base import ConnectorError, SeriesRequest
from macropulse_economics.connectors.http import Fetcher
from macropulse_economics.periods import PeriodError, normalise_fred_date
from macropulse_economics.redact import redact_secrets

ALFRED_OBSERVATIONS = "https://api.stlouisfed.org/fred/series/observations"
REALTIME_START = "1776-07-04"
REALTIME_END = "9999-12-31"
PAGE_SIZE = 100_000  # the API's maximum limit


@dataclass(frozen=True, slots=True)
class VintageObservation:
    """One (observation date, real-time period) pair from ALFRED."""

    period: str  # our label: "2008-Q3" / "2020-04" (via periods.normalise_fred_date)
    value: float | None  # None for "." (not available in that vintage)
    realtime_start: date  # first day this value was the published one
    realtime_end: date | None  # last day; None when REALTIME_END (still current)


@dataclass(slots=True)
class VintageFetch:
    """A complete ALFRED pull for one series, with provenance."""

    request: SeriesRequest
    observations: list[VintageObservation]
    url: str  # first page URL with the key redacted (redact_secrets)
    retrieved_at: datetime  # timezone-aware UTC


def _parse_iso_date(raw: object, field: str, dataset: str) -> date:
    if not isinstance(raw, str):
        raise ConnectorError(f"ALFRED {dataset}: {field} is not a string: {raw!r}")
    try:
        return date.fromisoformat(raw)
    except ValueError as exc:
        raise ConnectorError(f"ALFRED {dataset}: {field} is not ISO YYYY-MM-DD: {raw!r}") from exc


def parse_vintage_page(
    payload: dict[str, Any], request: SeriesRequest
) -> tuple[list[VintageObservation], int]:
    """Validate one ALFRED JSON page and return (observations, count)."""
    dataset = request.dataset
    observations = payload.get("observations")
    if not isinstance(observations, list):
        raise ConnectorError(f"ALFRED {dataset}: 'observations' missing or not a list")
    count = payload.get("count")
    if not isinstance(count, int) or isinstance(count, bool):
        raise ConnectorError(f"ALFRED {dataset}: 'count' missing or not an int")

    rows: list[VintageObservation] = []
    for row in observations:
        if not isinstance(row, dict):
            raise ConnectorError(f"ALFRED {dataset}: observation row is not an object")
        for key in ("realtime_start", "realtime_end", "date", "value"):
            if key not in row:
                raise ConnectorError(f"ALFRED {dataset}: row lacks {key!r}")
        raw_start = row["realtime_start"]
        raw_end = row["realtime_end"]
        raw_date = row["date"]
        raw_value = row["value"]

        realtime_start = _parse_iso_date(raw_start, "realtime_start", dataset)
        realtime_end = _parse_iso_date(raw_end, "realtime_end", dataset)
        if realtime_end < realtime_start:
            raise ConnectorError(
                f"ALFRED {dataset}: realtime_end {raw_end} before realtime_start {raw_start}"
            )

        if not isinstance(raw_date, str):
            raise ConnectorError(f"ALFRED {dataset}: date is not a string: {raw_date!r}")
        try:
            period = normalise_fred_date(raw_date, request.frequency)
        except (PeriodError, ValueError) as exc:
            raise ConnectorError(f"ALFRED {dataset}: {exc}") from exc

        if raw_value == ".":
            value: float | None = None
        else:
            try:
                value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise ConnectorError(
                    f"ALFRED {dataset}: value is neither '.' nor a float: {raw_value!r}"
                ) from exc

        rows.append(
            VintageObservation(
                period=period,
                value=value,
                realtime_start=realtime_start,
                realtime_end=None if raw_end == REALTIME_END else realtime_end,
            )
        )
    return rows, count


def fetch_vintages(
    fetcher: Fetcher,
    request: SeriesRequest,
    api_key: str | None,
    *,
    page_size: int = PAGE_SIZE,
) -> VintageFetch:
    """Fetch every ALFRED vintage for one FRED series, paginating until ``count`` rows."""
    if request.source_id != "fred":
        raise ConnectorError(f"ALFRED serves FRED series only: got source_id={request.source_id!r}")
    if api_key is None or not api_key.strip():
        raise ConnectorError("ALFRED needs FRED_API_KEY (server-side) — not configured")
    key = api_key.strip()

    observations: list[VintageObservation] = []
    count: int | None = None
    offset = 0
    first_url: str | None = None

    while count is None or len(observations) < count:
        response = fetcher.get(
            ALFRED_OBSERVATIONS,
            params={
                "series_id": request.dataset,
                "api_key": key,
                "file_type": "json",
                "realtime_start": REALTIME_START,
                "realtime_end": REALTIME_END,
                "limit": str(page_size),
                "offset": str(offset),
            },
        )
        if first_url is None:
            first_url = str(response.url)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ConnectorError(f"ALFRED {request.dataset}: response is not valid JSON") from exc
        if not isinstance(payload, dict):
            raise ConnectorError(f"ALFRED {request.dataset}: response JSON is not an object")
        rows, count = parse_vintage_page(payload, request)
        if not rows and len(observations) < count:
            raise ConnectorError(
                f"ALFRED {request.dataset}: empty page before reaching count={count}"
            )
        observations.extend(rows)
        offset += len(rows)

    return VintageFetch(
        request=request,
        observations=observations,
        url=redact_secrets(first_url) or "",
        retrieved_at=datetime.now(UTC),
    )
