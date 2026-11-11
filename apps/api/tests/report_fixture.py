"""Synthetic report content for renderer tests. Values are made up for layout tests only."""

# ruff: noqa: E501, RUF001 - long literal sentences with typographic symbols on purpose

from __future__ import annotations

from datetime import UTC, datetime

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

GDP_CITE = Citation(
    "Eurostat · namq_10_gdp · freq=Q, unit=CLV20_MNAC, s_adj=SCA, na_item=B1GQ (DE)",
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/namq_10_gdp?geo=DE",
    "2026-11-09T17:26:00+00:00",
    "2026-11-05T23:00:00+0100",
)
HICP_CITE = Citation("Eurostat · prc_hicp_minr (DE)", None, "2026-11-09T17:26:00+00:00")


def _quarters(first_year: int, n: int) -> list[str]:
    return [f"{first_year + i // 4}-Q{i % 4 + 1}" for i in range(n)]


def sample_content(*, empty: bool = False) -> ReportContent:
    qs = _quarters(2019, 28)
    gdp = tuple(
        (q, None if q == "2021-Q2" else round(0.4 - 0.1 * (i % 5), 2)) for i, q in enumerate(qs)
    )
    months = [f"{2024 + i // 12}-{i % 12 + 1:02d}" for i in range(30)]
    infl = tuple((m, round(2.0 + 0.05 * i, 2)) for i, m in enumerate(months))
    charts = (
        ReportChart(
            key="gdp",
            title="Real GDP growth (q/q)",
            unit="%",
            series=(ChartSeries("Real GDP q/q", "%", gdp, "bar"),),
            bands=(ChartBand("2020-Q1", "2020-Q2", "Technical recession (realised)"),),
            note="2021-Q2 missing in the stored series.",
            citation=GDP_CITE,
        ),
        ReportChart(
            key="inflation",
            title="Inflation (HICP, y/y)",
            unit="% y/y",
            series=(
                ChartSeries("HICP y/y", "% y/y", infl, "line"),
                ChartSeries("Policy rate", "%", tuple((m, 2.5) for m in months), "step"),
                ChartSeries("Forecast", "% y/y", (("2026-07", 3.4), ("2026-08", 3.3)), "dashed"),
            ),
            citation=HICP_CITE,
        ),
    )
    kpis = (
        KpiRow("Real GDP growth (q/q)", "%", 0.3, "2026-Q3", -0.4, "ok", None, GDP_CITE),
        KpiRow(
            "Inflation (HICP y/y)", "% y/y", 2.1, "2026-10", 0.2, "ok", "p = provisional", HICP_CITE
        ),
        KpiRow("Unemployment rate", "%", None, None, None, "no_data", "Not synced yet."),
    )
    estimates = (
        EstimateRow(
            2,
            0.041,
            "low",
            "HistGradientBoosting",
            "run-h2-hist_gbm",
            "2026-Q3",
            "Did not beat the base rate on 2015+ held-out years.",
        ),
        EstimateRow(
            4, None, None, None, None, None, None, "Model not trained: run `macropulse train`."
        ),
    )
    forecasts = (
        ForecastRow(
            "Real GDP growth (q/q)",
            "%",
            "Direct ridge AR",
            "2026-Q3",
            "2027-Q3",
            0.31,
            -0.56,
            1.12,
            0.75,
            0.71,
        ),
        ForecastRow(
            "Unemployment rate",
            "%",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "Fewer than 40 observations published.",
        ),
    )
    return ReportContent(
        title="MacroPulse country report: Germany",
        country_iso2="DE",
        country_name="Germany",
        as_of=None,
        as_of_label="Latest stored data (generated 2026-11-10)",
        generated_at=datetime(2026, 11, 10, 12, 0, tzinfo=UTC),
        app_version="0.1.0",
        data_basis="Latest stored revision of each official series; not the figures first published.",
        summary=(
            "Real GDP grew 0.3 % q/q in 2026-Q3, −0.4 pp below the previous quarter (Eurostat).",
            "The 2-quarter technical-recession estimate is 4.1 % (low band); the model did not beat the base rate on held-out years.",
            "Forecast intervals covered ≥ 75 % of outcomes in the backtest for GDP at four quarters.",
        ),
        kpis=kpis,
        charts=() if empty else charts,
        estimates=() if empty else estimates,
        forecasts=() if empty else forecasts,
        methodology=(
            "Technical recession: two consecutive quarters of negative real GDP q/q growth.",
            "Forecast intervals: 10th to 90th percentile of past forecast errors.",
        ),
        limitations=("Revised data, not first releases.", "Few recessions per country."),
        citations=(GDP_CITE, HICP_CITE),
    )
