"""OECD Data Explorer SDMX REST connector (Composite leading indicators dataflow, CSV output).

Docs: https://data-explorer.oecd.org/
Anonymous access is rate-limited, so the shared Fetcher's per-host throttle and 429 handling apply.
The composite leading indicator exists only for some countries (BE and NL publish confidence
indices only, finding F-002).
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

BASE = "https://sdmx.oecd.org/public/rest/data"
AGENCY = "OECD.SDD.STES"
VERSIONS: dict[str, str] = {"DSD_STES@DF_CLI": "4.1"}  # dataflow -> version, verified 2026-11-12
KEY_DIMENSIONS: tuple[str, ...] = (
    "REF_AREA",
    "FREQ",
    "MEASURE",
    "UNIT_MEASURE",
    "ACTIVITY",
    "ADJUSTMENT",
    "TRANSFORMATION",
    "TIME_HORIZ",
    "METHODOLOGY",
)


def parse_csv(text: str, request: SeriesRequest) -> tuple[list[FetchedObservation], str | None]:
    reader = csv.DictReader(io.StringIO(text.lstrip("﻿")))
    rows = list(reader)
    if not rows:
        raise ConnectorError(f"OECD {request.dataset}.{request.series_key}: empty response")

    header = reader.fieldnames or []
    missing = [name for name in ("TIME_PERIOD", "OBS_VALUE", *KEY_DIMENSIONS) if name not in header]
    if missing:
        raise ConnectorError(
            f"OECD {request.dataset}.{request.series_key}: missing column {missing}"
        )

    parts = request.series_key.split(".")
    if len(parts) != len(KEY_DIMENSIONS):
        raise ConnectorError(
            f"OECD {request.dataset}.{request.series_key}: series key must have "
            f"{len(KEY_DIMENSIONS)} dimensions, got {len(parts)}"
        )

    observations: list[FetchedObservation] = []
    seen_periods: set[str] = set()
    unit: str | None = None
    for row in rows:
        key = ".".join((row.get(name) or "").strip() for name in KEY_DIMENSIONS)
        if key != request.series_key:
            raise ConnectorError(
                f"OECD {request.dataset}.{request.series_key}: unexpected series {key}"
            )

        mult = (row.get("UNIT_MULT") or "").strip()
        if mult not in ("", "0"):
            raise ConnectorError(
                f"OECD {request.dataset}.{request.series_key}: unit multiplier {mult!r}"
            )

        raw = (row.get("OBS_VALUE") or "").strip()
        if not raw:
            continue
        period = (row.get("TIME_PERIOD") or "").strip()
        try:
            period_start(period)
            value = float(raw)
        except (PeriodError, ValueError) as exc:
            raise ConnectorError(
                f"OECD {request.dataset}.{request.series_key}: bad observation {period!r}={raw!r}"
            ) from exc
        if period in seen_periods:
            raise ConnectorError(
                f"OECD {request.dataset}.{request.series_key}: duplicate period {period}"
            )
        seen_periods.add(period)
        if unit is None:
            unit = (row.get("UNIT_MEASURE") or "").strip() or None
        observations.append(
            FetchedObservation(period, value, (row.get("OBS_STATUS") or "").strip() or None)
        )

    observations.sort(key=lambda o: period_start(o.period))
    return observations, unit


def fetch(fetcher: Fetcher, request: SeriesRequest) -> FetchResult:
    version = VERSIONS.get(request.dataset)
    if version is None:
        raise ConnectorError(f"OECD {request.dataset}: unknown OECD dataflow")
    url = f"{BASE}/{AGENCY},{request.dataset},{version}/{request.series_key}"
    response = fetcher.get(url, params={"format": "csvfile"})
    observations, unit = parse_csv(response.text, request)
    return FetchResult(
        request=request,
        observations=observations,
        url=str(response.url),
        retrieved_at=datetime.now(UTC),
        unit_label=unit,
    )
