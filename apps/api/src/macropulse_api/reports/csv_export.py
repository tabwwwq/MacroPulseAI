"""CSV export of report chart data.

Lays out the chart points of a :class:`ReportContent` as RFC 4180 CSV text.
The renderer never fetches, computes or invents numbers; it only formats what
the content already holds.  ``None`` values stay empty (never zero).
"""

from __future__ import annotations

import csv
import io

from macropulse_api.reports.content import ReportContent

CSV_HEADER: tuple[str, ...] = (
    "chart",
    "series",
    "unit",
    "period",
    "value",
    "source",
    "source_url",
    "retrieved_at",
    "report_as_of",
    "generated_at",
)


def _format_value(value: float | None) -> str:
    """Render a point value: empty string when missing, otherwise ``.10g``."""
    if value is None:
        return ""
    return format(value, ".10g")


def content_to_csv(content: ReportContent) -> str:
    """Return the chart data of *content* as CSV text.

    The first row is :data:`CSV_HEADER`.  Then one row per point, for every
    chart in order, every series in order, every point in order.  Fields that
    are ``None`` (or whose citation is absent) are written as empty strings.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(CSV_HEADER)

    as_of = content.as_of or "latest"
    generated_at = content.generated_at.isoformat()

    for chart in content.charts:
        citation = chart.citation
        for series in chart.series:
            for period, value in series.points:
                writer.writerow(
                    (
                        chart.title,
                        series.name,
                        series.unit,
                        period,
                        _format_value(value),
                        citation.label if citation is not None else "",
                        citation.url if citation is not None and citation.url is not None else "",
                        (
                            citation.retrieved_at
                            if citation is not None and citation.retrieved_at is not None
                            else ""
                        ),
                        as_of,
                        generated_at,
                    )
                )

    return buffer.getvalue()
