---
type: codex-run
name: local-report-pdf
date: 2026-11-11
time: "11:16"
status: success
exit_code: 0
sandbox: local-single-file
network: false
tags:
  - agent/codex
---

# ✅ Codex · local-report-pdf

Delegated by Claude Code via `scripts/agents/codex-task.ps1` on 2026-11-11 11:16. Sandbox `local-single-file`, network off, exit code 0.
See [[Agent workflow]] for how delegation and review work.

> [!summary] Codex report
> ```py
> """PDF renderer for MacroPulse country reports.
>
> Turns a fully computed :class:`~macropulse_api.reports.content.ReportContent` into a
> self-contained A4 PDF (reportlab platypus). Layout only: nothing here fetches, computes
> or invents numbers; ``None`` is printed as ``N/A``.
> """
>
> from __future__ import annotations
>
> import functools
> import io
> from pathlib import Path
> from typing import Any
> from xml.sax.saxutils import escape
>
> import matplotlib
> from reportlab.lib import colors
> from reportlab.lib.pagesizes import A4
> from reportlab.lib.styles import ParagraphStyle
> from reportlab.lib.units import mm
> from reportlab.pdfbase import pdfmetrics
> from reportlab.pdfbase.ttfonts import TTFont
> from reportlab.pdfgen import canvas
> from reportlab.platypus import (
>     Flowable,
>     Image,
>     KeepTogether,
>     Paragraph,
>     SimpleDocTemplate,
>     Spacer,
>     Table,
>     TableStyle,
> )
>
> from macropulse_api.reports.charts import render_chart_png
> from macropulse_api.reports.content import ReportContent
>
> # --- constants ---------------------------------------------------------------------------------
>
> _FONT_DIR = Path(matplotlib.get_data_path()) / "fonts" / "ttf"
> _FONT_REGULAR = "DejaVuSans"
> _FONT_BOLD = "DejaVuSans-Bold"
>
> _MARGIN = 18 * mm
> _FRAME_WIDTH = A4[0] - 2 * _MARGIN  # 174 mm on A4
>
> _GREY = colors.HexColor("#6b7280")
> _GRID = colors.HexColor("#d1d5db")
> _HEADER_BG = colors.HexColor("#f3f4f6")
> _BOX_BG = colors.HexColor("#f3f4f6")
>
> _CHART_WIDTH = 174 * mm
> _CHART_HEIGHT = 174 * 2.6 / 7 * mm
>
>
> # --- fonts -------------------------------------------------------------------------------------
>
>
> @functools.cache
> def _register_fonts() -> None:
>     """Register the bundled DejaVu TrueType fonts once (module-level guard)."""
>     pdfmetrics.registerFont(TTFont(_FONT_REGULAR, str(_FONT_DIR / "DejaVuSans.ttf")))
>     pdfmetrics.registerFont(TTFont(_FONT_BOLD, str(_FONT_DIR / "DejaVuSans-Bold.ttf")))
>
>
> # --- styles ------------------------------------------------------------------------------------
>
>
> def _build_styles() -> dict[str, ParagraphStyle]:
>     """Build the report styles from sample-sheet copies with the DejaVu fonts applied."""
>     styles: dict[str, ParagraphStyle] = {}
>
>     def _make(
>         name: str,
>         size: float,
>         bold: bool,
>         leading: float | None = None,
>         left_indent: float = 0,
>         bullet_indent: float = 0,
>     ) -> ParagraphStyle:
>         font = _FONT_BOLD if bold else _FONT_REGULAR
>         return ParagraphStyle(
>             name,
>             fontName=font,
>             fontSize=size,
>             leading=leading if leading is not None else size * 1.3,
>             textColor=colors.black,
>             leftIndent=left_indent,
>             bulletIndent=bullet_indent,
>         )
>
>     styles["title"] = _make("mp-title", 18, True, 22)
>     styles["h1"] = _make("mp-h1", 15, True, 19)
>     styles["h2"] = _make("mp-h2", 12.5, True, 16)
>     styles["h3"] = _make("mp-h3", 11, True, 14)
>     styles["body"] = _make("mp-body", 10, False, 13)
>     styles["bullet"] = _make("mp-bullet", 10, False, 13, left_indent=10, bullet_indent=0)
>     styles["cell"] = _make("mp-cell", 8, False, 10)
>     styles["cell_bold"] = _make("mp-cell-bold", 8, True, 10)
>     styles["caption"] = _make("mp-caption", 7, False, 9)
>     styles["note"] = _make("mp-note", 8, False, 10)
>     styles["disclaimer"] = _make("mp-disclaimer", 8, False, 10)
>     styles["header"] = _make("mp-header", 8, False, 10)
>     styles["footer"] = _make("mp-footer", 7, False, 9)
>     styles["note_row"] = _make("mp-note-row", 7.5, False, 9)
>     return styles
>
>
> _STYLES = _build_styles()
>
>
> # --- helpers -----------------------------------------------------------------------------------
>
>
> def _esc(text: str) -> str:
>     """Escape text from content before it is placed in a Paragraph."""
>     return escape(text)
>
>
> def _fmt(value: float | None, unit: str) -> str:
>     return "N/A" if value is None else f"{value:.2f} {unit}"
>
>
> def _fmt_change(value: float | None) -> str:
>     return "N/A" if value is None else f"{value:+.2f}"
>
>
> def _fmt_prob(value: float | None) -> str:
>     return "N/A" if value is None else f"{value * 100:.1f} %"
>
>
> def _fmt_pct(value: float | None) -> str:
>     return "N/A" if value is None else f"{value * 100:.0f} %"
>
>
> def _fmt_num(value: float | None) -> str:
>     return "N/A" if value is None else f"{value:.2f}"
>
>
> def _cell(text: str, bold: bool = False) -> Paragraph:
>     style = _STYLES["cell_bold"] if bold else _STYLES["cell"]
>     return Paragraph(_esc(text), style)
>
>
> def _note_row_cell(text: str) -> Paragraph:
>     return Paragraph(_esc(text), _STYLES["note_row"])
>
>
> def _check_widths(col_widths: list[float]) -> None:
>     """Ensure column widths sum to the frame width (guards against margin overflow)."""
>     total = sum(col_widths)
>     if abs(total - _FRAME_WIDTH) > 0.5:
>         raise ValueError(f"column widths sum to {total:.1f}, expected {_FRAME_WIDTH:.1f}")
>
>
> def _make_table(
>     header: list[str],
>     rows: list[list[str]],
>     col_widths: list[float],
>     notes: list[str | None] | None = None,
> ) -> Table:
>     """Table with one Paragraph per cell; a non-empty `notes[i]` becomes a full-width row
>     directly below data row `i` (long notes wrap there instead of in a narrow column)."""
>     _check_widths(col_widths)
>     data: list[list[Paragraph]] = [[_cell(h, bold=True) for h in header]]
>     style_cmds: list[tuple[Any, ...]] = [
>         ("BACKGROUND", (0, 0), (-1, 0), _HEADER_BG),
>         ("GRID", (0, 0), (-1, -1), 0.5, _GRID),
>         ("VALIGN", (0, 0), (-1, -1), "TOP"),
>         ("LEFTPADDING", (0, 0), (-1, -1), 4),
>         ("RIGHTPADDING", (0, 0), (-1, -1), 4),
>         ("TOPPADDING", (0, 0), (-1, -1), 3),
>         ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
>     ]
>     for i, row in enumerate(rows):
>         if len(row) != len(header):
>             raise ValueError(f"table row has {len(row)} cells for {len(header)} columns")
>         data.append([_cell(c) for c in row])
>         note = notes[i] if notes else None
>         if note:
>             data.a
> …(truncated)

> [!quote]- Brief sent to Codex
> # Brief
>
> Task: write the PDF renderer for country reports (reportlab).
>
> ## Files
> - CREATE `apps/api/src/macropulse_api/reports/pdf.py` — the only file you may create or edit.
> - CONTEXT (provided below, do not change): `apps/api/src/macropulse_api/reports/content.py` (data classes),
>   `apps/api/src/macropulse_api/reports/charts.py` (use `render_chart_png`),
>   `apps/api/tests/test_report_render.py` (the PDF tests are the specification),
>   `apps/api/tests/report_fixture.py` (sample content).
>
> ## API
> ```python
> def render_pdf(content: ReportContent) -> bytes:
> ```
>
> ## Requirements
> 1. reportlab platypus `SimpleDocTemplate` into an `io.BytesIO`, page size A4, all margins 18 mm.
>    Document metadata: `title=content.title`, `author="MacroPulse AI"`, `subject="Country macro report"`,
>    `creator=f"MacroPulse AI {content.app_version}"`.
> 2. Fonts: register TrueType fonts once (module-level guard) from matplotlib's bundled files:
>    `Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"` as `"DejaVuSans"` and
>    `"DejaVuSans-Bold.ttf"` as `"DejaVuSans-Bold"`. Use them in every style (Helvetica cannot print
>    "−", "≥" or "·"). Build styles from `getSampleStyleSheet()` copies with `fontName` changed.
> 3. Escape all text from `content` with `xml.sax.saxutils.escape` before putting it in a `Paragraph`.
> 4. Every page: header (8 pt, grey `#6b7280`) `MacroPulse AI · {country_name} · {as_of_label}`; footer
>    (7 pt) left `Generated {generated_at:%Y-%m-%d %H:%M} UTC · analytical estimates, not investment advice`,
>    right `Page {n} of {total}`. Use the two-pass "NumberedCanvas" pattern (a `Canvas` subclass that
>    stores page states in `showPage` and draws the footer for all pages in `save`), passed to
>    `doc.build(story, canvasmaker=...)`.
> 5. Story, in this order (headings: `Heading1` for the title, `Heading2` for sections, 10 pt body text):
>    1. Title `content.title`, then a 2-column key/value table: Country (`country_name (country_iso2)`),
>       As of (`as_of_label`), Generated (UTC), App version, Data basis.
>    2. If `content.warnings`: section "Warnings" with one bullet per warning.
>    3. "Summary": one bullet per sentence of `content.summary`.
>    4. "Key indicators": table columns Indicator | Value | Period | Change | Status | Note.
>       Value: `"N/A"` when `None`, else `f"{value:.2f} {unit}"`. Change: `"N/A"` when `None`, else `f"{change:+.2f}"`.
>       Period / Note: `"N/A"` / `""` when `None`.
>    5. "Charts": for each chart, a `Heading3` with its title, then `Image(BytesIO(render_chart_png(chart)))`
>       174 mm wide and 174*2.6/7 mm high, then the note (if any) and a 7 pt caption
>       `Source: {label} · retrieved {retrieved_at}` (skip parts that are `None`). If `render_chart_png`
>       raises `ValueError`, write "No data for this chart." instead of the image.
>    6. "Recession risk (technical recession, model estimates)": table Horizon | Probability | Band |
>       Model | Version | As of | Notes. Horizon `f"{h} quarters"`. Probability `"N/A"` when `None`, else
>       `f"{p * 100:.1f} %"`. Notes: `track_record` and `note` joined with a space (skip `None`).
>    7. "Indicator forecasts": table Indicator | Model | Origin → Target | Forecast | 80 % interval |
>       Coverage | RMSE vs naive | Note. Forecast `"N/A"` or `f"{value:.2f} {unit}"`; interval
>       `f"{lower:.2f} to {upper:.2f}"` or `"N/A"`; coverage `f"{coverage * 100:.0f} %"` or `"N/A"`;
>       RMSE vs naive `f"{rel_rmse:.2f}"` or `"N/A"`.
>    8. "Methodology" and "Limitations": one bullet per item.
>    9. "Sources": numbered list; each item `label`, then on new lines `URL: …`, `Retrieved: …`,
>       `Source updated: …` (only the parts that are not `None`).
>    10. The disclaimer in a light grey box (a one-cell `Table` with background `#f3f4f6`).
>    For an empty `charts`, `estimates` or `forecasts` tuple, write the paragraph
>    "Not available for this selection." under that section's heading instead of a table.
> 6. Tables: every cell is a `Paragraph` (so text wraps), font size 8, header row bold on `#f3f4f6`,
>    grid lines `#d1d5db` 0.5 pt, column widths summing to the frame width (174 mm), `repeatRows=1`.
> 7. Return the PDF bytes. Full type hints, module docstring, ruff-clean (line length 100).
>
> ## Out of scope
> Do not edit tests, `content.py`, `charts.py` or any other file. The lead runs the tests and will send you the failures.
>
> # Output file
>
> `apps/api/src/macropulse_api/reports/pdf.py`
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
> class R
> …(truncated)
