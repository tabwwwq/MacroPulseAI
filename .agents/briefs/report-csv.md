Task: write the CSV export of report chart data.

## Files
- CREATE `apps/api/src/macropulse_api/reports/csv_export.py` — the only file you may create or edit.
- CONTEXT (provided below, do not change): `apps/api/src/macropulse_api/reports/content.py`,
  `apps/api/tests/test_report_render.py` (the two CSV tests are the specification),
  `apps/api/tests/report_fixture.py`.

## API
```python
CSV_HEADER: tuple[str, ...] = (
    "chart", "series", "unit", "period", "value",
    "source", "source_url", "retrieved_at", "report_as_of", "generated_at",
)

def content_to_csv(content: ReportContent) -> str:
```

## Requirements
1. Use the standard `csv` module (`csv.writer` on an `io.StringIO`, `lineterminator="\r\n"`), so fields
   with commas or quotes are quoted correctly (RFC 4180).
2. First row: `CSV_HEADER`. Then one row per point, for every chart in order, every series in order,
   every point in order:
   `chart.title, series.name, series.unit, period, value, citation.label, citation.url, citation.retrieved_at, content.as_of or "latest", content.generated_at.isoformat()`.
3. `value`: empty string when `None` (missing stays missing, never 0); otherwise `format(value, ".10g")`.
4. When `chart.citation` is `None`, or one of its fields is `None`, write an empty string.
5. No other rows (no blank lines, no footer). A report without charts returns only the header line.
6. Full type hints, module docstring, ruff-clean (line length 100).

## Out of scope
Do not edit tests or other files. The lead runs the tests and sends you any failures.
