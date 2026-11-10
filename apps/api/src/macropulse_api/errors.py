"""Consistent error contract.

Every error body is `{"error": {code, message, details, request_id}}`.
"""

from __future__ import annotations

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from macropulse_api.schemas import ErrorBody, ErrorResponse

logger = logging.getLogger("macropulse.errors")

_HTTP_CODES = {
    400: "bad_request",
    401: "unauthorized",
    403: "forbidden",
    404: "not_found",
    405: "method_not_allowed",
    409: "conflict",
    413: "payload_too_large",
    429: "rate_limited",
    503: "service_unavailable",
}


class ApiError(Exception):
    """Raise from endpoints/services for an expected, user-facing failure."""

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details
        self.headers = headers


def _body(request: Request, code: str, message: str, details: dict[str, Any] | None) -> Any:
    request_id = getattr(request.state, "request_id", None)
    return ErrorResponse(
        error=ErrorBody(code=code, message=message, details=details, request_id=request_id)
    ).model_dump(mode="json")


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(ApiError)
    async def _api_error(request: Request, exc: ApiError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(request, exc.code, exc.message, exc.details),
            headers=exc.headers,
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = _HTTP_CODES.get(exc.status_code, "http_error")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(request, code, message, None),
            headers=getattr(exc, "headers", None),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Only location, message and type: never echo raw input back (could contain anything).
        errors = [
            {"loc": list(e.get("loc", ())), "msg": e.get("msg", ""), "type": e.get("type", "")}
            for e in exc.errors()
        ]
        return JSONResponse(
            status_code=422,
            content=_body(request, "validation_error", "Invalid request.", {"errors": errors}),
        )

    @app.exception_handler(SQLAlchemyError)
    async def _database_error(request: Request, exc: SQLAlchemyError) -> JSONResponse:
        # Log the class only; driver messages can contain connection strings.
        logger.error(
            "database_error", extra={"path": request.url.path, "error_type": type(exc).__name__}
        )
        return JSONResponse(
            status_code=503,
            content=_body(
                request,
                "database_unavailable",
                "The database is unavailable or not migrated. "
                "Run `uv run macropulse db upgrade` and check DATABASE_URL.",
                None,
            ),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_error", extra={"path": request.url.path})
        return JSONResponse(
            status_code=500,
            content=_body(request, "internal_error", "An unexpected error occurred.", None),
        )
