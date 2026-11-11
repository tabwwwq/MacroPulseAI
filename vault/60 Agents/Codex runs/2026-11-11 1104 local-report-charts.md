---
type: codex-run
name: local-report-charts
date: 2026-11-11
time: "11:04"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-report-charts

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 11:04. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```python
> """Chart renderer for PDF reports.
>
> Renders a :class:`~macropulse_api.reports.content.ReportChart` to deterministic PNG bytes using a
> headless Agg canvas (no ``matplotlib.pyplot`` global state, safe in a multi-threaded API).
> """
>
> from __future__ import annotations
>
> import io
> from datetime import datetime, time
>
> import matplotlib.dates as mdates
> from matplotlib.backends.backend_agg import FigureCanvasAgg
> from matplotlib.figure import Figure
> from matplotlib.lines import Line2D
> from matplotlib.patches import Patch
>
> from macropulse_api.reports.content import ReportChart
> from macropulse_economics.periods import period_start, shift
>
> _TEXT_COLOR = "#1f2937"
> _GRID_COLOR = "#e5e7eb"
> _BAND_COLOR = "#9ca3af"
> _SERIES_COLORS = ("#1d4ed8", "#b45309", "#047857", "#7c3aed")
>
>
> def _x(period: str) -> float:
>     """Matplotlib date number for the start of *period* at midnight."""
>     return mdates.date2num(datetime.combine(period_start(period), time()))
>
>
> def _bar_width_days(period: str) -> float:
>     """Bar width in days: 60 for quarterly, 20 for monthly, 3 otherwise."""
>     if "-Q" in period:
>         return 60.0
>     if len(period) == 7:  # "YYYY-MM"
>         return 20.0
>     return 3.0
>
>
> def _has_any_value(chart: ReportChart) -> bool:
>     return any(v is not None for s in chart.series for _, v in s.points)
>
>
> def _style_axes(ax: object) -> None:
>     """Apply the print-friendly light theme to *ax*."""
>     ax.set_facecolor("white")
>     ax.tick_params(axis="both", colors=_TEXT_COLOR, labelsize=7)
>     for spine in ax.spines.values():
>         spine.set_color(_TEXT_COLOR)
>     ax.yaxis.grid(True, color=_GRID_COLOR, linewidth=0.8)
>     ax.set_axisbelow(True)
>     ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # type: ignore[no-untyped-call]
>     ax.xaxis.set_major_formatter(
>         mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())  # type: ignore[no-untyped-call]
>     )
>
>
> def _draw_bands(ax: object, chart: ReportChart) -> list[Patch]:
>     """Draw shaded bands and return one legend handle per distinct label."""
>     handles: list[Patch] = []
>     seen: set[str] = set()
>     for band in chart.bands:
>         start = _x(band.start)
>         end = _x(shift(band.end, 1))
>         ax.axvspan(start, end, color=_BAND_COLOR, alpha=0.25, label=band.label)
>         if band.label not in seen:
>             seen.add(band.label)
>             handles.append(Patch(facecolor=_BAND_COLOR, alpha=0.25, label=band.label))
>     return handles
>
>
> def _draw_series(ax: object, chart: ReportChart) -> list[Line2D]:
>     """Draw every series (line/dashed/step/bar) and return legend handles."""
>     handles: list[Line2D] = []
>     for idx, s in enumerate(chart.series):
>         color = _SERIES_COLORS[idx % len(_SERIES_COLORS)]
>         if s.style == "bar":
>             xs = [_x(p) for p, v in s.points if v is not None]
>             ys = [float(v) for _, v in s.points if v is not None]
>             width = _bar_width_days(s.points[0][0]) if s.points else 3.0
>             ax.bar(xs, ys, width=width, color=color, label=s.name)
>             handles.append(Line2D([], [], color=color, label=s.name))
>         else:
>             xs = [_x(p) for p, _ in s.points]
>             ys = [float("nan") if v is None else float(v) for _, v in s.points]
>             if s.style == "dashed":
>                 line, = ax.plot(xs, ys, color=color, linestyle="--", label=s.name)
>             elif s.style == "step":
>                 line, = ax.plot(xs, ys, color=color, drawstyle="steps-post", label=s.name)
>             else:
>                 line, = ax.plot(xs, ys, color=color, label=s.name)
>             handles.append(line)
>     return handles
>
>
> def render_chart_png(
>     chart: ReportChart,
>     *,
>     width_in: float = 7.0,
>     height_in: float = 2.6,
>     dpi: int = 150,
> ) -> bytes:
>     """Render *chart* to PNG bytes of exactly ``width_in*dpi`` x ``height_in*dpi`` pixels."""
>     if not _has_any_value(chart):
>         raise ValueError(f"chart '{chart.key}' has no data")
>
>     fig = Figure(figsize=(width_in, height_in), dpi=dpi)
>     fig.set_layout_engine("constrained")
>     FigureCanvasAgg(fig)
>     fig.patch.set_facecolor("white")
>
>     ax = fig.add_subplot(111)
>     _style_axes(ax)
>     band_handles = _draw_bands(ax, chart)
>     series_handles = _draw_series(ax, chart)
>
>     ax.set_title(chart.title, fontsize=10, color=_TEXT_COLOR)
>     ax.set_ylabel(chart.unit, fontsize=8, color=_TEXT_COLOR)
>
>     handles = series_handles + band_handles
>     if handles:
>         ax.legend(handles=handles, loc="upper left", fontsize=7, frameon=False)
>
>     buf = io.BytesIO()
>     fig.savefig(buf, format="png", dpi=dpi, metadata={"Software": None})
>     return buf.getvalue()
> ```
>
> - Switched all x positions to `mdates.date2num` so series, bars and bands share the same date axis; removed the integer `x_index`/`all_periods`/`x_dates` scaffolding.
> - Dropped the invalid `canvas.close()` call (kept `FigureCanvasAgg(fig)` so the figure has an Agg canvas).
> - Band legend handles now use `matplotlib.patches.Patch(facecolor=..., alpha=0.25, label=...)` with one handle per distinct label.
> - Split the body into `_style_axes`, `_draw_bands`, `_draw_series`, `_x`, `_bar_width_days`, `_has_any_value` to satisfy PLR0912/PLR0915 and removed unused imports (`Any`, `font_manager`, `numpy`).
> - Added `# type: ignore[no-untyped-call]` only on the `AutoDateLocator`/`ConciseDateFormatter` lines; kept constrained layout, exact size, `metadata={"Software": None}` and the `ValueError` guard.

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the chart renderer for PDF reports.
>
> ## Files
> - CREATE `apps/api/src/macropulse_api/reports/charts.py` — the only file you may create or edit.
> - CONTEXT (provided below, do not change): `apps/api/src/macropulse_api/reports/content.py` (the data classes),
>   `apps/api/tests/test_report_render.py` (the four chart tests are the specification),
>   `packages/economics/src/macropulse_economics/periods.py` (use its `period_start`).
>
> ## Function
> ```python
> def render_chart_png(chart: ReportChart, *, width_in: float = 7.0, height_in: float = 2.6, dpi: int = 150) -> bytes:
> ```
> Returns PNG bytes of exactly `width_in*dpi` x `height_in*dpi` pixels.
>
> ## Requirements
> 1. Use `matplotlib.figure.Figure` with `matplotlib.backends.backend_agg.FigureCanvasAgg`. Do NOT import `matplotlib.pyplot` (no global state; the API is multi-threaded).
> 2. Print-friendly light theme: white background, text and axes `#1f2937`, horizontal grid `#e5e7eb`.
>    Series colours in order: `#1d4ed8`, `#b45309`, `#047857`, `#7c3aed` (cycle if more).
> 3. X positions: `datetime.combine(period_start(period), time())` for every point (works for "2026-Q3", "2026-10" and "2026-09-16").
> 4. Missing values (`None`) are gaps: use `float("nan")` for lines; skip them for bars. Never interpolate or fill.
> 5. Series styles: `"line"` solid; `"dashed"` linestyle `"--"`; `"step"` `drawstyle="steps-post"`; `"bar"` `ax.bar(...)` with width 60 days for quarterly periods, 20 days for monthly, 3 days otherwise.
> 6. Bands (`chart.bands`): `ax.axvspan(start, end_of_end_period, color="#9ca3af", alpha=0.25, label=band.label)` where the end is the start of the period after `band.end` (use `period_start(shift(band.end, 1))`; import `shift` from the same module). Add each distinct band label to the legend only once.
> 7. Title `chart.title` (fontsize 10), y-axis label `chart.unit` (fontsize 8), tick labels fontsize 7, legend fontsize 7, upper left, no frame. Dates: `AutoDateLocator` + `ConciseDateFormatter`.
> 8. If no series has any non-`None` value: `raise ValueError(f"chart '{chart.key}' has no data")`.
> 9. Exact size and determinism: `Figure(figsize=(width_in, height_in), dpi=dpi)`, use `fig.set_layout_engine("constrained")` (not `bbox_inches="tight"`, which changes the size), and save with
>    `fig.savefig(buf, format="png", dpi=dpi, metadata={"Software": None})` so two calls give identical bytes.
> 10. Full type hints, module docstring, ruff-clean with line length 100, no unused imports.
>
> ## Out of scope
> Do not edit tests, `content.py` or any other file. The lead runs the tests and sends you any failures.
>
> # Output file
>
> `apps/api/src/macropulse_api/reports/charts.py`
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
>     ge
> …(truncated)
