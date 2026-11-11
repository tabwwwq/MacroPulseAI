"""Specification tests for the report renderers (charts, PDF, CSV). Layout only: the content is a
synthetic fixture and nothing here measures data or model quality."""

from __future__ import annotations

import csv
import io
import re
from dataclasses import replace

import pytest
from PIL import Image
from pypdf import PdfReader

from macropulse_api.reports.charts import render_chart_png
from macropulse_api.reports.content import ChartSeries, ReportChart
from macropulse_api.reports.csv_export import CSV_HEADER, content_to_csv
from macropulse_api.reports.pdf import render_pdf

from .report_fixture import GDP_CITE, sample_content

# --- charts ------------------------------------------------------------------------------------


def test_chart_is_a_png_of_the_requested_size() -> None:
    chart = sample_content().charts[0]
    png = render_chart_png(chart, width_in=7.0, height_in=2.6, dpi=150)
    assert png[:8] == b"\x89PNG\r\n\x1a\n"
    img = Image.open(io.BytesIO(png))
    assert img.size == (1050, 390)


def test_chart_rendering_is_deterministic() -> None:
    chart = sample_content().charts[1]  # line + step + dashed, monthly periods
    assert render_chart_png(chart) == render_chart_png(chart)


def test_chart_accepts_daily_periods_and_gaps() -> None:
    chart = ReportChart(
        key="rate",
        title="Policy rate",
        unit="%",
        series=(
            ChartSeries(
                "ECB DFR",
                "%",
                (("2024-06-12", 3.75), ("2024-09-18", None), ("2024-10-23", 3.25)),
                "step",
            ),
        ),
    )
    assert render_chart_png(chart)[:4] == b"\x89PNG"


def test_chart_without_any_value_is_refused() -> None:
    chart = ReportChart("x", "Empty", "%", (ChartSeries("s", "%", (("2026-Q1", None),)),))
    with pytest.raises(ValueError, match="no data"):
        render_chart_png(chart)


# --- PDF ---------------------------------------------------------------------------------------


def _text(pdf: bytes) -> tuple[PdfReader, str]:
    reader = PdfReader(io.BytesIO(pdf))
    return reader, "\n".join(page.extract_text() or "" for page in reader.pages)


def test_pdf_contains_every_section_with_sources_and_caveats() -> None:
    content = sample_content()
    pdf = render_pdf(content)
    assert pdf[:5] == b"%PDF-"
    reader, text = _text(pdf)
    flat = re.sub(r"\s+", " ", text)
    assert len(reader.pages) >= 2
    assert reader.metadata is not None
    assert reader.metadata.title == content.title
    assert reader.metadata.author == "MacroPulse AI"
    for needle in (
        content.title,
        content.as_of_label,
        content.data_basis[:40],
        "Real GDP growth (q/q)",
        "Model not trained",
        "Fewer than 40 observations published.",
        "Not synced yet.",
        GDP_CITE.label[:40],
        GDP_CITE.url,
        "Technical recession: two consecutive quarters",
        "Revised data, not first releases.",
        content.disclaimer[:50],
    ):
        assert needle in flat, needle
    for sentence in content.summary:
        assert sentence[:35] in flat, sentence
    assert (
        "N/A" in flat
    )  # missing KPI and forecast values are printed, never left blank or invented
    assert "4.1 %" in flat  # probability formatted as a percentage
    assert re.search(r"[Pp]age 1 of \d+", flat)


def test_pdf_keeps_unicode_symbols() -> None:
    _, text = _text(render_pdf(sample_content()))
    assert "−0.4 pp" in text  # noqa: RUF001 - the typographic minus is the point
    assert "≥" in text


def test_pdf_with_empty_sections_says_so() -> None:
    _, text = _text(render_pdf(sample_content(empty=True)))
    assert "Not available for this selection." in text


def test_pdf_lists_warnings_when_present() -> None:
    content = replace(
        sample_content(), warnings=("Forecasts could not be built: data_not_synced.",)
    )
    _, text = _text(render_pdf(content))
    assert "Forecasts could not be built" in text


# --- CSV ---------------------------------------------------------------------------------------


def test_csv_has_one_row_per_chart_point_with_citations() -> None:
    content = sample_content()
    text = content_to_csv(content)
    assert "\r\n" in text
    rows = list(csv.reader(io.StringIO(text)))
    assert tuple(rows[0]) == CSV_HEADER
    expected = sum(len(s.points) for c in content.charts for s in c.series)
    assert len(rows) - 1 == expected
    by_key = {(r[0], r[1], r[3]): r for r in rows[1:]}
    gap = by_key[("Real GDP growth (q/q)", "Real GDP q/q", "2021-Q2")]
    assert gap[4] == ""  # missing stays missing
    first = by_key[("Real GDP growth (q/q)", "Real GDP q/q", "2019-Q1")]
    assert first[2] == "%"
    assert first[5] == GDP_CITE.label  # commas inside the label survive quoting
    assert first[6] == GDP_CITE.url
    assert first[7] == GDP_CITE.retrieved_at
    assert first[8] == "latest"
    assert first[9] == "2026-11-10T12:00:00+00:00"


def test_csv_of_a_report_without_charts_is_just_the_header() -> None:
    rows = list(csv.reader(io.StringIO(content_to_csv(sample_content(empty=True)))))
    assert rows == [list(CSV_HEADER)]
