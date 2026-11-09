"""Lineage and data-quality inventory of every native series the catalog maps to a connector.

One row per stored (or expected) native series: what was requested, how many observations are
stored, when they were fetched, and the checks of the most recent attempt. Nothing is inferred
from the probe: a series that never synced says `not_synced`.
"""

from __future__ import annotations

import csv
import io
from collections import Counter
from dataclasses import dataclass, field
from datetime import UTC, datetime
from urllib.parse import quote

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from macropulse_api.db import as_utc
from macropulse_api.models import DataSource, Observation, QualityCheck
from macropulse_api.schemas import DataQualityReport, SeriesHealth, StoredSeries
from macropulse_api.services.series_data import latest_checks
from macropulse_economics.connectors import CONNECTORS, SeriesRequest
from macropulse_economics.indicators import MAPPINGS
from macropulse_economics.series import SYNCABLE, request_for

EXPORT_PATH = "/api/observations/export"


@dataclass
class _Expected:
    request: SeriesRequest
    mapping_status: str
    indicators: set[str] = field(default_factory=set)
    countries: set[str] = field(default_factory=set)


def expected_series(country: str | None = None) -> dict[str, _Expected]:
    """Native series the catalog asks us to ingest, keyed by series id."""
    out: dict[str, _Expected] = {}
    for m in MAPPINGS:
        if m.status not in SYNCABLE or m.source_id not in CONNECTORS:
            continue
        if country is not None and m.country != country:
            continue
        req = request_for(m)
        entry = out.setdefault(req.series_id, _Expected(req, m.status.value))
        entry.indicators.add(m.indicator_id)
        entry.countries.add(m.country)
    if country is None:
        return out
    # A shared series (ECB rate) lists every member it serves, not only the filtered country.
    for m in MAPPINGS:
        if m.status in SYNCABLE and m.source_id in CONNECTORS:
            sid = request_for(m).series_id
            if sid in out:
                out[sid].countries.add(m.country)
    return out


def _health(observations: int, statuses: list[str]) -> SeriesHealth:
    if "fail" in statuses:
        return "fail"
    if observations == 0:
        return "not_synced"
    return "warn" if "warn" in statuses else "pass"


def _stored(
    session: Session, sid: str, exp: _Expected, sources: dict[str, DataSource]
) -> StoredSeries:
    req = exp.request
    count, first_start, last_start = session.execute(
        select(
            func.count(), func.min(Observation.period_start), func.max(Observation.period_start)
        ).where(Observation.series_id == sid)
    ).one()

    def label_at(start: object) -> str | None:
        if start is None:
            return None
        return session.scalar(
            select(Observation.period).where(
                Observation.series_id == sid, Observation.period_start == start
            )
        )

    latest = session.scalars(
        select(Observation)
        .where(Observation.series_id == sid)
        .order_by(Observation.retrieved_at.desc())
        .limit(1)
    ).first()
    checks = latest_checks(session, sid)
    run_id = session.scalar(
        select(func.max(QualityCheck.ingestion_run_id)).where(QualityCheck.series_id == sid)
    )
    source = sources.get(req.source_id)
    return StoredSeries(
        series_id=sid,
        source_id=req.source_id,
        source_name=source.name if source else req.source_id,
        dataset=req.dataset,
        series_key=req.series_key,
        geo=req.geo,
        frequency=req.frequency,
        unit=latest.unit if latest else req.unit,
        adjustment=req.adjustment,
        indicators=sorted(exp.indicators),
        countries=sorted(exp.countries),
        mapping_status=exp.mapping_status,
        observations=int(count),
        first_period=label_at(first_start),
        last_period=label_at(last_start),
        retrieved_at=as_utc(latest.retrieved_at) if latest else None,
        source_updated_at=latest.source_updated_at if latest else None,
        request_url=latest.source_url if latest else None,
        last_checked_run_id=run_id,
        health=_health(int(count), [c.status for c in checks]),
        quality=checks,
        export_path=f"{EXPORT_PATH}?series_id={quote(sid, safe='')}",
    )


def quality_report(session: Session, country: str | None = None) -> DataQualityReport:
    sources = {s.id: s for s in session.scalars(select(DataSource))}
    expected = expected_series(country)
    items = [_stored(session, sid, exp, sources) for sid, exp in sorted(expected.items())]
    counts = Counter(i.health for i in items)
    return DataQualityReport(
        country=country,
        items=items,
        counts={h: counts.get(h, 0) for h in ("pass", "warn", "fail", "not_synced")},
        generated_at=datetime.now(UTC),
    )


CSV_COLUMNS = (
    "period",
    "value",
    "source_flag",
    "unit",
    "adjustment",
    "frequency",
    "geo",
    "source_id",
    "dataset",
    "series_key",
    "source_url",
    "retrieved_at",
    "source_updated_at",
    "ingestion_run_id",
    "attribution",
)


def observations_csv(session: Session, series_id: str) -> tuple[str, int]:
    """Raw stored observations with per-row provenance (RFC 4180, CRLF). Returns (csv, rows)."""
    rows = session.scalars(
        select(Observation)
        .where(Observation.series_id == series_id)
        .order_by(Observation.period_start)
    ).all()
    attribution = ""
    if rows:
        source = session.get(DataSource, rows[0].source_id)
        attribution = source.attribution if source else ""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\r\n")
    writer.writerow(CSV_COLUMNS)
    for r in rows:
        retrieved = as_utc(r.retrieved_at)
        writer.writerow(
            [
                r.period,
                repr(r.value),
                r.obs_status or "",
                r.unit,
                r.adjustment or "",
                r.frequency,
                r.geo,
                r.source_id,
                r.dataset,
                r.series_key,
                r.source_url,
                retrieved.isoformat() if retrieved else "",
                r.source_updated_at or "",
                r.ingestion_run_id,
                attribution,
            ]
        )
    return buf.getvalue(), len(rows)
