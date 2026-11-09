"""Official-data connectors: Eurostat (JSON-stat), ECB (SDMX CSV) and FRED (graph CSV)."""

from macropulse_economics.connectors.base import (
    ConnectorError,
    FetchedObservation,
    FetchResult,
    SeriesRequest,
)
from macropulse_economics.connectors.registry import CONNECTORS, fetch_series

__all__ = [
    "CONNECTORS",
    "ConnectorError",
    "FetchResult",
    "FetchedObservation",
    "SeriesRequest",
    "fetch_series",
]
