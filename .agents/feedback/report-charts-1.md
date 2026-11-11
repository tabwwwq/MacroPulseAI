Review of your charts.py (lead). Fix ALL points and return the complete file.

1. BUG (blocking): you place points at integer positions (`x_index[p]`), not dates. Requirement 3
   says dates. Bands are drawn at dates while series are at 0..N, so they do not line up, bars of
   width 60 overlap, and the date locator labels nonsense. Use matplotlib date numbers everywhere:
   `x = mdates.date2num(datetime.combine(period_start(p), time()))` for series points, bar positions
   and band edges. Remove `x_index`, `all_periods` and the unused `x_dates`.
2. BUG (blocking): `FigureCanvasAgg` has no `close()`; `canvas.close()` raises AttributeError on
   every call. Do not call it. Keep `FigureCanvasAgg(fig)` so the figure has an Agg canvas.
3. Legend handle for bands: use `matplotlib.patches.Patch(facecolor="#9ca3af", alpha=0.25, label=...)`.
4. ruff (line length 100, rules include PL): currently
   - F401 unused imports `typing.Any`, `matplotlib.font_manager`, `numpy`; F841 unused `x_dates`
   - PLR0912 too many branches / PLR0915 too many statements in `render_chart_png`.
   Split the work into small helpers, e.g. `_style_axes(ax)`, `_draw_bands(ax, chart) -> list[Patch]`,
   `_draw_series(ax, chart) -> list[Artist]`, `_x(period) -> float`.
5. mypy --strict currently reports:
   - `axvspan` arguments are `float` (pass the `date2num` values, not `datetime`)
   - `Call to untyped function "AutoDateLocator"` / `"ConciseDateFormatter"`: keep the calls and add
     `# type: ignore[no-untyped-call]` on exactly those two lines.
   - `"FigureCanvasAgg" has no attribute "close"` (see point 2).
6. Keep everything else from the brief: Figure + FigureCanvasAgg (no pyplot), constrained layout,
   exact size, `savefig(..., metadata={"Software": None})`, `ValueError(f"chart '{chart.key}' has no data")`,
   NaN gaps for lines, skipped `None` for bars, styles line/dashed/step/bar, colours as specified.
