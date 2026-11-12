"""ALFRED vintages for US series: sync into `vintage_*` tables and revision analysis.

Vintages are fetched only with a server-side `FRED_API_KEY` (CLI `macropulse vintages-sync`). The
dashboards and models keep reading `observations` (latest revision); this module powers the explicit
"first release versus today" views, and nothing here estimates a missing value.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, sessionmaker

from macropulse_api.models import VintageObservation as VintageRow
from macropulse_api.models import VintageSeries
from macropulse_economics.connectors import ConnectorError, SeriesRequest
from macropulse_economics.connectors.alfred import VintageFetch, fetch_vintages
from macropulse_economics.connectors.alfred import VintageObservation as Vintage
from macropulse_economics.connectors.http import Fetcher
from macropulse_economics.indicators import get_indicator, mappings_for
from macropulse_economics.periods import period_end, shift
from macropulse_economics.redact import redact_secrets
from macropulse_economics.series import request_for
from macropulse_economics.transforms import Transform, transform_for
from macropulse_economics.vintages import (
    RevisionPoint,
    derived_as_of,
    revision_history,
    revision_summary,
)

logger = logging.getLogger("macropulse.vintages")

# Indicators whose US source series is fetched with its full revision history.
VINTAGE_INDICATORS: tuple[str, ...] = ("real_gdp_qoq", "inflation_yoy", "unemployment_rate")
VINTAGE_COUNTRY = "US"

# A stored "first vintage" counts as the first release only when it came out soon after the period
# ended (US GDP advance estimate ~30 days, CPI and unemployment ~1-2 weeks). Later appearances are
# back-filled history (e.g. the 1992 vintage that added real GDP back to 1947).
FIRST_RELEASE_MAX_DAYS = 120

VintageFetchFn = Callable[[Fetcher, SeriesRequest, str | None], VintageFetch]


class VintagesUnavailableError(LookupError):
    """No stored vintages for the requested series (not synced yet)."""


def vintage_requests() -> list[SeriesRequest]:
    """Native FRED series behind `VINTAGE_INDICATORS`, each once."""
    mappings = mappings_for(VINTAGE_COUNTRY)
    out: dict[str, SeriesRequest] = {}
    for indicator in VINTAGE_INDICATORS:
        mapping = mappings.get(indicator)
        if mapping is None or mapping.source_id != "fred":
            continue
        request = request_for(mapping)
        out.setdefault(request.series_id, request)
    return list(out.values())


@dataclass(slots=True)
class VintageOutcome:
    series_id: str
    rows: int = 0
    vintages: int = 0
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass(slots=True)
class VintageSyncReport:
    outcomes: list[VintageOutcome] = field(default_factory=list)


def _default_fetch(fetcher: Fetcher, request: SeriesRequest, key: str | None) -> VintageFetch:
    return fetch_vintages(fetcher, request, key)


def store_vintages(session: Session, result: VintageFetch) -> VintageOutcome:
    """Replace the stored history of one series with a complete new fetch."""
    req = result.request
    starts = sorted({o.realtime_start for o in result.observations})
    session.execute(delete(VintageRow).where(VintageRow.series_id == req.series_id))
    series = session.get(VintageSeries, req.series_id) or VintageSeries(series_id=req.series_id)
    series.source_id = req.source_id
    series.geo = req.geo
    series.dataset = req.dataset
    series.frequency = req.frequency
    series.unit = req.unit[:64]
    series.source_url = redact_secrets(result.url) or ""
    series.retrieved_at = result.retrieved_at
    series.rows = len(result.observations)
    series.vintages = len(starts)
    series.first_vintage = starts[0] if starts else None
    series.last_vintage = starts[-1] if starts else None
    session.merge(series)
    session.flush()
    session.add_all(
        VintageRow(
            series_id=req.series_id,
            period=o.period,
            value=o.value,
            realtime_start=o.realtime_start,
            realtime_end=o.realtime_end,
        )
        for o in result.observations
    )
    return VintageOutcome(req.series_id, rows=len(result.observations), vintages=len(starts))


def sync_vintages(
    factory: sessionmaker[Session],
    fetcher: Fetcher,
    api_key: str | None,
    *,
    fetch: VintageFetchFn = _default_fetch,
) -> VintageSyncReport:
    """Fetch and store every vintage series; one failing series never removes stored data."""
    report = VintageSyncReport()
    for request in vintage_requests():
        try:
            result = fetch(fetcher, request, api_key)
        except ConnectorError as exc:
            message = redact_secrets(str(exc)) or "fetch failed"
            if api_key:
                message = message.replace(api_key.strip(), "REDACTED")
            report.outcomes.append(VintageOutcome(request.series_id, error=message))
            logger.warning("vintage_fetch_failed", extra={"series": request.series_id})
            continue
        with factory() as session:
            outcome = store_vintages(session, result)
            session.commit()
        report.outcomes.append(outcome)
        logger.info(
            "vintage_sync_done",
            extra={"series": request.series_id, "rows": outcome.rows, "vintages": outcome.vintages},
        )
    return report


def load_vintages(session: Session, series_id: str) -> list[Vintage]:
    rows = session.execute(select(VintageRow).where(VintageRow.series_id == series_id)).scalars()
    return [Vintage(r.period, r.value, r.realtime_start, r.realtime_end) for r in rows]


def revisions(session: Session, country: str, indicator_id: str) -> dict[str, Any]:
    """First release versus current vintage for one US indicator, with provenance."""
    mapping = mappings_for(country).get(indicator_id)
    definition = get_indicator(indicator_id)
    if mapping is None or definition is None:  # pragma: no cover - guarded by the router
        raise VintagesUnavailableError(indicator_id)
    request = request_for(mapping)
    series = session.get(VintageSeries, request.series_id)
    rows = load_vintages(session, request.series_id) if series else []
    if series is None or not rows:
        raise VintagesUnavailableError(request.series_id)
    transform = transform_for(indicator_id, mapping.source_id)
    points = revision_history(rows, transform)
    # ALFRED starts at the series' first stored vintage: a period already published before then
    # shows that vintage's value, which is NOT its first release. Such points are listed but kept
    # out of every statistic.
    archive_start = min(r.realtime_start for r in rows)

    def is_first_release(p: RevisionPoint) -> bool:
        lag = (p.first_published - period_end(p.period)).days
        return p.first_published > archive_start and 0 <= lag <= FIRST_RELEASE_MAX_DAYS

    genuine = [p for p in points if is_first_release(p)]
    summary = revision_summary(genuine)
    signals = (
        technical_signals(rows, genuine, transform)
        if transform.kind == "growth" and transform.lag == 1
        else []
    )
    return {
        "country": country,
        "indicator": {"id": definition.id, "name": definition.name, "unit": definition.unit},
        "transform": transform.description or "As published by the source.",
        "revision_unit": "pp" if definition.unit.startswith("%") else definition.unit,
        "series": {
            "series_id": series.series_id,
            "dataset": series.dataset,
            "source_url": series.source_url,
            "retrieved_at": series.retrieved_at,
            "rows": series.rows,
            "vintages": series.vintages,
            "first_vintage": series.first_vintage,
            "last_vintage": series.last_vintage,
        },
        "points": [
            {
                "period": p.period,
                "first_published": p.first_published,
                "first_value": p.first_value,
                "latest_value": p.latest_value,
                "revision": p.revision,
                "first_release": is_first_release(p),
            }
            for p in points
        ],
        "archive_start": archive_start,
        "technical_signals": signals,
        "summary": {
            "count": summary.count,
            "mean_abs_revision": summary.mean_abs_revision,
            "max_abs_revision": summary.max_abs_revision,
            "max_abs_period": summary.max_abs_period,
            "sign_changes": summary.sign_changes,
        },
        "computed_at": datetime.now(UTC),
        "note": (
            "First release: the value derived from the first vintage in which the period appeared, "
            "using levels from that same vintage. Latest: the same derivation on the current "
            "vintage. Revisions are latest minus first release. Only values published within "
            f"{FIRST_RELEASE_MAX_DAYS} days of the period's end count as first releases; earlier "
            f"periods (the archive starts {archive_start.isoformat()}) and back-filled history are "
            "shown but excluded from the statistics. Source: ALFRED, Federal Reserve Bank of "
            "St. Louis."
        ),
    }


def technical_signals(
    rows: list[Vintage], points: list[RevisionPoint], transform: Transform
) -> list[dict[str, Any]]:
    """Quarters ending two consecutive negative q/q readings — as known on the day the quarter was
    first published (the previous quarter taken from that same vintage) and in today's data.

    Only quarters where at least one view shows the signal are returned. Zero is not negative.
    """
    by_period = {p.period: p for p in points}
    out: list[dict[str, Any]] = []
    for p in points:
        prev = shift(p.period, -1)
        prev_then = derived_as_of(rows, prev, p.first_published, transform)
        prev_now = by_period[prev].latest_value if prev in by_period else None
        then = prev_then is not None and prev_then < 0 and p.first_value < 0
        now = (
            prev_now is not None
            and p.latest_value is not None
            and prev_now < 0
            and p.latest_value < 0
        )
        if then or now:
            out.append(
                {
                    "period": p.period,
                    "published": p.first_published,
                    "as_first_known": then,
                    "in_latest_data": now,
                    "first_values": [prev_then, p.first_value],
                    "latest_values": [prev_now, p.latest_value],
                }
            )
    return out
