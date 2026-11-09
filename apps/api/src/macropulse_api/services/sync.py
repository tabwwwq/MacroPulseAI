"""`data-sync`: fetch native official series, validate, upsert with provenance, record quality.

One ingestion run per source. Each series is committed on its own, so an interrupted sync can simply
be re-run (upserts are idempotent). A failing series never aborts the others; the run ends
`succeeded`, `partial` or `failed` with a safe error summary (no secrets, no driver messages).
"""

from __future__ import annotations

import logging
from collections import defaultdict
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from macropulse_api.models import IngestionRun, Observation, QualityCheck
from macropulse_economics.connectors import ConnectorError, FetchResult, SeriesRequest, fetch_series
from macropulse_economics.connectors.http import Fetcher
from macropulse_economics.periods import period_start
from macropulse_economics.quality import CheckResult, run_checks
from macropulse_economics.series import native_series

logger = logging.getLogger("macropulse.sync")

FetchFn = Callable[[Fetcher, SeriesRequest], FetchResult]


@dataclass
class SeriesOutcome:
    series_id: str
    ok: bool
    rows: int = 0
    first: str | None = None
    last: str | None = None
    warnings: int = 0
    error: str | None = None


@dataclass
class SyncReport:
    runs: dict[str, tuple[int, str]] = field(default_factory=dict)  # source -> (run id, status)
    outcomes: list[SeriesOutcome] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def upsert_observations(session: Session, result: FetchResult, run_id: int) -> int:
    req = result.request
    existing = {
        o.period: o
        for o in session.scalars(select(Observation).where(Observation.series_id == req.series_id))
    }
    for fo in result.observations:
        row = existing.get(fo.period)
        if row is None:
            row = Observation(
                series_id=req.series_id,
                source_id=req.source_id,
                geo=req.geo,
                dataset=req.dataset,
                series_key=req.series_key,
                period=fo.period,
                period_start=period_start(fo.period),
                frequency=req.frequency,
            )
            session.add(row)
        row.value = fo.value
        row.obs_status = fo.obs_status
        row.unit = req.unit
        row.adjustment = req.adjustment
        row.source_url = result.url
        row.source_updated_at = result.source_updated_at
        row.retrieved_at = result.retrieved_at
        row.ingestion_run_id = run_id
    return len(result.observations)


def _store_checks(
    session: Session, run_id: int, series_id: str, checks: Iterable[CheckResult]
) -> None:
    for c in checks:
        session.add(
            QualityCheck(
                ingestion_run_id=run_id,
                series_id=series_id,
                rule=c.rule,
                status=c.status,
                detail=c.detail,
            )
        )


def _sync_series(
    session: Session,
    fetcher: Fetcher,
    fetch: FetchFn,
    req: SeriesRequest,
    *,
    run_id: int,
    day: date,
) -> SeriesOutcome:
    """Fetch, validate and upsert one native series in its own transaction."""
    outcome = SeriesOutcome(series_id=req.series_id, ok=False)
    try:
        result = fetch(fetcher, req)
        checks = run_checks(result, day)
        if result.unit_label:
            checks.append(
                CheckResult("unit_echo", "pass", f"Source unit label: {result.unit_label}")
            )
        if any(c.status == "fail" for c in checks):
            raise ConnectorError("; ".join(c.detail for c in checks if c.status == "fail"))
        outcome.rows = upsert_observations(session, result, run_id)
        _store_checks(session, run_id, req.series_id, checks)
        session.commit()
        outcome.ok = True
        outcome.first = result.observations[0].period
        outcome.last = result.observations[-1].period
        outcome.warnings = sum(c.status == "warn" for c in checks)
    except ConnectorError as exc:
        session.rollback()
        outcome.error = str(exc)
    except Exception as exc:  # unexpected: keep going, log class only
        session.rollback()
        outcome.error = f"unexpected {type(exc).__name__}"
        logger.exception("sync_series_error", extra={"series_id": req.series_id})
    if outcome.error:
        outcome.rows = 0
        _store_checks(session, run_id, req.series_id, [CheckResult("fetch", "fail", outcome.error)])
        session.commit()
    return outcome


def run_sync(
    factory: sessionmaker[Session],
    fetcher: Fetcher,
    *,
    sources: Iterable[str] | None = None,
    countries: Iterable[str] | None = None,
    today: date | None = None,
    fetch: FetchFn = fetch_series,
) -> SyncReport:
    requests, skipped = native_series(countries, sources)
    report = SyncReport(skipped=skipped)
    by_source: dict[str, list[SeriesRequest]] = defaultdict(list)
    for r in requests:
        by_source[r.source_id].append(r)
    day = today or datetime.now(UTC).date()

    for source_id, reqs in sorted(by_source.items()):
        with factory() as session:
            started = IngestionRun(source_id=source_id, status="running", rows_upserted=0)
            session.add(started)
            session.commit()
            run_id = started.id
        outcomes = []
        for req in reqs:
            with factory() as session:
                outcomes.append(_sync_series(session, fetcher, fetch, req, run_id=run_id, day=day))
        report.outcomes.extend(outcomes)

        errors = [f"{o.series_id}: {o.error}" for o in outcomes if o.error]
        rows_total = sum(o.rows for o in outcomes)
        status = "partial" if errors else "succeeded"
        if len(errors) == len(reqs):
            status = "failed"
        with factory() as session:
            run = session.get(IngestionRun, run_id)
            if run is None:  # pragma: no cover - the row was created above in this process
                raise RuntimeError(f"ingestion run {run_id} disappeared")
            run.status = status
            run.rows_upserted = rows_total
            run.finished_at = datetime.now(UTC)
            run.error_summary = "; ".join(errors)[:2000] or None
            session.commit()
        report.runs[source_id] = (run_id, status)
        logger.info(
            "sync_source_done", extra={"source": source_id, "status": status, "rows": rows_total}
        )
    return report
