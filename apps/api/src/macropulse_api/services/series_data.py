"""Load one stored official series for a country/indicator and derive the values that are shown.

Shared by `/api/indicators`, the country summary (KPI tiles) and the data-quality report so that
every number on screen goes through the same mapping → native rows → transparent transform path.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from macropulse_api.db import as_utc
from macropulse_api.errors import ApiError
from macropulse_api.models import DataSource, Observation, QualityCheck
from macropulse_api.schemas import IndicatorDefinition, QualityCheckResult, SeriesProvenance
from macropulse_api.services.coverage import SYNC_HINT
from macropulse_economics.connectors import CONNECTORS
from macropulse_economics.indicators import (
    INDICATORS,
    IndicatorDef,
    SourceMapping,
    get_indicator,
    mappings_for,
)
from macropulse_economics.series import SYNCABLE, series_id_for
from macropulse_economics.transforms import Transform, transform_for
from macropulse_economics.transforms import apply as apply_transform

Point = tuple[str, float]


@dataclass(frozen=True)
class IndicatorData:
    iso: str
    indicator: IndicatorDef
    mapping: SourceMapping
    series_id: str
    transform: Transform
    rows: Sequence[Observation]  # native observations, oldest first
    points: list[Point]  # derived values shown to the user, oldest first

    @property
    def latest_row(self) -> Observation:
        """Row carrying the most recent fetch provenance."""
        return max(self.rows, key=lambda r: (as_utc(r.retrieved_at), r.period_start))

    @property
    def unit(self) -> str:
        return self.indicator.unit if self.transform.kind == "growth" else self.latest_row.unit


def resolve_indicator(indicator_id: str) -> IndicatorDef:
    ind = get_indicator(indicator_id)
    if ind is None:
        raise ApiError(
            422,
            "unsupported_indicator",
            f"Indicator '{indicator_id}' is not supported.",
            {"supported": [i.id for i in INDICATORS]},
        )
    return ind


def syncable_mapping(iso: str, ind: IndicatorDef) -> SourceMapping:
    """The mapping we can ingest for this country, or a 404 that says why there is none."""
    m = mappings_for(iso).get(ind.id)
    if m is None or m.status not in SYNCABLE:
        reason = (m.note if m else "") or "No official source is mapped for this country."
        raise ApiError(404, "indicator_unavailable", reason)
    if m.source_id not in CONNECTORS:
        raise ApiError(404, "indicator_unavailable", f"No {m.source_id} connector yet.")
    return m


def load_indicator(session: Session, iso: str, ind: IndicatorDef) -> IndicatorData:
    m = syncable_mapping(iso, ind)
    sid = series_id_for(m)
    rows = session.scalars(
        select(Observation).where(Observation.series_id == sid).order_by(Observation.period_start)
    ).all()
    if not rows:
        raise ApiError(503, "data_not_synced", f"No observations stored for {sid}. {SYNC_HINT}")
    transform = transform_for(ind.id, m.source_id)
    points = apply_transform(transform, [(r.period, r.value) for r in rows])
    return IndicatorData(iso, ind, m, sid, transform, rows, points)


def indicator_definition(ind: IndicatorDef) -> IndicatorDefinition:
    return IndicatorDefinition(
        id=ind.id,
        name=ind.name,
        category=ind.category.value,
        unit=ind.unit,
        frequency=ind.frequency.value,
        description=ind.description,
        kpi=ind.kpi,
    )


def provenance(session: Session, data: IndicatorData) -> SeriesProvenance:
    latest = data.latest_row
    source = session.get(DataSource, data.mapping.source_id)
    return SeriesProvenance(
        source_id=data.mapping.source_id,
        source_name=source.name if source else data.mapping.source_id,
        docs_url=source.docs_url if source else None,
        dataset=data.mapping.dataset,
        series_key=data.mapping.series_key,
        series_id=data.series_id,
        native_unit=latest.unit,
        adjustment=latest.adjustment,
        request_url=latest.source_url,
        retrieved_at=as_utc(latest.retrieved_at),
        source_updated_at=latest.source_updated_at,
        native_observations=len(data.rows),
    )


def latest_checks(session: Session, series_id: str) -> list[QualityCheckResult]:
    """Checks of the most recent ingestion run that attempted this series (a failed attempt
    included, so a broken latest sync is visible even when older observations remain)."""
    run_id = session.scalar(
        select(func.max(QualityCheck.ingestion_run_id)).where(QualityCheck.series_id == series_id)
    )
    if run_id is None:
        return []
    checks = session.scalars(
        select(QualityCheck)
        .where(QualityCheck.series_id == series_id, QualityCheck.ingestion_run_id == run_id)
        .order_by(QualityCheck.id)
    ).all()
    return [QualityCheckResult(rule=c.rule, status=c.status, detail=c.detail) for c in checks]
