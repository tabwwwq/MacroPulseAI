Task: write the PDF renderer for country reports (reportlab).

## Files
- CREATE `apps/api/src/macropulse_api/reports/pdf.py` — the only file you may create or edit.
- CONTEXT (provided below, do not change): `apps/api/src/macropulse_api/reports/content.py` (data classes),
  `apps/api/src/macropulse_api/reports/charts.py` (use `render_chart_png`),
  `apps/api/tests/test_report_render.py` (the PDF tests are the specification),
  `apps/api/tests/report_fixture.py` (sample content).

## API
```python
def render_pdf(content: ReportContent) -> bytes:
```

## Requirements
1. reportlab platypus `SimpleDocTemplate` into an `io.BytesIO`, page size A4, all margins 18 mm.
   Document metadata: `title=content.title`, `author="MacroPulse AI"`, `subject="Country macro report"`,
   `creator=f"MacroPulse AI {content.app_version}"`.
2. Fonts: register TrueType fonts once (module-level guard) from matplotlib's bundled files:
   `Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"` as `"DejaVuSans"` and
   `"DejaVuSans-Bold.ttf"` as `"DejaVuSans-Bold"`. Use them in every style (Helvetica cannot print
   "−", "≥" or "·"). Build styles from `getSampleStyleSheet()` copies with `fontName` changed.
3. Escape all text from `content` with `xml.sax.saxutils.escape` before putting it in a `Paragraph`.
4. Every page: header (8 pt, grey `#6b7280`) `MacroPulse AI · {country_name} · {as_of_label}`; footer
   (7 pt) left `Generated {generated_at:%Y-%m-%d %H:%M} UTC · analytical estimates, not investment advice`,
   right `Page {n} of {total}`. Use the two-pass "NumberedCanvas" pattern (a `Canvas` subclass that
   stores page states in `showPage` and draws the footer for all pages in `save`), passed to
   `doc.build(story, canvasmaker=...)`.
5. Story, in this order (headings: `Heading1` for the title, `Heading2` for sections, 10 pt body text):
   1. Title `content.title`, then a 2-column key/value table: Country (`country_name (country_iso2)`),
      As of (`as_of_label`), Generated (UTC), App version, Data basis.
   2. If `content.warnings`: section "Warnings" with one bullet per warning.
   3. "Summary": one bullet per sentence of `content.summary`.
   4. "Key indicators": table columns Indicator | Value | Period | Change | Status | Note.
      Value: `"N/A"` when `None`, else `f"{value:.2f} {unit}"`. Change: `"N/A"` when `None`, else `f"{change:+.2f}"`.
      Period / Note: `"N/A"` / `""` when `None`.
   5. "Charts": for each chart, a `Heading3` with its title, then `Image(BytesIO(render_chart_png(chart)))`
      174 mm wide and 174*2.6/7 mm high, then the note (if any) and a 7 pt caption
      `Source: {label} · retrieved {retrieved_at}` (skip parts that are `None`). If `render_chart_png`
      raises `ValueError`, write "No data for this chart." instead of the image.
   6. "Recession risk (technical recession, model estimates)": table Horizon | Probability | Band |
      Model | Version | As of | Notes. Horizon `f"{h} quarters"`. Probability `"N/A"` when `None`, else
      `f"{p * 100:.1f} %"`. Notes: `track_record` and `note` joined with a space (skip `None`).
   7. "Indicator forecasts": table Indicator | Model | Origin → Target | Forecast | 80 % interval |
      Coverage | RMSE vs naive | Note. Forecast `"N/A"` or `f"{value:.2f} {unit}"`; interval
      `f"{lower:.2f} to {upper:.2f}"` or `"N/A"`; coverage `f"{coverage * 100:.0f} %"` or `"N/A"`;
      RMSE vs naive `f"{rel_rmse:.2f}"` or `"N/A"`.
   8. "Methodology" and "Limitations": one bullet per item.
   9. "Sources": numbered list; each item `label`, then on new lines `URL: …`, `Retrieved: …`,
      `Source updated: …` (only the parts that are not `None`).
   10. The disclaimer in a light grey box (a one-cell `Table` with background `#f3f4f6`).
   For an empty `charts`, `estimates` or `forecasts` tuple, write the paragraph
   "Not available for this selection." under that section's heading instead of a table.
6. Tables: every cell is a `Paragraph` (so text wraps), font size 8, header row bold on `#f3f4f6`,
   grid lines `#d1d5db` 0.5 pt, column widths summing to the frame width (174 mm), `repeatRows=1`.
7. Return the PDF bytes. Full type hints, module docstring, ruff-clean (line length 100).

## Out of scope
Do not edit tests, `content.py`, `charts.py` or any other file. The lead runs the tests and will send you the failures.
