"""Shared connector types."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


class ConnectorError(RuntimeError):
    """A source could not be fetched or its response failed validation. Message is safe to log."""


@dataclass(frozen=True, slots=True)
class SeriesRequest:
    """One native official series, exactly as it is requested from the source."""

    source_id: str
    dataset: str
    series_key: (
        str  # human-readable filter/key, e.g. "freq=Q, unit=CLV20_MNAC, s_adj=SCA, na_item=B1GQ"
    )
    geo: str  # ISO2 country, or "EA" for euro-area aggregates
    frequency: str  # quarterly | monthly | daily | event
    unit: str
    adjustment: str | None = None
    indicator_ids: tuple[str, ...] = ()

    @property
    def series_id(self) -> str:
        return f"{self.source_id}:{self.dataset}:{self.series_key}:{self.geo}"


@dataclass(frozen=True, slots=True)
class FetchedObservation:
    period: str
    value: float
    obs_status: str | None = None


@dataclass(slots=True)
class FetchResult:
    request: SeriesRequest
    observations: list[FetchedObservation]
    url: str
    retrieved_at: datetime
    source_updated_at: str | None = None
    unit_label: str | None = None  # label echoed by the source, for provenance checks
    warnings: list[str] = field(default_factory=list)
