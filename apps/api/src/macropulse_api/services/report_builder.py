"""Assemble a country report from stored data and published models.

Every number comes from the same services the API serves (KPIs, series, live inference, forecast
backtests); every sentence of the summary is a template filled with one of those numbers. Sections
that cannot be built say why (`warnings`, row notes) instead of being dropped silently.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from macropulse_api import __version__
from macropulse_api.errors import ApiError
from macropulse_api.reports.content import (
    ChartBand,
    ChartSeries,
    Citation,
    EstimateRow,
    ForecastRow,
    KpiRow,
    ReportChart,
    ReportContent,
)
from macropulse_api.routers.summary import LATEST_BASIS, as_of_basis, cutoff_for, kpi_value
from macropulse_api.schemas import SeriesProvenance
from macropulse_api.services import forecasts, inference
from macropulse_api.services.series_data import load_indicator, provenance, resolve_indicator
from macropulse_economics import get_country
from macropulse_economics.indicators import INDICATORS
from macropulse_economics.periods import period_end
from macropulse_economics.quality import NORMAL_STATUS
from macropulse_ml.target import technical_recessions

CHART_YEARS = 10
CHARTS = (
    ("real_gdp_qoq", "bar"),
    ("inflation_yoy", "line"),
    ("unemployment_rate", "line"),
    ("policy_rate", "step"),
)
FORECAST_METRICS = ("real_gdp_qoq", "inflation_yoy", "unemployment_rate")
FORECAST_MODEL = "ar"
FORECAST_HORIZON_Q = 4
UNDER_COVERAGE = 0.7

METHODOLOGY = (
    "Technical recession: at least one pair of consecutive quarters with negative quarter-on-"
    "quarter real GDP growth inside the next H quarters (H = 2 or 4). Zero growth is not negative. "
    "This is not an official recession call; for the US, NBER dates are shown only as an external "
    "reference.",
    "Recession probabilities come from the published model of the latest training run. Its track "
    "record is measured walk-forward: each historical estimate was made by a model fitted only on "
    "outcomes known before that year; 2000-2014 are development years, 2015 onwards held out.",
    "Forecasts: direct ridge autoregression refitted at every origin; 80 % intervals are the 10th "
    "to 90th percentile of the model's own past errors at that step, and their coverage is "
    "measured in a rolling-origin backtest.",
    "Key indicators are derived transparently from native official series (q/q and y/y growth "
    "from levels, rates as published); missing observations stay missing.",
)


def _cite(p: SeriesProvenance | None) -> Citation | None:
    if p is None:
        return None
    return Citation(
        label=f"{p.source_name} · {p.dataset} · {p.series_key}",
        url=p.request_url,
        retrieved_at=p.retrieved_at.replace(microsecond=0).isoformat() if p.retrieved_at else None,
        source_updated_at=p.source_updated_at,
    )


def _signed(v: float, unit: str = "") -> str:
    text = f"{abs(v):.2f}"
    sign = "+" if v > 0 else "−" if v < 0 else ""  # noqa: RUF001 - typographic minus in prose
    return f"{sign}{text}{f' {unit}' if unit else ''}"


def _kpis(session: Session, iso: str, cutoff: date) -> tuple[list[KpiRow], list[str]]:
    rows: list[KpiRow] = []
    sentences: list[str] = []
    for ind in (i for i in INDICATORS if i.kpi):
        k = kpi_value(session, iso, ind, cutoff)
        status = "stale" if k.status == "ok" and k.stale else k.status
        note = k.reason
        if k.status == "ok" and k.source_flag and k.source_flag not in NORMAL_STATUS:
            note = f"Source flag: {k.source_flag}"
        if k.status == "ok" and k.stale:
            note = f"Older than its release cycle ({k.days_since_period_end} days at the cut-off)."
        rows.append(
            KpiRow(ind.name, k.unit, k.value, k.period, k.change, status, note, _cite(k.provenance))
        )
        if k.value is not None and ind.id in {
            "real_gdp_qoq",
            "inflation_yoy",
            "unemployment_rate",
            "policy_rate",
        }:
            change = (
                f", {_signed(k.change, 'pp' if '%' in k.unit else k.unit)} versus "
                f"{k.previous_period}"
                if k.change is not None
                else ""
            )
            source = k.provenance.source_name if k.provenance else "stored series"
            sentences.append(
                f"{ind.name}: {k.value:.2f} {k.unit} in {k.period}{change} ({source})."
            )
    return rows, sentences


def _window_start(cutoff: date) -> date:
    return date(cutoff.year - CHART_YEARS, 1, 1)


def _charts(session: Session, iso: str, cutoff: date) -> tuple[list[ReportChart], list[str]]:
    charts: list[ReportChart] = []
    warnings: list[str] = []
    start = _window_start(cutoff)
    for ind_id, style in CHARTS:
        ind = resolve_indicator(ind_id)
        try:
            data = load_indicator(session, iso, ind)
        except ApiError as exc:
            warnings.append(f"{ind.name} chart not included: {exc.message}")
            continue
        known = [(p, v) for p, v in data.points if period_end(p) <= cutoff]
        shown = tuple((p, v) for p, v in known if period_end(p) >= start)
        if not shown:
            warnings.append(f"{ind.name} chart not included: no observation in the window.")
            continue
        bands: list[ChartBand] = []
        note = None
        if ind_id == "real_gdp_qoq":
            for a, b in technical_recessions(dict(known)):
                if period_end(b) >= start:
                    bands.append(ChartBand(a, b, "Technical recession (realised)"))
            note = (
                "Shaded: technical recessions in the stored data (two negative quarters)."
                if bands
                else "No technical recession in this window of the stored data."
            )
        charts.append(
            ReportChart(
                key=ind_id,
                title=ind.name,
                unit=ind.unit,
                series=(ChartSeries(ind.name, ind.unit, shown, style),),
                bands=tuple(bands),
                note=note,
                citation=_cite(provenance(session, data)),
            )
        )
    return charts, warnings


def _track_sentence(track: dict[str, Any]) -> str | None:
    held = track.get("heldout") or {}
    skill = held.get("brier_skill")
    if skill is None:
        return None
    verdict = "beat" if track.get("beats_baseline_heldout") else "did not beat"
    return (
        f"Held-out 2015+ Brier skill vs the base rate {skill:+.3f} "
        f"({held.get('n')} quarters, {held.get('events')} events): it {verdict} the base rate."
    )


def _estimates(
    session: Session, iso: str, as_of: str | None, models_dir: Path
) -> tuple[list[EstimateRow], list[str]]:
    rows: list[EstimateRow] = []
    sentences: list[str] = []
    for h in (2, 4):
        try:
            e = inference.estimate(session, iso, h, as_of, models_dir=models_dir)
        except ApiError as exc:
            rows.append(EstimateRow(h, None, None, None, None, None, None, exc.message))
            continue
        note = None
        if e["in_sample"]:
            wf = e["walk_forward_probability"]
            note = (
                "In-sample fit: this quarter's outcome was in the training data. Walk-forward "
                f"estimate made without it: {wf * 100:.1f} %."
                if wf is not None
                else "In-sample fit: this quarter's outcome was in the training data."
            )
        track = _track_sentence(e["track_record"])
        rows.append(
            EstimateRow(
                h,
                e["probability"],
                e["band"],
                e["model"]["name"],
                e["model"]["id"],
                e["as_of"],
                track,
                note,
            )
        )
        sentence = (
            f"The published {h}-quarter technical-recession model estimates "
            f"{e['probability'] * 100:.1f} % ({e['band']} band) as of {e['as_of']}."
        )
        if e["in_sample"]:
            wf = e["walk_forward_probability"]
            sentence = (
                f"For {e['as_of']} the published {h}-quarter model gives "
                f"{e['probability'] * 100:.1f} %, but that is an in-sample fit (the outcome was in "
                "its training data), not a forecast"
                + (
                    f"; the walk-forward estimate made without that outcome was {wf * 100:.1f} %."
                    if wf is not None
                    else "; no walk-forward estimate exists for this quarter."
                )
            )
        if e["track_record"].get("beats_baseline_heldout") is False:
            sentence += " On the 2015+ held-out years it did not beat the historical base rate."
        sentences.append(sentence)
    if all(r.probability is None for r in rows):
        sentences.append("No recession probability is shown: no usable published model.")
    return rows, sentences


def _forecasts(
    session: Session, iso: str, as_of: str | None
) -> tuple[list[ForecastRow], list[str]]:
    rows: list[ForecastRow] = []
    sentences: list[str] = []
    for metric in FORECAST_METRICS:
        ind = resolve_indicator(metric)
        name, unit = ind.name, ind.unit
        try:
            fc = forecasts.forecast(session, iso, metric, FORECAST_HORIZON_Q, as_of)
        except ApiError as exc:
            rows.append(
                ForecastRow(name, "", None, None, None, None, None, None, None, None, exc.message)
            )
            continue
        model = next(m for m in fc["models"] if m["key"] == FORECAST_MODEL)
        steps = fc["steps"]
        metric_row = next(
            (
                m
                for m in fc["backtest"]["metrics"]
                if m["model"] == FORECAST_MODEL and m["step"] == steps
            ),
            None,
        )
        point = next((p for p in model["path"] if p["step"] == steps), None)
        if point is None:
            rows.append(
                ForecastRow(
                    name,
                    unit,
                    model["name"],
                    fc["origin"],
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    model["reason"] or "No forecast at this horizon.",
                )
            )
            continue
        coverage = metric_row["coverage"] if metric_row else None
        rows.append(
            ForecastRow(
                name,
                unit,
                model["name"],
                fc["origin"],
                point["period"],
                point["value"],
                point["lower"],
                point["upper"],
                coverage,
                metric_row["rel_rmse"] if metric_row else None,
                None if point["lower"] is not None else "Too few past errors for an interval.",
            )
        )
        interval = (
            f" (80 % interval {point['lower']:.2f} to {point['upper']:.2f}"
            + (f"; measured backtest coverage {coverage:.0%}" if coverage is not None else "")
            + ")"
            if point["lower"] is not None
            else ""
        )
        sentences.append(
            f"{model['name']} forecast for {name} in {point['period']}: "
            f"{point['value']:.2f} {unit}{interval}."
        )
    return rows, sentences


def _limitations(estimates: list[EstimateRow], fcs: list[ForecastRow]) -> list[str]:
    out = [
        "All values are latest revised data; the figures first published are not stored, so "
        "historical views are revised-data / release-lag approximations.",
        "Few technical recessions per country: model metrics rest on small event counts.",
        "Probabilities are analytical estimates, not certainties; no confidence interval is shown "
        "because with this few events it would mostly reflect sampling noise.",
    ]
    if any(e.track_record and "did not beat" in e.track_record for e in estimates):
        out.append(
            "The published recession models did not beat the historical base rate on the held-out "
            "years 2015 onwards; read their probabilities with that track record in mind."
        )
    under = [f.indicator for f in fcs if f.coverage is not None and f.coverage < UNDER_COVERAGE]
    if under:
        out.append(
            "Forecast intervals under-covered in the backtest (below 70 % for a nominal 80 %) for: "
            + ", ".join(under)
            + ". Treat them as too narrow."
        )
    return out


def build_report(
    session: Session,
    iso2: str,
    as_of: str | None,
    *,
    models_dir: Path,
    now: datetime | None = None,
) -> ReportContent:
    country = get_country(iso2)
    if country is None:
        raise ApiError(422, "unsupported_country", f"Country '{iso2}' is not supported.")
    iso = iso2.upper()
    generated = now or datetime.now(UTC)
    cutoff = cutoff_for(as_of, generated.date())

    kpis, kpi_text = _kpis(session, iso, cutoff)
    charts, warnings = _charts(session, iso, cutoff)
    estimates, est_text = _estimates(session, iso, as_of, models_dir)
    fcs, fc_text = _forecasts(session, iso, as_of)

    citations: dict[str, Citation] = {}
    for c in [k.citation for k in kpis] + [ch.citation for ch in charts]:
        if c is not None:
            citations.setdefault(c.label, c)

    return ReportContent(
        title=f"MacroPulse country report: {country.name}",
        country_iso2=iso,
        country_name=country.name,
        as_of=as_of,
        as_of_label="Latest stored data"
        if as_of is None
        else f"As of {as_of} (cut-off {cutoff.isoformat()})",
        generated_at=generated,
        app_version=__version__,
        data_basis=LATEST_BASIS if as_of is None else as_of_basis(cutoff),
        summary=tuple(kpi_text + est_text + fc_text),
        kpis=tuple(kpis),
        charts=tuple(charts),
        estimates=tuple(estimates),
        forecasts=tuple(fcs),
        methodology=METHODOLOGY,
        limitations=tuple(_limitations(estimates, fcs)),
        citations=tuple(citations.values()),
        warnings=tuple(warnings),
    )
