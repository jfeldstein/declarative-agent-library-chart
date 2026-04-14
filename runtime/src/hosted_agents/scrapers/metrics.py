"""Prometheus metrics for scheduled scraper jobs (``agent_runtime_scraper_*`` prefix).

New integration checklist (keep in sync when adding a scraper implementation):

- **Helm:** extend ``helm/chart/templates/scraper-cronjobs.yaml`` so the job ``name`` maps to
  the correct ``python -m ...`` module (today: ``reference`` → ``reference_job``, else
  ``stub_job``).
- **Example:** update ``examples/with-scrapers/values.yaml`` and
  ``examples/with-scrapers/tests/with_scrapers_test.yaml`` so operators see every value key
  and CI asserts rendering for each built-in kind.
- **Dashboard:** add or adjust panels in ``grafana/cfha-agent-overview.json`` for new metric
  labels or series; document scrape in ``grafana/README.md`` / ``docs/observability.md``.
- **Runtime:** register counters/histograms on :data:`SCRAPER_REGISTRY` here so CronJob pods do
  not mix scraper series with the agent/RAG default registry.
"""

from __future__ import annotations

import os
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Literal

import httpx
from prometheus_client import (
    CONTENT_TYPE_LATEST,
    CollectorRegistry,
    Counter,
    Histogram,
    generate_latest,
)

# Dedicated registry so scraper CronJob pods do not expose agent/RAG metrics from the global REGISTRY.
SCRAPER_REGISTRY = CollectorRegistry()

RagSubmitResult = Literal["success", "client_error", "server_error"]

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
    registry=SCRAPER_REGISTRY,
)
SCRAPER_RUN_DURATION = Histogram(
    "agent_runtime_scraper_run_duration_seconds",
    "Wall time of a scraper job from start to completion",
    ("integration",),
    buckets=_DURATION_BUCKETS,
    registry=SCRAPER_REGISTRY,
)
SCRAPER_RAG_SUBMISSIONS = Counter(
    "agent_runtime_scraper_rag_submissions_total",
    "Attempts to submit ingested content to RAG /v1/embed",
    ("integration", "result"),
    registry=SCRAPER_REGISTRY,
)


def _classify_http_status(status_code: int) -> RagSubmitResult:
    """Match RAG HTTP embed/query metrics: status → success | client_error | server_error."""
    if status_code >= 500:
        return "server_error"
    if status_code >= 400:
        return "client_error"
    return "success"


def observe_scraper_run(
    integration: str, success: bool, elapsed_seconds: float
) -> None:
    result: str = "success" if success else "error"
    SCRAPER_RUNS.labels(integration=integration, result=result).inc()
    SCRAPER_RUN_DURATION.labels(integration=integration).observe(
        max(elapsed_seconds, 0.0)
    )


def observe_rag_embed_attempt(integration: str, result: RagSubmitResult) -> None:
    SCRAPER_RAG_SUBMISSIONS.labels(integration=integration, result=result).inc()


def classify_rag_submission_result(exc: BaseException) -> RagSubmitResult:
    """Map httpx errors from POST /v1/embed to RagSubmitResult labels."""
    if isinstance(exc, httpx.HTTPStatusError):
        return _classify_http_status(exc.response.status_code)
    if isinstance(exc, httpx.RequestError):
        return "server_error"
    return "server_error"


def parse_scraper_metrics_addr(addr: str) -> tuple[str, int]:
    """Parse ``host:port`` or IPv6 ``[addr]:port`` for the scraper metrics listener."""
    s = addr.strip()
    if not s:
        raise ValueError("SCRAPER_METRICS_ADDR is empty")
    if s.startswith("["):
        if "]:" not in s:
            raise ValueError(
                f"SCRAPER_METRICS_ADDR IPv6 literal must use [host]:port form, got {addr!r}",
            )
        host_bracketed, _, port_s = s.rpartition("]:")
        host = host_bracketed[1:]
        return host, int(port_s)
    host, sep, port_s = s.rpartition(":")
    if not sep:
        raise ValueError(f"SCRAPER_METRICS_ADDR must be host:port, got {addr!r}")
    return (host if host else "0.0.0.0"), int(port_s)


def start_scraper_metrics_http(addr: str) -> HTTPServer:
    """Serve ``GET /metrics`` from :data:`SCRAPER_REGISTRY` (background thread)."""
    listen_host, port = parse_scraper_metrics_addr(addr)

    class _MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in ("/metrics", "/metrics/"):
                self.send_error(404)
                return
            payload = generate_latest(SCRAPER_REGISTRY)
            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, _format: str, *_args: object) -> None:
            return

    httpd = HTTPServer((listen_host, port), _MetricsHandler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    return httpd


def maybe_start_scraper_metrics_http() -> HTTPServer | None:
    addr = os.environ.get("SCRAPER_METRICS_ADDR", "").strip()
    if not addr:
        return None
    return start_scraper_metrics_http(addr)


def stop_scraper_metrics_http(httpd: HTTPServer | None) -> None:
    if httpd is None:
        return
    grace = float(os.environ.get("SCRAPER_METRICS_GRACE_SECONDS", "15"))
    if grace > 0:
        time.sleep(grace)
    httpd.shutdown()
