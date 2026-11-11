---
type: codex-run
name: local-report-csv
date: 2026-11-11
time: "11:05"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-report-csv

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 11:05. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```py
> """CSV export of report chart data.
>
> Lays out the chart points of a :class:`ReportContent` as RFC 4180 CSV text.
> The renderer never fetches, computes or invents numbers; it only formats what
> the content already holds.  ``None`` values stay empty (never zero).
> """
>
> from __future__ import annotations
>
> import csv
> import io
>
> from macropulse_api.reports.content import ReportContent
>
> CSV_HEADER: tuple[str, ...] = (
>     "chart",
>     "series",
>     "unit",
>     "period",
>     "value",
>     "source",
>     "source_url",
>     "retrieved_at",
>     "report_as_of",
>     "generated_at",
> )
>
>
> def _format_value(value: float | None) -> str:
>     """Render a point value: empty string when missing, otherwise ``.10g``."""
>     if value is None:
>         return ""
>     return format(value, ".10g")
>
>
> def content_to_csv(content: ReportContent) -> str:
>     """Return the chart data of *content* as CSV text.
>
>     The first row is :data:`CSV_HEADER`.  Then one row per point, for every
>     chart in order, every series in order, every point in order.  Fields that
>     are ``None`` (or whose citation is absent) are written as empty strings.
>     """
>     buffer = io.StringIO()
>     writer = csv.writer(buffer, lineterminator="\r\n")
>     writer.writerow(CSV_HEADER)
>
>     as_of = content.as_of or "latest"
>     generated_at = content.generated_at.isoformat()
>
>     for chart in content.charts:
>         citation = chart.citation
>         for series in chart.series:
>             for period, value in series.points:
>                 writer.writerow(
>                     (
>                         chart.title,
>                         series.name,
>                         series.unit,
>                         period,
>                         _format_value(value),
>                         citation.label if citation is not None else "",
>                         citation.url if citation is not None and citation.url is not None else "",
>                         (
>                             citation.retrieved_at
>                             if citation is not None and citation.retrieved_at is not None
>                             else ""
>                         ),
>                         as_of,
>                         generated_at,
>                     )
>                 )
>
>     return buffer.getvalue()
> ```
>
> - Used `csv.writer` on an `io.StringIO` with `lineterminator="\r\n"` so commas/quotes in `GDP_CITE.label` are quoted per RFC 4180, matching the test's `csv.reader` round-trip.
> - `value` is `""` for `None` and `format(value, ".10g")` otherwise; `as_of` falls back to `"latest"` and `generated_at` uses `isoformat()` (yields `2026-11-10T12:00:00+00:00` for the fixture).
> - Citation fields are guarded individually so a `None` citation or any `None` field writes an empty string.
> - No charts → only the header row is emitted (no trailing blank line beyond the header's own terminator).
> - Kept line length ≤ 100 and added full type hints plus a module docstring for ruff-cleanliness.

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the CSV export of report chart data.
>
> ## Files
> - CREATE `apps/api/src/macropulse_api/reports/csv_export.py` — the only file you may create or edit.
> - CONTEXT (provided below, do not change): `apps/api/src/macropulse_api/reports/content.py`,
>   `apps/api/tests/test_report_render.py` (the two CSV tests are the specification),
>   `apps/api/tests/report_fixture.py`.
>
> ## API
> ```python
> CSV_HEADER: tuple[str, ...] = (
>     "chart", "series", "unit", "period", "value",
>     "source", "source_url", "retrieved_at", "report_as_of", "generated_at",
> )
>
> def content_to_csv(content: ReportContent) -> str:
> ```
>
> ## Requirements
> 1. Use the standard `csv` module (`csv.writer` on an `io.StringIO`, `lineterminator="\r\n"`), so fields
>    with commas or quotes are quoted correctly (RFC 4180).
> 2. First row: `CSV_HEADER`. Then one row per point, for every chart in order, every series in order,
>    every point in order:
>    `chart.title, series.name, series.unit, period, value, citation.label, citation.url, citation.retrieved_at, content.as_of or "latest", content.generated_at.isoformat()`.
> 3. `value`: empty string when `None` (missing stays missing, never 0); otherwise `format(value, ".10g")`.
> 4. When `chart.citation` is `None`, or one of its fields is `None`, write an empty string.
> 5. No other rows (no blank lines, no footer). A report without charts returns only the header line.
> 6. Full type hints, module docstring, ruff-clean (line length 100).
>
> ## Out of scope
> Do not edit tests or other files. The lead runs the tests and sends you any failures.
>
> # Output file
>
> `apps/api/src/macropulse_api/reports/csv_export.py`
>
> # Context files
>
> ## `apps/api/src/macropulse_api/reports/content.py`
>
> ```py
> """Report content contract: everything a report shows, already computed from stored data.
>
> The renderers (PDF, charts, CSV) only lay this out; they never fetch, compute or invent numbers.
> `None` always means "not available" and must be printed as "N/A" (with the note when one exists).
> """
>
> from __future__ import annotations
>
> from dataclasses import dataclass, field
> from datetime import datetime
>
> DISCLAIMER = (
>     "MacroPulse AI report: analytical estimates from official statistics and statistical models. "
>     "Not investment advice, not an official recession call and not a forecast of certainty."
> )
>
>
> @dataclass(frozen=True)
> class Citation:
>     """Where a set of numbers comes from."""
>
>     label: str  # e.g. "Eurostat · namq_10_gdp · freq=Q, unit=CLV20_MNAC, ... (DE)"
>     url: str | None = None  # exact request URL of the last successful fetch
>     retrieved_at: str | None = None  # ISO timestamp of that fetch (data freshness)
>     source_updated_at: str | None = None  # as reported by the source, when it reports one
>
>
> @dataclass(frozen=True)
> class ChartSeries:
>     name: str
>     unit: str
>     # (period, value); period like "2026-Q3", "2026-10" or "2026-09-16"
>     points: tuple[tuple[str, float | None], ...]
>     style: str = "line"  # "line" | "dashed" | "step" | "bar"
>
>
> @dataclass(frozen=True)
> class ChartBand:
>     """Shaded period, e.g. a realised technical recession or an external NBER reference."""
>
>     start: str
>     end: str
>     label: str
>
>
> @dataclass(frozen=True)
> class ReportChart:
>     key: str
>     title: str
>     unit: str
>     series: tuple[ChartSeries, ...]
>     bands: tuple[ChartBand, ...] = ()
>     note: str | None = None
>     citation: Citation | None = None
>
>
> @dataclass(frozen=True)
> class KpiRow:
>     label: str
>     unit: str
>     value: float | None
>     period: str | None
>     change: float | None  # vs the previous period, in `unit` (pp for rates)
>     status: str  # "ok" | "stale" | "no_data" | "unavailable"
>     note: str | None = None  # reason when there is no value, or a source flag
>     citation: Citation | None = None
>
>
> @dataclass(frozen=True)
> class EstimateRow:
>     """Published recession model for one horizon, or why there is none."""
>
>     horizon: int
>     probability: float | None  # 0..1
>     band: str | None  # "low" | "moderate" | "elevated" | "high"
>     model: str | None
>     version: str | None
>     as_of: str | None
>     track_record: str | None  # one sentence from recorded metrics
>     note: str | None = None  # e.g. "Model not trained", in-sample flag
>
>
> @dataclass(frozen=True)
> class ForecastRow:
>     indicator: str
>     unit: str
>     model: str | None
>     origin: str | None
>     target: str | None  # period the value refers to
>     value: float | None
>     lower: float | None  # empirical 80 % interval
>     upper: float | None
>     coverage: float | None  # measured backtest coverage of that interval at this step, 0..1
>     rel_rmse: float | None  # RMSE relative to the naive forecast at this step
>     note: str | None = None
>
>
> @dataclass(frozen=True)
> class ReportContent:
>     title: str
>     country_iso2: str
>     country_name: str
>     as_of: str | None  # requested as-of quarter; None = latest
>     # human text, e.g. "Latest stored data" or "As of 2008-Q2 (cut-off 2008-06-30)"
>     as_of_label: str
>     generated_at: datetime  # timezone-aware UTC
>     app_version: str
>     data_basis: str  # what the numbers are and are not (revisions, vintages)
>     summary: tuple[str, ...]  # rules-based sentences, each traceable to a number below
>     kpis: tuple[KpiRow, ...]
>     charts: tuple[ReportChart, ...]
>     estimates: tuple[EstimateRow, ...]
>     forecasts: tuple[ForecastRow, ...]
>     methodology: tuple[str, ...]
>     limitations: tuple[str, ...]
>     citations: tuple[Citation, ...]
>     disclaimer: str = DISCLAIMER
>     # e.g. sections that could not be built
>     warnings: tuple[str, ...] = field(default_factory=tuple)
>
> ```
>
> ## `apps/api/tests/test_report_render.py`
>
> ```py
> """Specification tests for the report renderers (charts, PDF, CSV). Layout only: the content is a
> synthetic fixture and nothing here measures data or model quality."""
>
> from __future__ import annotations
>
> import csv
> import io
> import re
> from dataclasses import replace
>
> import pytest
> from PIL import Image
> from pypdf import PdfReader
>
> from macropulse_api.r
> …(truncated)
