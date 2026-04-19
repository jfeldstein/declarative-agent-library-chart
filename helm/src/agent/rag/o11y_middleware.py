"""Record RAG HTTP metrics from response status (and unhandled exceptions)."""

from __future__ import annotations

import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from agent.observability.middleware import (
    publish_rag_embed_completed,
    publish_rag_query_completed,
)
from agent.rag.metrics import classify_http_status


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
                publish_rag_embed_completed(result=res, elapsed_seconds=elapsed)
            elif path == "/v1/query":
                publish_rag_query_completed(result=res, elapsed_seconds=elapsed)
            raise

        elapsed = time.perf_counter() - start
        result = classify_http_status(response.status_code)
        if path in ("/v1/embed", "/v1/relate"):
            publish_rag_embed_completed(result=result, elapsed_seconds=elapsed)
        elif path == "/v1/query":
            publish_rag_query_completed(result=result, elapsed_seconds=elapsed)
        return response
