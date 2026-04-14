"""Reference scraper: pushes fixture text + entity graph slice to the RAG HTTP API.

Env: ``RAG_SERVICE_URL``, ``SCRAPER_SCOPE``, optional ``REFERENCE_SCRAPER_TEXT``,
``SCRAPER_INTEGRATION`` (Prometheus ``integration`` label). See ``examples/with-scrapers/`` and
``metrics.py`` (maintainer checklist for new scrapers).
"""

from __future__ import annotations

import os
import sys
import time

import httpx

from hosted_agents.scrapers.metrics import (
    classify_rag_submission_result,
    maybe_start_scraper_metrics_http,
    observe_rag_embed_attempt,
    observe_scraper_run,
    stop_scraper_metrics_http,
)


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


def _post_embed(
    client: httpx.Client, base: str, payload: dict, integration: str
) -> None:
    try:
        r = client.post(f"{base}/v1/embed", json=payload)
        r.raise_for_status()
    except httpx.HTTPError as exc:
        observe_rag_embed_attempt(integration, classify_rag_submission_result(exc))
        raise
    observe_rag_embed_attempt(integration, "success")


def _integration_label() -> str:
    v = os.environ.get("SCRAPER_INTEGRATION", "reference").strip()
    return v or "reference"


def run() -> None:
    t0 = time.perf_counter()
    integration = _integration_label()
    httpd = maybe_start_scraper_metrics_http()

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
        stop_scraper_metrics_http(httpd)


if __name__ == "__main__":
    run()
