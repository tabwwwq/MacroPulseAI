"""Native series to ingest, derived from the indicator catalog.

Several indicators can share one native series (real GDP levels feed both q/q and y/y growth) and
several countries can share one series (the ECB rate for all euro-area members); each native series
is fetched and stored exactly once.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace

from macropulse_economics.connectors.base import SeriesRequest
from macropulse_economics.connectors.registry import CONNECTORS
from macropulse_economics.indicators import MAPPINGS, MappingStatus, SourceMapping

SYNCABLE = {MappingStatus.VERIFIED, MappingStatus.PARTIAL}

# Units of the *native* series as published (Eurostat/ECB/OECD echo them back, checked on ingest;
# FRED units are from the series documentation and are not machine-verified without the API key).
NATIVE_UNITS: dict[tuple[str, str], str] = {
    ("eurostat", "namq_10_gdp"): "Chain-linked volumes (2020), million units of national currency",
    ("eurostat", "une_rt_m"): "% of population in the labour force",
    ("eurostat", "prc_hicp_minr"): "Annual rate of change, %",
    ("eurostat", "gov_10q_ggdebt"): "% of GDP",
    ("ecb", "FM"): "% per annum",
    ("fred", "GDPC1"): "Billions of chained 2017 dollars, SAAR (FRED documentation)",
    ("fred", "CPIAUCSL"): "Index 1982-1984=100, SA (FRED documentation)",
    ("fred", "UNRATE"): "%, SA (FRED documentation)",
    ("fred", "FEDFUNDS"): "% (FRED documentation)",
    ("eurostat", "irt_lt_mcby_m"): "% per annum",
    ("eurostat", "irt_st_m"): "% per annum",
    ("fred", "GS10"): "% per annum (FRED documentation)",
    ("fred", "TB3MS"): "% per annum (FRED documentation)",
    ("fred", "GFDEGDQ188S"): "% of GDP (FRED documentation)",
    ("fred", "T10Y3M"): "percentage points (FRED documentation)",
    ("fred", "USREC"): "1 = recession, 0 = expansion (FRED documentation)",
    ("oecd", "DSD_STES@DF_CLI"): "Index, long-term average = 100 (OECD)",
}


def geo_for(mapping: SourceMapping) -> str:
    """Geography of the native series: shared euro-area series (the ECB rate, the euro-area
    3-month rate) are stored once as "EA"."""
    if mapping.geo:
        return mapping.geo
    return "EA" if mapping.source_id == "ecb" else mapping.country


def request_for(mapping: SourceMapping) -> SeriesRequest:
    return SeriesRequest(
        source_id=mapping.source_id,
        dataset=mapping.dataset,
        series_key=mapping.series_key,
        geo=geo_for(mapping),
        frequency=mapping.native_frequency.value,
        unit=NATIVE_UNITS.get((mapping.source_id, mapping.dataset), "see source documentation"),
        adjustment=mapping.adjustment,
    )


def series_id_for(mapping: SourceMapping) -> str:
    return request_for(mapping).series_id


def native_series(
    countries: Iterable[str] | None = None, sources: Iterable[str] | None = None
) -> tuple[list[SeriesRequest], list[str]]:
    """(requests to fetch, human-readable reasons for mappings that cannot be synced yet)."""
    want_c = {c.upper() for c in countries} if countries else None
    want_s = set(sources) if sources else None
    by_id: dict[str, SeriesRequest] = {}
    indicators: dict[str, set[str]] = {}
    skipped: list[str] = []
    for m in MAPPINGS:
        if want_c is not None and m.country not in want_c:
            continue
        if want_s is not None and m.source_id not in want_s:
            continue
        label = f"{m.country}/{m.indicator_id}"
        if m.status not in SYNCABLE:
            skipped.append(f"{label}: {m.status.value}")
            continue
        if m.source_id not in CONNECTORS:
            skipped.append(f"{label}: no {m.source_id} connector yet")
            continue
        req = request_for(m)
        by_id.setdefault(req.series_id, req)
        indicators.setdefault(req.series_id, set()).add(m.indicator_id)
    requests = [
        replace(r, indicator_ids=tuple(sorted(indicators[r.series_id]))) for r in by_id.values()
    ]
    return sorted(requests, key=lambda r: r.series_id), sorted(set(skipped))
