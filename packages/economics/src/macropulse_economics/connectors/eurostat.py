"""Eurostat dissemination API (JSON-stat 2.0).

Docs: https://ec.europa.eu/eurostat/web/user-guides/data-browser/api-data-access/api-introduction
Eurostat serves the latest revision only; history is a revised-data view (no vintages here).
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from macropulse_economics.connectors.base import (
    ConnectorError,
    FetchedObservation,
    FetchResult,
    SeriesRequest,
)
from macropulse_economics.connectors.http import Fetcher
from macropulse_economics.periods import PeriodError, period_start

BASE = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"


def parse_filters(series_key: str) -> dict[str, str]:
    """ "freq=Q, unit=CLV20_MNAC" -> {"freq": "Q", "unit": "CLV20_MNAC"}."""
    out: dict[str, str] = {}
    for part in series_key.split(","):
        key, sep, value = part.strip().partition("=")
        if not sep or not key or not value:
            raise ConnectorError(f"Malformed Eurostat filter: {part!r}")
        out[key.strip()] = value.strip()
    return out


def parse_jsonstat(
    payload: dict[str, Any], request: SeriesRequest
) -> tuple[list[FetchedObservation], str | None, str | None]:
    """Return (observations, unit label, updated) for a single-series JSON-stat response."""
    if "error" in payload:
        raise ConnectorError(f"Eurostat error for {request.dataset}: {payload['error']}")
    try:
        ids: list[str] = payload["id"]
        sizes: list[int] = payload["size"]
        dims: dict[str, Any] = payload["dimension"]
    except (KeyError, TypeError) as exc:
        raise ConnectorError(f"Eurostat response for {request.dataset} is not JSON-stat") from exc
    if not ids or ids[-1] != "time":
        raise ConnectorError(f"{request.dataset}: time is not the last dimension")
    ambiguous = [d for d, n in zip(ids[:-1], sizes[:-1], strict=True) if n != 1]
    if ambiguous:
        raise ConnectorError(
            f"{request.dataset}: filter selects several series (dimensions {ambiguous})"
        )

    index = dims["time"]["category"]["index"]
    if isinstance(index, list):
        index = {label: pos for pos, label in enumerate(index)}
    raw_values = payload.get("value", {})
    raw_status = payload.get("status", {})
    if isinstance(raw_values, list):
        raw_values = {str(i): v for i, v in enumerate(raw_values)}
    if isinstance(raw_status, list):
        raw_status = {str(i): s for i, s in enumerate(raw_status)}

    observations = []
    for period, pos in sorted(index.items(), key=lambda kv: kv[1]):
        value = raw_values.get(str(pos))
        if value is None:
            continue  # missing official value stays missing
        try:
            period_start(period)
        except PeriodError as exc:
            raise ConnectorError(f"{request.dataset}: unexpected period {period!r}") from exc
        if not isinstance(value, (int, float)):
            raise ConnectorError(f"{request.dataset}: non-numeric value at {period}")
        observations.append(
            FetchedObservation(period, float(value), raw_status.get(str(pos)) or None)
        )

    unit_label = None
    if "unit" in dims:
        labels = dims["unit"]["category"].get("label", {})
        unit_label = next(iter(labels.values()), None)
    return observations, unit_label, payload.get("updated")


def fetch(fetcher: Fetcher, request: SeriesRequest) -> FetchResult:
    params = {**parse_filters(request.series_key), "geo": request.geo, "lang": "EN"}
    url = f"{BASE}/{request.dataset}"
    response = fetcher.get(url, params=params)
    try:
        payload = response.json()
    except ValueError as exc:
        raise ConnectorError(f"{request.dataset}: response is not JSON") from exc
    observations, unit_label, updated = parse_jsonstat(payload, request)
    return FetchResult(
        request=request,
        observations=observations,
        url=str(response.url),
        retrieved_at=datetime.now(UTC),
        source_updated_at=updated,
        unit_label=unit_label,
    )
