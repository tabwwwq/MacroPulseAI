"""Derive *current* support levels and source health from what is actually stored.

Nothing here is hard-coded optimism: a country's level follows the observations in the database,
and a source that never ran is `never_synced`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from macropulse_api.db import as_utc
from macropulse_api.models import Country, DataSource, IngestionRun, Observation
from macropulse_api.schemas import CountrySupport, SourceStatus, SourceSyncStatus
from macropulse_economics import SupportLevel
from macropulse_economics.connectors import CONNECTORS
from macropulse_economics.indicators import MappingStatus, SourceMapping, mappings_for
from macropulse_economics.periods import days_since_end
from macropulse_economics.quality import MAX_AGE_DAYS
from macropulse_economics.series import SYNCABLE, series_id_for

CORE_INDICATORS = ("real_gdp_qoq", "inflation_yoy", "unemployment_rate")
CORE_LABELS = {
    "real_gdp_qoq": "real GDP",
    "inflation_yoy": "inflation",
    "unemployment_rate": "unemployment",
}
SYNC_HINT = "Run `uv run macropulse data-sync` to ingest official data."

_RUN_STATUS_TO_SOURCE_STATUS: dict[str, SourceSyncStatus] = {
    "running": "running",
    "succeeded": "ok",
    "partial": "degraded",
    "failed": "failed",
}


@dataclass(frozen=True, slots=True)
class SeriesStats:
    count: int
    latest_period: str
    latest_start: date
    retrieved_at: datetime | None


def series_stats(session: Session) -> dict[str, SeriesStats]:
    """Observation count and latest period per stored native series."""
    rows = session.execute(
        select(
            Observation.series_id,
            func.count(),
            func.max(Observation.period_start),
            func.max(Observation.retrieved_at),
        ).group_by(Observation.series_id)
    ).all()
    out: dict[str, SeriesStats] = {}
    for series_id, count, latest_start, retrieved in rows:
        period = session.scalar(
            select(Observation.period).where(
                Observation.series_id == series_id, Observation.period_start == latest_start
            )
        )
        out[series_id] = SeriesStats(int(count), period or "", latest_start, as_utc(retrieved))
    return out


def stats_for_mapping(
    mapping: SourceMapping | None, stats: dict[str, SeriesStats]
) -> SeriesStats | None:
    if mapping is None or mapping.status not in SYNCABLE or mapping.source_id not in CONNECTORS:
        return None
    return stats.get(series_id_for(mapping))


def _is_fresh(mapping: SourceMapping, s: SeriesStats, today: date) -> bool:
    limit = MAX_AGE_DAYS.get(mapping.native_frequency.value)
    return limit is None or days_since_end(s.latest_period, today) <= limit


def country_support(
    country: Country, stats: dict[str, SeriesStats], today: date | None = None
) -> CountrySupport:
    """`full`: verified, fresh real GDP + inflation + unemployment stored. `partial`: real GDP
    stored (the recession target is computable) but something else is missing, stale or unverified.
    `unavailable`: no real-GDP observations."""
    day = today or datetime.now(UTC).date()
    target = SupportLevel(country.target_support)
    mappings = mappings_for(country.iso2)
    have: dict[str, SeriesStats] = {}
    for ind in CORE_INDICATORS:
        s = stats_for_mapping(mappings.get(ind), stats)
        if s is not None:
            have[ind] = s

    if "real_gdp_qoq" not in have:
        return CountrySupport(
            level=SupportLevel.UNAVAILABLE,
            target=target,
            reason=f"No real-GDP observations stored yet. {SYNC_HINT}",
        )

    problems: list[str] = []
    for ind in CORE_INDICATORS:
        m = mappings.get(ind)
        s = have.get(ind)
        if m is None or s is None:
            problems.append(f"{CORE_LABELS[ind]} not ingested")
            continue
        if not _is_fresh(m, s, day):
            problems.append(f"{CORE_LABELS[ind]} stale (latest {s.latest_period})")
        if m.status is not MappingStatus.VERIFIED:
            problems.append(f"{CORE_LABELS[ind]} series metadata not verified ({m.source_id})")
    latest = ", ".join(
        f"{CORE_LABELS[i]} {have[i].latest_period}" for i in CORE_INDICATORS if i in have
    )
    if not problems:
        return CountrySupport(
            level=SupportLevel.FULL,
            target=target,
            reason=f"Verified official series ingested and current — latest: {latest}.",
        )
    return CountrySupport(
        level=SupportLevel.PARTIAL,
        target=target,
        reason=f"Ingested ({latest}); limitations: {'; '.join(problems)}.",
    )


def source_status(session: Session, source: DataSource, key_configured: bool) -> SourceStatus:
    latest = session.scalars(
        select(IngestionRun)
        .where(IngestionRun.source_id == source.id)
        .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
        .limit(1)
    ).first()
    # Freshness = last run that fetched data successfully (a partial run did fetch some series).
    last_success = session.scalars(
        select(IngestionRun)
        .where(
            IngestionRun.source_id == source.id, IngestionRun.status.in_(["succeeded", "partial"])
        )
        .order_by(IngestionRun.finished_at.desc(), IngestionRun.id.desc())
        .limit(1)
    ).first()
    status: SourceSyncStatus = "never_synced"
    if latest is not None:
        status = _RUN_STATUS_TO_SOURCE_STATUS.get(latest.status, "failed")
    return SourceStatus(
        id=source.id,
        name=source.name,
        publisher=source.publisher,
        docs_url=source.docs_url,
        terms_url=source.terms_url,
        attribution=source.attribution,
        requires_api_key=source.requires_api_key,
        api_key_configured=key_configured if source.requires_api_key else None,
        status=status,
        last_attempt_at=as_utc(latest.started_at) if latest else None,
        last_success_at=as_utc(last_success.finished_at) if last_success else None,
        last_rows_upserted=latest.rows_upserted if latest else None,
        last_error=latest.error_summary if latest and latest.status != "succeeded" else None,
    )
