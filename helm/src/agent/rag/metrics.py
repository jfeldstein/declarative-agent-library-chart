"""Prometheus metrics for the RAG HTTP service (agent_runtime_rag_* prefix)."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

from agent.metrics import TriggerResult

_DURATION_BUCKETS = (
    0.001,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    float("inf"),
)

RAG_EMBED_REQUESTS = Counter(
    "agent_runtime_rag_embed_requests_total",
    "Count of RAG embed and relate mutations",
    ("result",),
)
RAG_EMBED_DURATION = Histogram(
    "agent_runtime_rag_embed_duration_seconds",
    "Latency of RAG /v1/embed and /v1/relate handling",
    ("result",),
    buckets=_DURATION_BUCKETS,
)

RAG_QUERY_REQUESTS = Counter(
    "agent_runtime_rag_query_requests_total",
    "Count of RAG /v1/query invocations",
    ("result",),
)
RAG_QUERY_DURATION = Histogram(
    "agent_runtime_rag_query_duration_seconds",
    "Latency of RAG /v1/query handling",
    ("result",),
    buckets=_DURATION_BUCKETS,
)


def observe_rag_embed(result: TriggerResult, elapsed_seconds: float) -> None:
    RAG_EMBED_REQUESTS.labels(result=result).inc()
    RAG_EMBED_DURATION.labels(result=result).observe(max(elapsed_seconds, 0.0))


def observe_rag_query(result: TriggerResult, elapsed_seconds: float) -> None:
    RAG_QUERY_REQUESTS.labels(result=result).inc()
    RAG_QUERY_DURATION.labels(result=result).observe(max(elapsed_seconds, 0.0))


def classify_http_status(status_code: int) -> TriggerResult:
    if status_code >= 500:
        return "server_error"
    if status_code >= 400:
        return "client_error"
    return "success"
