"""Reference scraper: pushes fixture text + entity graph slice to the RAG HTTP API."""

from __future__ import annotations

import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer

import httpx
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest

from hosted_agents.scrapers.metrics import (
    classify_rag_submission_result,
    observe_rag_embed_attempt,
    observe_scraper_run,
)


def _start_metrics_http(addr: str) -> HTTPServer:
    host, sep, port_s = addr.rpartition(":")
    if not sep:
        raise ValueError(f"SCRAPER_METRICS_ADDR must be host:port, got {addr!r}")
    port = int(port_s)
    listen_host = host or "0.0.0.0"

    class _MetricsHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            if self.path not in ("/metrics", "/metrics/"):
                self.send_error(404)
                return
            payload = generate_latest(REGISTRY)
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


def _embed_payload() -> dict:
    scope = os.environ.get("SCRAPER_SCOPE", "reference").strip() or "reference"
    return {
        "scope": scope,
        "entities": [
            {"id": "ref-doc", "entity_type": "document"},
            {"id": "ref-folder", "entity_type": "folder"},
        ],
        "relationships": [
            {
                "source": "ref-doc",
                "target": "ref-folder",
                "relationship_type": "contained_in",
            },
        ],
        "items": [
            {
                "text": os.environ.get(
                    "REFERENCE_SCRAPER_TEXT",
                    "Reference scraper fixture: login timeout bug tracked under REF-1.",
                ),
                "metadata": {"source": "reference-scraper"},
                "entity_id": "ref-doc",
            },
        ],
    }


def _post_embed(client: httpx.Client, base: str, payload: dict, integration: str) -> None:
    try:
        r = client.post(f"{base}/v1/embed", json=payload)
        r.raise_for_status()
    except httpx.HTTPError as exc:
        observe_rag_embed_attempt(integration, classify_rag_submission_result(exc))
        raise
    observe_rag_embed_attempt(integration, "success")


def run() -> None:
    t0 = time.perf_counter()
    integration = os.environ.get("SCRAPER_INTEGRATION", "reference").strip() or "reference"
    metrics_addr = os.environ.get("SCRAPER_METRICS_ADDR", "").strip()
    httpd: HTTPServer | None = None
    if metrics_addr:
        httpd = _start_metrics_http(metrics_addr)

    run_ok = False
    try:
        base = os.environ.get("RAG_SERVICE_URL", "").strip().rstrip("/")
        if not base:
            print("RAG_SERVICE_URL is required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        payload = _embed_payload()
        with httpx.Client(timeout=60.0) as client:
            _post_embed(client, base, payload, integration)
        run_ok = True
    finally:
        elapsed = time.perf_counter() - t0
        observe_scraper_run(integration, run_ok, elapsed)
        if httpd is not None:
            grace = float(os.environ.get("SCRAPER_METRICS_GRACE_SECONDS", "15"))
            if grace > 0:
                time.sleep(grace)
            httpd.shutdown()


if __name__ == "__main__":
    run()
