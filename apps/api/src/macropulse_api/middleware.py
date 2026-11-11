"""Request-id propagation, request body limits, security headers and one log line per request."""

from __future__ import annotations

import logging
import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from macropulse_api.logging_config import request_id_var

logger = logging.getLogger("macropulse.request")
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{8,64}$")
# Every API request body is a small JSON object (reports, scenarios); anything bigger is refused.
MAX_BODY_BYTES = 64 * 1024
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def _error(status: int, code: str, message: str, request_id: str) -> JSONResponse:
    body = {"error": {"code": code, "message": message, "details": None, "request_id": request_id}}
    return JSONResponse(status_code=status, content=body)


def _body_problem(request: Request, request_id: str) -> JSONResponse | None:
    if request.method not in {"POST", "PUT", "PATCH"}:
        return None
    length = request.headers.get("content-length")
    if length is None or not length.isdigit():
        return _error(411, "length_required", "Send a Content-Length header.", request_id)
    if int(length) > MAX_BODY_BYTES:
        return _error(
            413,
            "payload_too_large",
            f"Request body exceeds {MAX_BODY_BYTES // 1024} KiB.",
            request_id,
        )
    return None


def install_request_middleware(app: FastAPI) -> None:
    @app.middleware("http")
    async def _request_context(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        incoming = request.headers.get("x-request-id", "")
        request_id = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
        request.state.request_id = request_id
        token = request_id_var.set(request_id)
        started = time.perf_counter()
        status = 500
        try:
            refused = _body_problem(request, request_id)
            response = refused if refused is not None else await call_next(request)
            status = response.status_code
            response.headers["X-Request-ID"] = request_id
            for name, value in SECURITY_HEADERS.items():
                response.headers.setdefault(name, value)
            return response
        finally:
            logger.info(
                "request",
                extra={
                    "method": request.method,
                    "path": request.url.path,  # path only: query strings are not logged
                    "status": status,
                    "duration_ms": round((time.perf_counter() - started) * 1000, 1),
                },
            )
            request_id_var.reset(token)
