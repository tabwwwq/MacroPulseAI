Review of your pdf.py (lead). 9 of 10 tests pass. Fix ALL points below and return the complete file.

1. FAILING TEST `test_pdf_contains_every_section_with_sources_and_caveats`:
   "Fewer than 40 observations published." is not found. It is in your table, but the narrow Note
   column wraps it over several lines and the text extraction interleaves those lines with the
   neighbouring cells. Layout change (also easier to read): in the **estimates** and **forecasts**
   tables remove the "Notes"/"Note" column; when a row has notes (estimates: `track_record` and
   `note`; forecasts: `note`), add an extra row directly below it whose single cell spans all
   columns (`("SPAN", (0, r), (-1, r))` in the TableStyle), 7.5 pt grey text. Recompute column widths
   so they still sum to 174 mm. Keep the KPI table's Note column as it is.
2. THREAD SAFETY (blocking): the module-level `content_ref` and `global content_ref` are shared
   between concurrent requests (the API renders reports in a thread pool), so two reports could get
   each other's header/footer. Remove them. Build the header and footer strings inside `render_pdf`
   and pass them to the canvas:
   `doc.build(story, canvasmaker=functools.partial(NumberedCanvas, header=header, footer=footer))`
   with `def __init__(self, *args: Any, header: str, footer: str, **kwargs: Any) -> None`.
3. Fonts: replace the `_fonts_registered` global with `@functools.cache` on `_register_fonts()`.
   Move every import to the top of the module (no imports inside functions).
4. ruff (line length 100, rules include PL, N, RUF) currently reports:
   - F401 unused `datetime.datetime`, `reportlab.lib.enums.TA_LEFT`, local `ReportChart` import
   - F841 unused local `base` in `_build_styles` (use `getSampleStyleSheet()` copies as the brief says,
     or drop the variable)
   - RUF100 an unused `# noqa: N802` (keep `noqa` only where ruff really reports N802)
   - PLW0603 `global` statements (points 2 and 3)
   - PLC0415 imports inside functions (point 3)
   - PLR0912 / PLR0915 `render_pdf` is too long: move the story assembly into small section helpers
     (e.g. `_story(content, styles) -> list[Flowable]` calling one helper per section).
5. mypy --strict (reportlab has no type stubs; it is configured as untyped `Any`):
   - `class NumberedCanvas(canvas.Canvas):  # type: ignore[misc]`
   - annotate `*args: Any, **kwargs: Any`; `self._saved_page_states: list[dict[str, Any]] = []`
   - every bare `list` return/variable must have type arguments: use `list[Flowable]`
     (`from reportlab.platypus import Flowable`) for story fragments.
6. Keep everything that works: fonts DejaVuSans for all text (the header/footer "·" renders
   correctly), escaping, metadata, two-pass page numbers, "Not available for this selection.",
   "No data for this chart.", sources list, disclaimer box, formats of all numbers.
