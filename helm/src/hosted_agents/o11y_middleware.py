"""HTTP middleware for request correlation and structured logs."""

from __future__ import annotations

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from hosted_agents.o11y_logging import (
    SERVICE_NAME,
    configure_request_logging,
    get_logger,
)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """Bind ``request_id`` + ``service`` for structlog; echo ``X-Request-Id`` on responses."""

    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        configure_request_logging()
        structlog.contextvars.clear_contextvars()
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        request.state.request_id = (
            request_id  # same id echoed on response and forwarded outbound
        )
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            service=SERVICE_NAME,
        )
        log = get_logger()
        log.info(
            "http_request_start",
            path=request.url.path,
            method=request.method,
        )
        response: Response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        log.info(
            "http_request_end",
            path=request.url.path,
            status_code=response.status_code,
        )
        structlog.contextvars.clear_contextvars()
        return response
