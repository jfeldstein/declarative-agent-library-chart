"""Prometheus metrics for scheduled scraper jobs (agent_runtime_scraper_* prefix)."""

from __future__ import annotations

from prometheus_client import Counter, Histogram

from hosted_agents.metrics import TriggerResult
from hosted_agents.rag.metrics import classify_http_status

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
    10.0,
    30.0,
    float("inf"),
)

SCRAPER_RUNS = Counter(
    "agent_runtime_scraper_runs_total",
    "Count of scraper job executions",
    ("integration", "result"),
)
SCRAPER_RUN_DURATION = Histogram(
    "agent_runtime_scraper_run_duration_seconds",
    "Wall time of a scraper job from start to completion",
    ("integration",),
    buckets=_DURATION_BUCKETS,
)
SCRAPER_RAG_SUBMISSIONS = Counter(
    "agent_runtime_scraper_rag_submissions_total",
    "Attempts to submit ingested content to RAG /v1/embed",
    ("integration", "result"),
)


def observe_scraper_run(integration: str, success: bool, elapsed_seconds: float) -> None:
    result: str = "success" if success else "error"
    SCRAPER_RUNS.labels(integration=integration, result=result).inc()
    SCRAPER_RUN_DURATION.labels(integration=integration).observe(max(elapsed_seconds, 0.0))


def observe_rag_embed_attempt(integration: str, result: TriggerResult) -> None:
    SCRAPER_RAG_SUBMISSIONS.labels(integration=integration, result=result).inc()


def classify_rag_submission_result(exc: BaseException) -> TriggerResult:
    """Map httpx errors from a RAG /v1/embed call to metric result labels."""
    import httpx

    if isinstance(exc, httpx.HTTPStatusError):
        return classify_http_status(exc.response.status_code)
    if isinstance(exc, httpx.RequestError):
        return "server_error"
    return "server_error"
