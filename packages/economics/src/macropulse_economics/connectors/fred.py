"""FRED via the key-free graph CSV endpoint.

Values and dates are official FRED data; series metadata (units, seasonal adjustment) and ALFRED
vintages need the authenticated API (`FRED_API_KEY`) and are not fetched here — the catalog marks
these mappings `partial` for that reason.
Docs: https://fred.stlouisfed.org/docs/api/fred/series_observations.html
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
from macropulse_economics.periods import PeriodError, normalise_fred_date

GRAPH_CSV = "https://fred.stlouisfed.org/graph/fredgraph.csv"


def parse_csv(text: str, request: SeriesRequest) -> tuple[list[FetchedObservation], int]:
    """Return (observations, number of missing '.' values skipped)."""
    reader = csv.reader(io.StringIO(text.lstrip("﻿")))
    header = next(reader, None)
    if not header or len(header) != 2 or header[1].strip() != request.dataset:
        raise ConnectorError(f"FRED {request.dataset}: unexpected CSV header {header!r}")
    observations, missing = [], 0
    for row in reader:
        if not row:
            continue
        raw_date, raw_value = row[0].strip(), row[1].strip()
        if raw_value in ("", "."):
            missing += 1  # FRED's missing-value marker: stays missing
            continue
        try:
            period = normalise_fred_date(raw_date, request.frequency)
            value = float(raw_value)
        except (PeriodError, ValueError) as exc:
            raise ConnectorError(f"FRED {request.dataset}: bad row {row!r}") from exc
        observations.append(FetchedObservation(period, value))
    return observations, missing


def fetch(fetcher: Fetcher, request: SeriesRequest) -> FetchResult:
    response = fetcher.get(GRAPH_CSV, params={"id": request.dataset})
    observations, missing = parse_csv(response.text, request)
    warnings = [f"{missing} missing value(s) marked '.' by FRED were skipped"] if missing else []
    return FetchResult(
        request=request,
        observations=observations,
        url=str(response.url),
        retrieved_at=datetime.now(UTC),
        warnings=warnings,
    )
