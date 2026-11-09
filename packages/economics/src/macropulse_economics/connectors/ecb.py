"""ECB Data Portal (SDMX 2.1 REST, CSV output).

Docs: https://data.ecb.europa.eu/help/api/overview
Policy rates are event-dated (one observation per decision date) and shared by all euro-area
members.
"""

from __future__ import annotations

import csv
import io
from datetime import UTC, datetime

from macropulse_economics.connectors.base import (
    ConnectorError,
    FetchedObservation,
    FetchResult,
    SeriesRequest,
)
from macropulse_economics.connectors.http import Fetcher
from macropulse_economics.periods import PeriodError, period_start

BASE = "https://data-api.ecb.europa.eu/service/data"


def parse_csv(text: str, request: SeriesRequest) -> tuple[list[FetchedObservation], str | None]:
    rows = list(csv.DictReader(io.StringIO(text.lstrip("﻿"))))
    if not rows:
        raise ConnectorError(f"ECB {request.dataset}.{request.series_key}: empty response")
    if "TIME_PERIOD" not in rows[0] or "OBS_VALUE" not in rows[0]:
        raise ConnectorError("ECB response is missing TIME_PERIOD/OBS_VALUE columns")
    keys: set[str] = {k for r in rows if (k := (r.get("KEY") or "").strip())}
    expected = f"{request.dataset}.{request.series_key}"
    if keys and keys != {expected}:
        raise ConnectorError(f"ECB returned unexpected series {sorted(keys)} for {expected}")
    observations = []
    for r in rows:
        raw = (r.get("OBS_VALUE") or "").strip()
        if not raw:
            continue
        period = r["TIME_PERIOD"].strip()
        try:
            period_start(period)
            value = float(raw)
        except (PeriodError, ValueError) as exc:
            raise ConnectorError(f"ECB {expected}: bad observation {period!r}={raw!r}") from exc
        observations.append(
            FetchedObservation(period, value, (r.get("OBS_STATUS") or "").strip() or None)
        )
    observations.sort(key=lambda o: period_start(o.period))
    unit = (rows[-1].get("UNIT") or "").strip() or None
    return observations, unit


def fetch(fetcher: Fetcher, request: SeriesRequest) -> FetchResult:
    url = f"{BASE}/{request.dataset}/{request.series_key}"
    response = fetcher.get(url, params={"format": "csvdata", "detail": "full"})
    observations, unit = parse_csv(response.text, request)
    return FetchResult(
        request=request,
        observations=observations,
        url=str(response.url),
        retrieved_at=datetime.now(UTC),
        unit_label=unit,
    )
