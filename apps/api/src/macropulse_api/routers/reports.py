"""Report builder: dated PDF / CSV / JSON reports from stored data and published models."""

from __future__ import annotations

import dataclasses
import json
import logging
from datetime import datetime
from typing import Any, Literal

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel, Field

from macropulse_api.deps import SessionDep
from macropulse_api.errors import ApiError
from macropulse_api.ratelimit import compute_limit
from macropulse_api.reports.content import ReportContent
from macropulse_api.schemas import ErrorResponse
from macropulse_api.services.report_builder import build_report

router = APIRouter(prefix="/api/reports", tags=["reports"])
logger = logging.getLogger("macropulse.reports")

MEDIA = {
    "pdf": "application/pdf",
    "csv": "text/csv; charset=utf-8",
    "json": "application/json",
}


class ReportRequest(BaseModel):
    model_config = {"extra": "forbid"}

    country: str = Field(pattern=r"^[A-Za-z]{2}$")
    as_of: str | None = Field(default=None, pattern=r"^\d{4}-Q[1-4]$")
    format: Literal["pdf", "csv", "json"] = "pdf"


def filename(content: ReportContent, fmt: str) -> str:
    stamp = content.generated_at.strftime("%Y%m%d")
    iso = content.country_iso2.lower()
    return f"macropulse-report-{iso}-{content.as_of or 'latest'}-{stamp}.{fmt}"


def _jsonable(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(type(value).__name__)


def content_json(content: ReportContent) -> str:
    return json.dumps(dataclasses.asdict(content), default=_jsonable, ensure_ascii=False, indent=2)


def _render(content: ReportContent, fmt: str) -> bytes:
    if fmt == "pdf":
        from macropulse_api.reports.pdf import render_pdf  # noqa: PLC0415 - heavy import on demand

        return render_pdf(content)
    if fmt == "csv":
        from macropulse_api.reports.csv_export import content_to_csv  # noqa: PLC0415

        return content_to_csv(content).encode("utf-8")
    return content_json(content).encode("utf-8")


@router.post(
    "/generate",
    summary="Generate a dated country report (PDF, CSV of chart data, or JSON)",
    response_class=Response,
    responses={
        200: {
            "content": {m: {} for m in MEDIA.values()},
            "description": "The report file (Content-Disposition carries a descriptive filename).",
        },
        422: {"model": ErrorResponse, "description": "Unsupported country, as-of or format."},
        429: {"model": ErrorResponse, "description": "Too many compute requests."},
        500: {"model": ErrorResponse, "description": "Rendering failed (no details exposed)."},
    },
    dependencies=[Depends(compute_limit)],
)
def generate_report(request: Request, session: SessionDep, body: ReportRequest) -> Response:
    content = build_report(
        session, body.country, body.as_of, models_dir=request.app.state.settings.models_dir
    )
    try:
        data = _render(content, body.format)
    except Exception as exc:  # never leak renderer internals to the client
        logger.error(
            "report rendering failed",
            extra={"error_type": type(exc).__name__, "country": content.country_iso2},
        )
        raise ApiError(
            500,
            "report_generation_failed",
            "The report could not be rendered. Try again, or download the CSV or JSON instead.",
        ) from exc
    return Response(
        content=data,
        media_type=MEDIA[body.format],
        headers={
            "Content-Disposition": f'attachment; filename="{filename(content, body.format)}"',
            "Cache-Control": "no-store",
        },
    )
