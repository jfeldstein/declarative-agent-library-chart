"""Record RAG HTTP metrics from response status (and unhandled exceptions)."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from hosted_agents.rag.metrics import (
    classify_http_status,
    observe_rag_embed,
    observe_rag_query,
)


class RAGMetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):  # type: ignore[no-untyped-def]
        path = request.url.path
        method = request.method.upper()

        if (
            method != "POST"
            or path in ("/metrics", "/health")
            or path.startswith("/docs")
        ):
            return await call_next(request)

        start = time.perf_counter()
        try:
            response: Response = await call_next(request)
        except Exception:
            elapsed = time.perf_counter() - start
            res = "server_error"
            if path in ("/v1/embed", "/v1/relate"):
                observe_rag_embed(res, elapsed)
            elif path == "/v1/query":
                observe_rag_query(res, elapsed)
            raise

        elapsed = time.perf_counter() - start
        result = classify_http_status(response.status_code)
        if path in ("/v1/embed", "/v1/relate"):
            observe_rag_embed(result, elapsed)
        elif path == "/v1/query":
            observe_rag_query(result, elapsed)
        return response
