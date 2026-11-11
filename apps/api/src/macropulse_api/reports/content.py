"""Report content contract: everything a report shows, already computed from stored data.

The renderers (PDF, charts, CSV) only lay this out; they never fetch, compute or invent numbers.
`None` always means "not available" and must be printed as "N/A" (with the note when one exists).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

DISCLAIMER = (
    "MacroPulse AI report: analytical estimates from official statistics and statistical models. "
    "Not investment advice, not an official recession call and not a forecast of certainty."
)


@dataclass(frozen=True)
class Citation:
    """Where a set of numbers comes from."""

    label: str  # e.g. "Eurostat · namq_10_gdp · freq=Q, unit=CLV20_MNAC, ... (DE)"
    url: str | None = None  # exact request URL of the last successful fetch
    retrieved_at: str | None = None  # ISO timestamp of that fetch (data freshness)
    source_updated_at: str | None = None  # as reported by the source, when it reports one


@dataclass(frozen=True)
class ChartSeries:
    name: str
    unit: str
    # (period, value); period like "2026-Q3", "2026-10" or "2026-09-16"
    points: tuple[tuple[str, float | None], ...]
    style: str = "line"  # "line" | "dashed" | "step" | "bar"


@dataclass(frozen=True)
class ChartBand:
    """Shaded period, e.g. a realised technical recession or an external NBER reference."""

    start: str
    end: str
    label: str


@dataclass(frozen=True)
class ReportChart:
    key: str
    title: str
    unit: str
    series: tuple[ChartSeries, ...]
    bands: tuple[ChartBand, ...] = ()
    note: str | None = None
    citation: Citation | None = None


@dataclass(frozen=True)
class KpiRow:
    label: str
    unit: str
    value: float | None
    period: str | None
    change: float | None  # vs the previous period, in `unit` (pp for rates)
    status: str  # "ok" | "stale" | "no_data" | "unavailable"
    note: str | None = None  # reason when there is no value, or a source flag
    citation: Citation | None = None


@dataclass(frozen=True)
class EstimateRow:
    """Published recession model for one horizon, or why there is none."""

    horizon: int
    probability: float | None  # 0..1
    band: str | None  # "low" | "moderate" | "elevated" | "high"
    model: str | None
    version: str | None
    as_of: str | None
    track_record: str | None  # one sentence from recorded metrics
    note: str | None = None  # e.g. "Model not trained", in-sample flag


@dataclass(frozen=True)
class ForecastRow:
    indicator: str
    unit: str
    model: str | None
    origin: str | None
    target: str | None  # period the value refers to
    value: float | None
    lower: float | None  # empirical 80 % interval
    upper: float | None
    coverage: float | None  # measured backtest coverage of that interval at this step, 0..1
    rel_rmse: float | None  # RMSE relative to the naive forecast at this step
    note: str | None = None


@dataclass(frozen=True)
class ReportContent:
    title: str
    country_iso2: str
    country_name: str
    as_of: str | None  # requested as-of quarter; None = latest
    # human text, e.g. "Latest stored data" or "As of 2008-Q2 (cut-off 2008-06-30)"
    as_of_label: str
    generated_at: datetime  # timezone-aware UTC
    app_version: str
    data_basis: str  # what the numbers are and are not (revisions, vintages)
    summary: tuple[str, ...]  # rules-based sentences, each traceable to a number below
    kpis: tuple[KpiRow, ...]
    charts: tuple[ReportChart, ...]
    estimates: tuple[EstimateRow, ...]
    forecasts: tuple[ForecastRow, ...]
    methodology: tuple[str, ...]
    limitations: tuple[str, ...]
    citations: tuple[Citation, ...]
    disclaimer: str = DISCLAIMER
    # e.g. sections that could not be built
    warnings: tuple[str, ...] = field(default_factory=tuple)
