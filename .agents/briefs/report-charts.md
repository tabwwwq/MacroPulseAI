Task: write the chart renderer for PDF reports.

## Files
- CREATE `apps/api/src/macropulse_api/reports/charts.py` — the only file you may create or edit.
- CONTEXT (provided below, do not change): `apps/api/src/macropulse_api/reports/content.py` (the data classes),
  `apps/api/tests/test_report_render.py` (the four chart tests are the specification),
  `packages/economics/src/macropulse_economics/periods.py` (use its `period_start`).

## Function
```python
def render_chart_png(chart: ReportChart, *, width_in: float = 7.0, height_in: float = 2.6, dpi: int = 150) -> bytes:
```
Returns PNG bytes of exactly `width_in*dpi` x `height_in*dpi` pixels.

## Requirements
1. Use `matplotlib.figure.Figure` with `matplotlib.backends.backend_agg.FigureCanvasAgg`. Do NOT import `matplotlib.pyplot` (no global state; the API is multi-threaded).
2. Print-friendly light theme: white background, text and axes `#1f2937`, horizontal grid `#e5e7eb`.
   Series colours in order: `#1d4ed8`, `#b45309`, `#047857`, `#7c3aed` (cycle if more).
3. X positions: `datetime.combine(period_start(period), time())` for every point (works for "2026-Q3", "2026-10" and "2026-09-16").
4. Missing values (`None`) are gaps: use `float("nan")` for lines; skip them for bars. Never interpolate or fill.
5. Series styles: `"line"` solid; `"dashed"` linestyle `"--"`; `"step"` `drawstyle="steps-post"`; `"bar"` `ax.bar(...)` with width 60 days for quarterly periods, 20 days for monthly, 3 days otherwise.
6. Bands (`chart.bands`): `ax.axvspan(start, end_of_end_period, color="#9ca3af", alpha=0.25, label=band.label)` where the end is the start of the period after `band.end` (use `period_start(shift(band.end, 1))`; import `shift` from the same module). Add each distinct band label to the legend only once.
7. Title `chart.title` (fontsize 10), y-axis label `chart.unit` (fontsize 8), tick labels fontsize 7, legend fontsize 7, upper left, no frame. Dates: `AutoDateLocator` + `ConciseDateFormatter`.
8. If no series has any non-`None` value: `raise ValueError(f"chart '{chart.key}' has no data")`.
9. Exact size and determinism: `Figure(figsize=(width_in, height_in), dpi=dpi)`, use `fig.set_layout_engine("constrained")` (not `bbox_inches="tight"`, which changes the size), and save with
   `fig.savefig(buf, format="png", dpi=dpi, metadata={"Software": None})` so two calls give identical bytes.
10. Full type hints, module docstring, ruff-clean with line length 100, no unused imports.

## Out of scope
Do not edit tests, `content.py` or any other file. The lead runs the tests and sends you any failures.
