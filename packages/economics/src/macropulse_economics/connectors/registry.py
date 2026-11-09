"""Connector dispatch."""

from __future__ import annotations

from collections.abc import Callable

from macropulse_economics.connectors import ecb, eurostat, fred
from macropulse_economics.connectors.base import ConnectorError, FetchResult, SeriesRequest
from macropulse_economics.connectors.http import Fetcher

ConnectorFn = Callable[[Fetcher, SeriesRequest], FetchResult]

CONNECTORS: dict[str, ConnectorFn] = {
    "eurostat": eurostat.fetch,
    "ecb": ecb.fetch,
    "fred": fred.fetch,
}


def fetch_series(fetcher: Fetcher, request: SeriesRequest) -> FetchResult:
    connector = CONNECTORS.get(request.source_id)
    if connector is None:
        raise ConnectorError(f"No connector for source {request.source_id!r} yet")
    return connector(fetcher, request)
