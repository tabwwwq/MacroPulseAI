"""PDF renderer for MacroPulse country reports.

Turns a fully computed :class:`~macropulse_api.reports.content.ReportContent` into a
self-contained A4 PDF (reportlab platypus). Layout only: nothing here fetches, computes
or invents numbers; ``None`` is printed as ``N/A``.
"""

from __future__ import annotations

import functools
import io
from pathlib import Path
from typing import Any
from xml.sax.saxutils import escape

import matplotlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    Flowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from macropulse_api.reports.charts import render_chart_png
from macropulse_api.reports.content import ReportContent

# --- constants ---------------------------------------------------------------------------------

_FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
_FONT_REGULAR = "DejaVuSans"
_FONT_BOLD = "DejaVuSans-Bold"

_MARGIN = 18 * mm
_FRAME_WIDTH = A4[0] - 2 * _MARGIN  # 174 mm on A4

_GREY = colors.HexColor("#6b7280")
_GRID = colors.HexColor("#d1d5db")
_HEADER_BG = colors.HexColor("#f3f4f6")
_BOX_BG = colors.HexColor("#f3f4f6")

_CHART_WIDTH = 174 * mm
_CHART_HEIGHT = 174 * 2.6 / 7 * mm


# --- fonts -------------------------------------------------------------------------------------


@functools.cache
def _register_fonts() -> None:
    """Register the bundled DejaVu TrueType fonts once (module-level guard)."""
    pdfmetrics.registerFont(TTFont(_FONT_REGULAR, str(_FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(_FONT_DIR / "DejaVuSans-Bold.ttf")))


# --- styles ------------------------------------------------------------------------------------


def _build_styles() -> dict[str, ParagraphStyle]:
    """Build the report styles from sample-sheet copies with the DejaVu fonts applied."""
    styles: dict[str, ParagraphStyle] = {}

    def _make(
        name: str,
        size: float,
        bold: bool,
        leading: float | None = None,
        *,
        left_indent: float = 0,
        bullet_indent: float = 0,
    ) -> ParagraphStyle:
        font = _FONT_BOLD if bold else _FONT_REGULAR
        return ParagraphStyle(
            name,
            fontName=font,
            fontSize=size,
            leading=leading if leading is not None else size * 1.3,
            textColor=colors.black,
            leftIndent=left_indent,
            bulletIndent=bullet_indent,
            keepWithNext=bold and size >= 11,  # headings never end a page alone
        )

    styles["title"] = _make("mp-title", 18, True, 22)
    styles["h1"] = _make("mp-h1", 15, True, 19)
    styles["h2"] = _make("mp-h2", 12.5, True, 16)
    styles["h3"] = _make("mp-h3", 11, True, 14)
    styles["body"] = _make("mp-body", 10, False, 13)
    styles["bullet"] = _make("mp-bullet", 10, False, 13, left_indent=10, bullet_indent=0)
    styles["cell"] = _make("mp-cell", 8, False, 10)
    styles["cell_bold"] = _make("mp-cell-bold", 8, True, 10)
    styles["caption"] = _make("mp-caption", 7, False, 9)
    styles["note"] = _make("mp-note", 8, False, 10)
    styles["disclaimer"] = _make("mp-disclaimer", 8, False, 10)
    styles["header"] = _make("mp-header", 8, False, 10)
    styles["footer"] = _make("mp-footer", 7, False, 9)
    styles["note_row"] = _make("mp-note-row", 7.5, False, 9)
    return styles


_STYLES = _build_styles()


# --- helpers -----------------------------------------------------------------------------------


def _esc(text: str) -> str:
    """Escape text from content before it is placed in a Paragraph."""
    return escape(text)


def _fmt(value: float | None, unit: str) -> str:
    return "N/A" if value is None else f"{value:.2f} {unit}"


def _fmt_change(value: float | None) -> str:
    return "N/A" if value is None else f"{value:+.2f}"


def _fmt_prob(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.1f} %"


def _fmt_pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.0f} %"


def _fmt_num(value: float | None) -> str:
    return "N/A" if value is None else f"{value:.2f}"


def _cell(text: str, bold: bool = False) -> Paragraph:
    style = _STYLES["cell_bold"] if bold else _STYLES["cell"]
    return Paragraph(_esc(text), style)


def _note_row_cell(text: str) -> Paragraph:
    return Paragraph(_esc(text), _STYLES["note_row"])


def _check_widths(col_widths: list[float]) -> None:
    """Ensure column widths sum to the frame width (guards against margin overflow)."""
    total = sum(col_widths)
    if abs(total - _FRAME_WIDTH) > 0.5:
        raise ValueError(f"column widths sum to {total:.1f}, expected {_FRAME_WIDTH:.1f}")


def _make_table(
    header: list[str],
    rows: list[list[str]],
    col_widths: list[float],
    notes: list[str | None] | None = None,
) -> Table:
    """Table with one Paragraph per cell; a non-empty `notes[i]` becomes a full-width row
    directly below data row `i` (long notes wrap there instead of in a narrow column)."""
    _check_widths(col_widths)
    data: list[list[Paragraph]] = [[_cell(h, bold=True) for h in header]]
    style_cmds: list[tuple[Any, ...]] = [
        ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
        ("GRID", (0, 0), (-1, -1), 0.5, _GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]
    for i, row in enumerate(rows):
        if len(row) != len(header):
            raise ValueError(f"table row has {len(row)} cells for {len(header)} columns")
        data.append([_cell(c) for c in row])
        note = notes[i] if notes else None
        if note:
            data.append([_note_row_cell(note)] + [_cell("")] * (len(header) - 1))
            r = len(data) - 1
            style_cmds.append(("SPAN", (0, r), (-1, r)))
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle(style_cmds))
    return table


def _bullet(text: str) -> Paragraph:
    return Paragraph(_esc(text), _STYLES["bullet"], bulletText="\u2022")


def _not_available() -> Paragraph:
    return Paragraph("Not available for this selection.", _STYLES["body"])


# --- canvas with header/footer (two-pass numbering) --------------------------------------------


class NumberedCanvas(canvas.Canvas):  # type: ignore[misc]
    """Canvas that defers footer drawing so the total page count is known."""

    def __init__(self, *args: Any, header: str, footer: str, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._saved_page_states: list[dict[str, Any]] = []
        self._header_text: str = header
        self._footer_text: str = footer

    def showPage(self) -> None:  # noqa: N802 - reportlab API
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self._draw_page_decorations(total)
            super().showPage()
        super().save()

    def _draw_page_decorations(self, total: int) -> None:
        page = self._pageNumber
        width, height = A4
        # header
        self.setFont(_FONT_REGULAR, 8)
        self.setFillColor(_GREY)
        self.drawString(_MARGIN, height - _MARGIN + 6 * mm, self._header_text)
        # footer
        self.setFont(_FONT_REGULAR, 7)
        self.setFillColor(_GREY)
        left = self._footer_text
        right = f"Page {page} of {total}"
        self.drawString(_MARGIN, _MARGIN - 6 * mm, left)
        self.drawRightString(width - _MARGIN, _MARGIN - 6 * mm, right)


# --- story builders ----------------------------------------------------------------------------


def _build_meta_table(content: ReportContent) -> Table:
    rows = [
        ("Country", f"{content.country_name} ({content.country_iso2})"),
        ("As of", content.as_of_label),
        ("Generated (UTC)", f"{content.generated_at:%Y-%m-%d %H:%M}"),
        ("App version", content.app_version),
        ("Data basis", content.data_basis),
    ]
    data = [[_cell(k, bold=True), _cell(v)] for k, v in rows]
    col_widths = [_FRAME_WIDTH * 0.28, _FRAME_WIDTH * 0.72]
    _check_widths(col_widths)
    table = Table(data, colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), _HEADER_BG),
                ("GRID", (0, 0), (-1, -1), 0.5, _GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return table


def _build_kpi_table(content: ReportContent) -> Table:
    header = ["Indicator", "Value", "Period", "Change", "Status", "Note"]
    rows: list[list[str]] = []
    for k in content.kpis:
        value = "N/A" if k.value is None else f"{k.value:.2f} {k.unit}"
        change = "N/A" if k.change is None else f"{k.change:+.2f}"
        period = "N/A" if k.period is None else k.period
        note = "" if k.note is None else k.note
        rows.append([k.label, value, period, change, k.status, note])
    widths = [
        _FRAME_WIDTH * 0.26,
        _FRAME_WIDTH * 0.16,
        _FRAME_WIDTH * 0.14,
        _FRAME_WIDTH * 0.14,
        _FRAME_WIDTH * 0.14,
        _FRAME_WIDTH * 0.16,
    ]
    return _make_table(header, rows, widths)


def _build_estimate_table(content: ReportContent) -> Table:
    header = ["Horizon", "Probability", "Band", "Model", "Version", "As of"]
    rows: list[list[str]] = []
    notes: list[str | None] = []
    for e in content.estimates:
        notes.append(" ".join(p for p in (e.track_record, e.note) if p) or None)
        row = [
            f"{e.horizon} quarters",
            _fmt_prob(e.probability),
            "N/A" if e.band is None else e.band,
            "N/A" if e.model is None else e.model,
            "N/A" if e.version is None else e.version,
            "N/A" if e.as_of is None else e.as_of,
        ]
        rows.append(row)
    widths = [
        _FRAME_WIDTH * 0.14,
        _FRAME_WIDTH * 0.16,
        _FRAME_WIDTH * 0.14,
        _FRAME_WIDTH * 0.20,
        _FRAME_WIDTH * 0.18,
        _FRAME_WIDTH * 0.18,
    ]
    return _make_table(header, rows, widths, notes=notes)


def _build_forecast_table(content: ReportContent) -> Table:
    header = [
        "Indicator",
        "Model",
        "Origin \u2192 Target",
        "Forecast",
        "80 % interval",
        "Coverage",
        "RMSE vs naive",
    ]
    rows: list[list[str]] = []
    notes: list[str | None] = []
    for f in content.forecasts:
        notes.append(f.note or None)
        origin_target = "N/A"
        if f.origin is not None or f.target is not None:
            origin_target = f"{f.origin or 'N/A'} \u2192 {f.target or 'N/A'}"
        if f.lower is not None and f.upper is not None:
            interval = f"{f.lower:.2f} to {f.upper:.2f}"
        else:
            interval = "N/A"
        forecast = "N/A" if f.value is None else f"{f.value:.2f} {f.unit}"
        row = [
            f.indicator,
            "N/A" if f.model is None else f.model,
            origin_target,
            forecast,
            interval,
            _fmt_pct(f.coverage),
            _fmt_num(f.rel_rmse),
        ]
        rows.append(row)
    widths = [
        _FRAME_WIDTH * 0.18,
        _FRAME_WIDTH * 0.16,
        _FRAME_WIDTH * 0.18,
        _FRAME_WIDTH * 0.13,
        _FRAME_WIDTH * 0.13,
        _FRAME_WIDTH * 0.11,
        _FRAME_WIDTH * 0.11,
    ]
    return _make_table(header, rows, widths, notes=notes)


def _build_chart_block(content: ReportContent, lead: Flowable | None = None) -> list[Flowable]:
    """One KeepTogether per chart; `lead` (the section heading) joins the first block so the
    heading never ends a page alone."""
    story: list[Flowable] = []
    for chart in content.charts:
        block: list[Flowable] = [Paragraph(_esc(chart.title), _STYLES["h3"])]
        if lead is not None:
            block.insert(0, lead)
            lead = None
        try:
            png = render_chart_png(chart)
            block.append(Image(io.BytesIO(png), width=_CHART_WIDTH, height=_CHART_HEIGHT))
        except ValueError:
            block.append(Paragraph("No data for this chart.", _STYLES["body"]))
        if chart.note is not None:
            block.append(Paragraph(_esc(chart.note), _STYLES["note"]))
        caption_parts: list[str] = []
        if chart.citation is not None:
            if chart.citation.label is not None:
                caption_parts.append(f"Source: {chart.citation.label}")
            if chart.citation.retrieved_at is not None:
                caption_parts.append(f"retrieved {chart.citation.retrieved_at}")
        if caption_parts:
            block.append(Paragraph(_esc(" \u00b7 ".join(caption_parts)), _STYLES["caption"]))
        block.append(Spacer(1, 4 * mm))
        story.append(KeepTogether(block))
    return story


def _build_sources(content: ReportContent) -> list[Flowable]:
    story: list[Flowable] = []
    for i, c in enumerate(content.citations, start=1):
        lines = [f"{i}. {_esc(c.label)}"]
        if c.url is not None:
            lines.append(f"URL: {_esc(c.url)}")
        if c.retrieved_at is not None:
            lines.append(f"Retrieved: {_esc(c.retrieved_at)}")
        if c.source_updated_at is not None:
            lines.append(f"Source updated: {_esc(c.source_updated_at)}")
        story.append(Paragraph("<br/>".join(lines), _STYLES["body"]))
    return story


def _build_disclaimer(content: ReportContent) -> Table:
    cell = Paragraph(_esc(content.disclaimer), _STYLES["disclaimer"])
    col_widths = [_FRAME_WIDTH]
    _check_widths(col_widths)
    table = Table([[cell]], colWidths=col_widths)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), _BOX_BG),
                ("BOX", (0, 0), (-1, -1), 0.5, _GRID),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return table


# --- section helpers for story assembly --------------------------------------------------------


def _section_title(text: str) -> Paragraph:
    return Paragraph(_esc(text), _STYLES["h2"])


def _section_warnings(content: ReportContent) -> list[Flowable]:
    story: list[Flowable] = []
    if content.warnings:
        story.append(_section_title("Warnings"))
        for w in content.warnings:
            story.append(_bullet(w))
        story.append(Spacer(1, 4 * mm))
    return story


def _section_summary(content: ReportContent) -> list[Flowable]:
    story: list[Flowable] = [_section_title("Summary")]
    for sentence in content.summary:
        story.append(_bullet(sentence))
    story.append(Spacer(1, 4 * mm))
    return story


def _section_kpis(content: ReportContent) -> list[Flowable]:
    story: list[Flowable] = [_section_title("Key indicators")]
    if content.kpis:
        story.append(_build_kpi_table(content))
    else:
        story.append(_not_available())
    story.append(Spacer(1, 6 * mm))
    return story


def _section_charts(content: ReportContent) -> list[Flowable]:
    if content.charts:
        story: list[Flowable] = _build_chart_block(content, lead=_section_title("Charts"))
    else:
        story = [_section_title("Charts"), _not_available()]
    story.append(Spacer(1, 4 * mm))
    return story


def _section_estimates(content: ReportContent) -> list[Flowable]:
    story: list[Flowable] = [
        _section_title("Recession risk (technical recession, model estimates)")
    ]
    if content.estimates:
        story.append(_build_estimate_table(content))
    else:
        story.append(_not_available())
    story.append(Spacer(1, 6 * mm))
    return story


def _section_forecasts(content: ReportContent) -> list[Flowable]:
    story: list[Flowable] = [_section_title("Indicator forecasts")]
    if content.forecasts:
        story.append(_build_forecast_table(content))
    else:
        story.append(_not_available())
    story.append(Spacer(1, 6 * mm))
    return story


def _section_methodology(content: ReportContent) -> list[Flowable]:
    story: list[Flowable] = [_section_title("Methodology")]
    for item in content.methodology:
        story.append(_bullet(item))
    story.append(Spacer(1, 4 * mm))
    story.append(_section_title("Limitations"))
    for item in content.limitations:
        story.append(_bullet(item))
    story.append(Spacer(1, 6 * mm))
    return story


def _section_sources(content: ReportContent) -> list[Flowable]:
    story: list[Flowable] = [_section_title("Sources")]
    if content.citations:
        story.extend(_build_sources(content))
    else:
        story.append(_not_available())
    story.append(Spacer(1, 6 * mm))
    return story


def _section_disclaimer(content: ReportContent) -> list[Flowable]:
    return [_build_disclaimer(content)]


def _story(content: ReportContent) -> list[Flowable]:
    """Assemble the full story for the report."""
    story: list[Flowable] = []
    story.append(Paragraph(_esc(content.title), _STYLES["title"]))
    story.append(Spacer(1, 4 * mm))
    story.append(_build_meta_table(content))
    story.append(Spacer(1, 6 * mm))
    story.extend(_section_warnings(content))
    story.extend(_section_summary(content))
    story.extend(_section_kpis(content))
    story.extend(_section_charts(content))
    story.extend(_section_estimates(content))
    story.extend(_section_forecasts(content))
    story.extend(_section_methodology(content))
    story.extend(_section_sources(content))
    story.extend(_section_disclaimer(content))
    return story


# --- public API --------------------------------------------------------------------------------


def render_pdf(content: ReportContent) -> bytes:
    """Render *content* to a self-contained A4 PDF and return the bytes."""
    _register_fonts()

    header = f"MacroPulse AI \u00b7 {content.country_name} \u00b7 {content.as_of_label}"
    footer = (
        f"Generated {content.generated_at:%Y-%m-%d %H:%M} UTC \u00b7 "
        "analytical estimates, not investment advice"
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=_MARGIN,
        rightMargin=_MARGIN,
        topMargin=_MARGIN,
        bottomMargin=_MARGIN,
        title=content.title,
        author="MacroPulse AI",
        subject="Country macro report",
        creator=f"MacroPulse AI {content.app_version}",
    )

    story = _story(content)
    doc.build(story, canvasmaker=functools.partial(NumberedCanvas, header=header, footer=footer))
    return buf.getvalue()
