"""Indicator catalog: definitions, verified source mappings and ingestion state per country."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query
from sqlalchemy import select

from macropulse_api.db import as_utc
from macropulse_api.deps import SessionDep
from macropulse_api.models import DataSource, IngestionRun
from macropulse_api.routers.countries import unsupported_country
from macropulse_api.schemas import (
    CatalogEntry,
    CountryCatalog,
    ErrorResponse,
    IndicatorCatalog,
    IndicatorDefinition,
    IngestionState,
    SourceMappingInfo,
)
from macropulse_api.services.coverage import SeriesStats, series_stats, stats_for_mapping
from macropulse_economics import COUNTRIES, get_country
from macropulse_economics.indicators import INDICATORS, PROBE_DATE, SourceMapping, mappings_for

router = APIRouter(prefix="/api/indicators", tags=["indicators"])

CountryQuery = Annotated[
    str | None,
    Query(pattern=r"^[A-Za-z]{2}$", description="ISO alpha-2 code; omit for all countries."),
]


def _mapping_info(m: SourceMapping | None, sources: dict[str, DataSource]) -> SourceMappingInfo:
    if m is None:
        return SourceMappingInfo(
            status="unmapped",
            source_id=None,
            source_name=None,
            docs_url=None,
            dataset=None,
            series_key=None,
            native_frequency=None,
            adjustment=None,
            probe_last_period=None,
            probe_date=None,
            note="No official source mapped for this country yet.",
            scope_note="",
        )
    src = sources.get(m.source_id)
    return SourceMappingInfo(
        status=m.status.value,
        source_id=m.source_id,
        source_name=src.name if src else m.source_id,
        docs_url=src.docs_url if src else None,
        dataset=m.dataset,
        series_key=m.series_key,
        native_frequency=m.native_frequency.value,
        adjustment=m.adjustment,
        probe_last_period=m.probe_last_period,
        probe_date=PROBE_DATE,
        note=m.note,
        scope_note=m.scope_note,
    )


def _ingestion(
    m: SourceMapping | None,
    stats: dict[str, SeriesStats],
    last_success: dict[str, datetime | None],
) -> IngestionState:
    s = stats_for_mapping(m, stats)
    return IngestionState(
        observations=s.count if s else 0,
        latest_period=s.latest_period if s else None,
        source_last_success_at=last_success.get(m.source_id) if m else None,
    )


@router.get(
    "/catalog",
    response_model=IndicatorCatalog,
    summary="Indicator definitions, verified source mappings and ingestion state",
    responses={422: {"model": ErrorResponse, "description": "Malformed or unsupported country."}},
)
def indicator_catalog(session: SessionDep, country: CountryQuery = None) -> IndicatorCatalog:
    if country is not None and get_country(country) is None:
        raise unsupported_country(country)
    isos = [country.upper()] if country else [c.iso2 for c in COUNTRIES]

    sources = {s.id: s for s in session.scalars(select(DataSource)).all()}
    last_success = {}
    for source_id in sources:
        run = session.scalars(
            select(IngestionRun)
            .where(
                IngestionRun.source_id == source_id,
                IngestionRun.status.in_(["succeeded", "partial"]),
            )
            .order_by(IngestionRun.finished_at.desc())
            .limit(1)
        ).first()
        last_success[source_id] = as_utc(run.finished_at) if run else None

    stats = series_stats(session)
    countries = []
    for iso in isos:
        mapped = mappings_for(iso)
        items = []
        for ind in INDICATORS:
            m = mapped.get(ind.id)
            items.append(
                CatalogEntry(
                    indicator=IndicatorDefinition(
                        id=ind.id,
                        name=ind.name,
                        category=ind.category.value,
                        unit=ind.unit,
                        frequency=ind.frequency.value,
                        description=ind.description,
                        kpi=ind.kpi,
                    ),
                    mapping=_mapping_info(m, sources),
                    ingestion=_ingestion(m, stats, last_success),
                )
            )
        countries.append(CountryCatalog(country=iso, items=items))
    return IndicatorCatalog(probe_date=PROBE_DATE, countries=countries)
