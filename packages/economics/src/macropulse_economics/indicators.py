"""Indicator definitions and per-country source mappings, with live-probe verification status.

Every mapping records what the 2026-11-08 feasibility probe actually observed (see
`docs/DATA_FEASIBILITY.md` and `docs/data-feasibility-probe.json`). Nothing here is an
observation: values are ingested by the Phase 3 connectors. A mapping status tells the UI whether a
series can be expected (`verified`), exists but is out of date (`stale`), returned values without
full metadata (`partial`), is not published for that geography (`not_published`) or has not been
mapped yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

PROBE_DATE = "2026-11-08"


class Category(StrEnum):
    GROWTH = "growth"
    PRICES = "prices"
    LABOR = "labor"
    MONETARY = "monetary"
    FISCAL = "fiscal"
    LEADING = "leading"
    REFERENCE = "reference"


class Frequency(StrEnum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUAL = "annual"
    EVENT = "event"  # e.g. policy-rate decisions, recorded on the date of change
    DAILY = "daily"


class MappingStatus(StrEnum):
    VERIFIED = "verified"
    PARTIAL = "partial"
    STALE = "stale"
    NOT_PUBLISHED = "not_published"
    UNMAPPED = "unmapped"


@dataclass(frozen=True, slots=True)
class IndicatorDef:
    id: str
    name: str
    category: Category
    unit: str
    frequency: Frequency
    description: str
    kpi: bool = False  # shown as a headline KPI tile


@dataclass(frozen=True, slots=True)
class SourceMapping:
    indicator_id: str
    country: str
    source_id: str
    dataset: str
    series_key: str
    native_frequency: Frequency
    adjustment: str | None
    status: MappingStatus
    probe_last_period: str | None
    note: str = ""
    scope_note: str = ""
    geo: str | None = None  # native geography when it differs from the country (shared series)


INDICATORS: tuple[IndicatorDef, ...] = (
    IndicatorDef(
        "real_gdp_qoq",
        "Real GDP growth (q/q)",
        Category.GROWTH,
        "%",
        Frequency.QUARTERLY,
        "Quarter-on-quarter change of seasonally and calendar adjusted chain-linked real GDP. "
        "Basis of the technical-recession target.",
        kpi=True,
    ),
    IndicatorDef(
        "real_gdp_yoy",
        "Real GDP growth (y/y)",
        Category.GROWTH,
        "%",
        Frequency.QUARTERLY,
        "Year-on-year change of the same real GDP series.",
    ),
    IndicatorDef(
        "inflation_yoy",
        "Inflation (y/y)",
        Category.PRICES,
        "%",
        Frequency.MONTHLY,
        "Annual rate of change of the all-items HICP (EU) or CPI (US).",
        kpi=True,
    ),
    IndicatorDef(
        "unemployment_rate",
        "Unemployment rate",
        Category.LABOR,
        "% of labour force",
        Frequency.MONTHLY,
        "Seasonally adjusted unemployment rate, total population.",
        kpi=True,
    ),
    IndicatorDef(
        "policy_rate",
        "Policy rate",
        Category.MONETARY,
        "% p.a.",
        Frequency.EVENT,
        "Central-bank policy rate. Euro area members share the ECB rate.",
        kpi=True,
    ),
    IndicatorDef(
        "bond_yield_10y",
        "Long-term government bond yield (10y)",
        Category.MONETARY,
        "% p.a.",
        Frequency.MONTHLY,
        "Ten-year government bond yield, monthly average (EMU convergence series for EU members).",
    ),
    IndicatorDef(
        "short_rate_3m",
        "Short-term interest rate (3m)",
        Category.MONETARY,
        "% p.a.",
        Frequency.MONTHLY,
        "Three-month money-market rate (euro area for members; 3-month Treasury bill for the US).",
    ),
    IndicatorDef(
        "gov_debt_gdp",
        "Government debt",
        Category.FISCAL,
        "% of GDP",
        Frequency.QUARTERLY,
        "Gross government debt as a share of GDP.",
    ),
    IndicatorDef(
        "cli",
        "Composite leading indicator",
        Category.LEADING,
        "index",
        Frequency.MONTHLY,
        "OECD composite leading indicator (amplitude adjusted).",
    ),
    IndicatorDef(
        "yield_spread",
        "Yield-curve slope (10y minus 3m)",
        Category.LEADING,
        "pp",
        Frequency.DAILY,
        "10-year minus 3-month government bond yield.",
    ),
    IndicatorDef(
        "nber_recession",
        "NBER recession (reference)",
        Category.REFERENCE,
        "0/1",
        Frequency.MONTHLY,
        "Official US business-cycle dating — an external reference, never the model target.",
    ),
)

_EU = ("BE", "DE", "FR", "NL")
_ISO3 = {"BE": "BEL", "DE": "DEU", "FR": "FRA", "NL": "NLD"}
_GDP_LAST = {"BE": "2026-Q2", "DE": "2026-Q3", "FR": "2026-Q3", "NL": "2026-Q3"}
_HICP_NOTE = (
    "ECOICOP ver.2 successor of prc_hicp_manr (frozen at 2025-12, finding F-001): covers 1997-01 "
    "onward; overlapping months differ by at most 0.1 pp (checked 2026-11-09)."
)


def _eu_mappings(c: str) -> list[SourceMapping]:
    gdp = SourceMapping(
        "real_gdp_qoq",
        c,
        "eurostat",
        "namq_10_gdp",
        "freq=Q, unit=CLV20_MNAC, s_adj=SCA, na_item=B1GQ",
        Frequency.QUARTERLY,
        "seasonally and calendar adjusted",
        MappingStatus.VERIFIED,
        _GDP_LAST[c],
        "Chain-linked volumes (2020); growth is derived from levels.",
    )
    return [
        gdp,
        SourceMapping(
            "real_gdp_yoy",
            c,
            gdp.source_id,
            gdp.dataset,
            gdp.series_key,
            gdp.native_frequency,
            gdp.adjustment,
            gdp.status,
            gdp.probe_last_period,
            gdp.note,
        ),
        SourceMapping(
            "inflation_yoy",
            c,
            "eurostat",
            "prc_hicp_minr",
            "freq=M, unit=RCH_A, coicop18=TOTAL",
            Frequency.MONTHLY,
            None,
            MappingStatus.VERIFIED,
            "2026-10",
            _HICP_NOTE,
        ),
        SourceMapping(
            "unemployment_rate",
            c,
            "eurostat",
            "une_rt_m",
            "s_adj=SA, age=TOTAL, sex=T, unit=PC_ACT",
            Frequency.MONTHLY,
            "seasonally adjusted",
            MappingStatus.VERIFIED,
            "2026-09",
        ),
        SourceMapping(
            "policy_rate",
            c,
            "ecb",
            "FM",
            "B.U2.EUR.4F.KR.DFR.LEV",
            Frequency.EVENT,
            None,
            MappingStatus.VERIFIED,
            "2026-09-16",
            "ECB deposit facility rate, recorded on decision dates.",
            scope_note="Shared euro area rate — not a national central-bank rate.",
        ),
        SourceMapping(
            "bond_yield_10y",
            c,
            "eurostat",
            "irt_lt_mcby_m",
            "freq=M, int_rt=MCBY",
            Frequency.MONTHLY,
            None,
            MappingStatus.VERIFIED,
            "2026-09",
            "EMU convergence criterion bond yield; live-verified 2026-11-09 from "
            + ("1986-04" if c == "NL" else "1980-01")
            + ".",
        ),
        SourceMapping(
            "short_rate_3m",
            c,
            "eurostat",
            "irt_st_m",
            "freq=M, int_rt=IRT_M3",
            Frequency.MONTHLY,
            None,
            MappingStatus.VERIFIED,
            "2026-10",
            "Eurostat publishes this rate for the euro area only (no national series); "
            "live-verified 2026-11-09 from 1990-01.",
            scope_note="Shared euro area 3-month rate — not a national rate; before 1999 a "
            "Eurostat euro-area aggregate.",
            geo="EA",
        ),
        SourceMapping(
            "gov_debt_gdp",
            c,
            "eurostat",
            "gov_10q_ggdebt",
            "unit=PC_GDP, sector=S13, na_item=GD",
            Frequency.QUARTERLY,
            None,
            MappingStatus.VERIFIED,
            "2026-Q2",
            scope_note="General government, consolidated.",
        ),
        SourceMapping(
            "cli",
            c,
            "oecd",
            "DSD_STES@DF_CLI",
            f"{_ISO3[c]}.M.LI",
            Frequency.MONTHLY,
            "amplitude adjusted",
            MappingStatus.PARTIAL if c in {"DE", "FR"} else MappingStatus.NOT_PUBLISHED,
            "2026-09" if c in {"DE", "FR"} else None,
            "CLI variants found; exact measure/adjustment to be fixed in Phase 3."
            if c in {"DE", "FR"}
            else "OECD publishes only confidence indices for this country (finding F-002).",
        ),
    ]


_US: list[SourceMapping] = [
    SourceMapping(
        "real_gdp_qoq",
        "US",
        "fred",
        "GDPC1",
        "GDPC1",
        Frequency.QUARTERLY,
        "seasonally adjusted annual rate",
        MappingStatus.PARTIAL,
        "2026-Q3",
        "Values verified via fredgraph CSV; units/adjustment metadata need FRED_API_KEY.",
    ),
    SourceMapping(
        "real_gdp_yoy",
        "US",
        "fred",
        "GDPC1",
        "GDPC1",
        Frequency.QUARTERLY,
        "seasonally adjusted annual rate",
        MappingStatus.PARTIAL,
        "2026-Q3",
    ),
    SourceMapping(
        "inflation_yoy",
        "US",
        "fred",
        "CPIAUCSL",
        "CPIAUCSL",
        Frequency.MONTHLY,
        "seasonally adjusted",
        MappingStatus.PARTIAL,
        "2026-09",
        "CPI index; the y/y rate is derived. Not identical to HICP.",
    ),
    SourceMapping(
        "unemployment_rate",
        "US",
        "fred",
        "UNRATE",
        "UNRATE",
        Frequency.MONTHLY,
        "seasonally adjusted",
        MappingStatus.PARTIAL,
        "2026-10",
    ),
    SourceMapping(
        "policy_rate",
        "US",
        "fred",
        "FEDFUNDS",
        "FEDFUNDS",
        Frequency.MONTHLY,
        None,
        MappingStatus.PARTIAL,
        "2026-10",
        "Effective federal funds rate (monthly average).",
    ),
    SourceMapping(
        "bond_yield_10y",
        "US",
        "fred",
        "GS10",
        "GS10",
        Frequency.MONTHLY,
        None,
        MappingStatus.PARTIAL,
        "2026-10",
        "10-year Treasury constant maturity, monthly average; values verified 2026-11-09 from "
        "1953-04 via fredgraph CSV.",
    ),
    SourceMapping(
        "short_rate_3m",
        "US",
        "fred",
        "TB3MS",
        "TB3MS",
        Frequency.MONTHLY,
        None,
        MappingStatus.PARTIAL,
        "2026-10",
        "3-month Treasury bill, secondary market, monthly average; values verified 2026-11-09.",
        scope_note="Treasury bill rate — not an interbank rate like the euro-area 3-month rate.",
    ),
    SourceMapping(
        "gov_debt_gdp",
        "US",
        "fred",
        "GFDEGDQ188S",
        "GFDEGDQ188S",
        Frequency.QUARTERLY,
        None,
        MappingStatus.PARTIAL,
        "2026-Q2",
        scope_note="Federal debt only — not comparable with EU general-government debt.",
    ),
    SourceMapping(
        "cli",
        "US",
        "oecd",
        "DSD_STES@DF_CLI",
        "USA.M.LI",
        Frequency.MONTHLY,
        "amplitude adjusted",
        MappingStatus.PARTIAL,
        "2026-09",
        "CLI variants found; exact measure/adjustment to be fixed in Phase 3.",
    ),
    SourceMapping(
        "yield_spread",
        "US",
        "fred",
        "T10Y3M",
        "T10Y3M",
        Frequency.DAILY,
        None,
        MappingStatus.PARTIAL,
        "2026-11-06",
    ),
    SourceMapping(
        "nber_recession",
        "US",
        "fred",
        "USREC",
        "USREC",
        Frequency.MONTHLY,
        None,
        MappingStatus.PARTIAL,
        "2026-10",
        "External reference only — never used as the technical-recession target.",
    ),
]

MAPPINGS: tuple[SourceMapping, ...] = tuple(m for c in _EU for m in _eu_mappings(c)) + tuple(_US)

_INDICATOR_INDEX = {i.id: i for i in INDICATORS}


def get_indicator(indicator_id: str) -> IndicatorDef | None:
    return _INDICATOR_INDEX.get(indicator_id)


def mappings_for(country: str) -> dict[str, SourceMapping]:
    """Source mapping per indicator id for one country (missing id = unmapped)."""
    return {m.indicator_id: m for m in MAPPINGS if m.country == country.upper()}
