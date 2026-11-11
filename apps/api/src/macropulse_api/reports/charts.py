"""Chart renderer for PDF reports.

Renders a :class:`~macropulse_api.reports.content.ReportChart` to deterministic PNG bytes using a
headless Agg canvas (no ``matplotlib.pyplot`` global state, safe in a multi-threaded API).
"""

from __future__ import annotations

import io
from datetime import datetime, time

import matplotlib.dates as mdates
from matplotlib.axes import Axes
from matplotlib.backends.backend_agg import FigureCanvasAgg
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

from macropulse_api.reports.content import ReportChart
from macropulse_economics.periods import period_start, shift

_TEXT_COLOR = "#1f2937"
_GRID_COLOR = "#e5e7eb"
_BAND_COLOR = "#9ca3af"
_SERIES_COLORS = ("#1d4ed8", "#b45309", "#047857", "#7c3aed")


def _x(period: str) -> float:
    """Matplotlib date number for the start of *period* at midnight."""
    when = datetime.combine(period_start(period), time())
    return float(mdates.date2num(when))  # type: ignore[no-untyped-call]


def _bar_width_days(period: str) -> float:
    """Bar width in days: 60 for quarterly, 20 for monthly, 3 otherwise."""
    if "-Q" in period:
        return 60.0
    if len(period) == 7:  # "YYYY-MM"
        return 20.0
    return 3.0


def _has_any_value(chart: ReportChart) -> bool:
    return any(v is not None for s in chart.series for _, v in s.points)


def _style_axes(ax: Axes) -> None:
    """Apply the print-friendly light theme to *ax*."""
    ax.set_facecolor("white")
    ax.tick_params(axis="both", colors=_TEXT_COLOR, labelsize=7)
    for spine in ax.spines.values():
        spine.set_color(_TEXT_COLOR)
    ax.yaxis.grid(True, color=_GRID_COLOR, linewidth=0.8)
    ax.set_axisbelow(True)
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())  # type: ignore[no-untyped-call]
    ax.xaxis.set_major_formatter(
        mdates.ConciseDateFormatter(ax.xaxis.get_major_locator())  # type: ignore[no-untyped-call]
    )


def _draw_bands(ax: Axes, chart: ReportChart) -> list[Patch]:
    """Draw shaded bands and return one legend handle per distinct label."""
    handles: list[Patch] = []
    seen: set[str] = set()
    for band in chart.bands:
        start = _x(band.start)
        end = _x(shift(band.end, 1))
        ax.axvspan(start, end, color=_BAND_COLOR, alpha=0.25, label=band.label)
        if band.label not in seen:
            seen.add(band.label)
            handles.append(Patch(facecolor=_BAND_COLOR, alpha=0.25, label=band.label))
    return handles


def _draw_series(ax: Axes, chart: ReportChart) -> list[Line2D]:
    """Draw every series (line/dashed/step/bar) and return legend handles."""
    handles: list[Line2D] = []
    for idx, s in enumerate(chart.series):
        color = _SERIES_COLORS[idx % len(_SERIES_COLORS)]
        if s.style == "bar":
            xs = [_x(p) for p, v in s.points if v is not None]
            ys = [float(v) for _, v in s.points if v is not None]
            width = _bar_width_days(s.points[0][0]) if s.points else 3.0
            ax.bar(xs, ys, width=width, color=color, label=s.name)
            handles.append(Line2D([], [], color=color, label=s.name))
        else:
            xs = [_x(p) for p, _ in s.points]
            ys = [float("nan") if v is None else float(v) for _, v in s.points]
            if s.style == "dashed":
                (line,) = ax.plot(xs, ys, color=color, linestyle="--", label=s.name)
            elif s.style == "step":
                (line,) = ax.plot(xs, ys, color=color, drawstyle="steps-post", label=s.name)
            else:
                (line,) = ax.plot(xs, ys, color=color, label=s.name)
            handles.append(line)
    return handles


def render_chart_png(
    chart: ReportChart,
    *,
    width_in: float = 7.0,
    height_in: float = 2.6,
    dpi: int = 150,
) -> bytes:
    """Render *chart* to PNG bytes of exactly ``width_in*dpi`` x ``height_in*dpi`` pixels."""
    if not _has_any_value(chart):
        raise ValueError(f"chart '{chart.key}' has no data")

    fig = Figure(figsize=(width_in, height_in), dpi=dpi)
    fig.set_layout_engine("constrained")
    FigureCanvasAgg(fig)
    fig.patch.set_facecolor("white")

    ax = fig.add_subplot(111)
    _style_axes(ax)
    band_handles = _draw_bands(ax, chart)
    series_handles = _draw_series(ax, chart)

    ax.set_title(chart.title, fontsize=10, color=_TEXT_COLOR)
    ax.set_ylabel(chart.unit, fontsize=8, color=_TEXT_COLOR)

    handles = series_handles + band_handles
    if handles:
        ax.legend(handles=handles, loc="upper left", fontsize=7, frameon=False)

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, metadata={"Software": None})
    return buf.getvalue()
