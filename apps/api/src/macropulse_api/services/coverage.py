"""Derive *current* support levels and source health from what is actually stored.

Nothing here is hard-coded optimism: until observations exist, every country is `unavailable`, and a
source that never ran is `never_synced`. Phase 3 extends `country_support` with real coverage rules.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from macropulse_api.db import as_utc
from macropulse_api.models import Country, DataSource, IngestionRun
from macropulse_api.schemas import CountrySupport, SourceStatus, SourceSyncStatus
from macropulse_economics import SupportLevel

NO_OBSERVATIONS_REASON = (
    "No observations have been ingested yet. Official-data connectors (Eurostat, ECB, FRED, "
    "World Bank, OECD) are implemented in Phase 3; run the data sync once they are available."
)

_RUN_STATUS_TO_SOURCE_STATUS: dict[str, SourceSyncStatus] = {
    "running": "running",
    "succeeded": "ok",
    "partial": "degraded",
    "failed": "failed",
}


def country_support(country: Country) -> CountrySupport:
    return CountrySupport(
        level=SupportLevel.UNAVAILABLE,
        target=SupportLevel(country.target_support),
        reason=NO_OBSERVATIONS_REASON,
    )


def source_status(session: Session, source: DataSource, key_configured: bool) -> SourceStatus:
    latest = session.scalars(
        select(IngestionRun)
        .where(IngestionRun.source_id == source.id)
        .order_by(IngestionRun.started_at.desc(), IngestionRun.id.desc())
        .limit(1)
    ).first()
    last_success = session.scalars(
        select(IngestionRun)
        .where(IngestionRun.source_id == source.id, IngestionRun.status == "succeeded")
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
