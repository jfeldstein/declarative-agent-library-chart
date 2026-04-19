"""Shared scraper runtime: RAG ``/v1/embed`` ingestion and process lifecycle.

Integration modules fetch remote data and map it to one or more **embed payloads**
(JSON bodies for ``POST .../v1/embed``). This module performs HTTP submission,
metrics for each attempt, and optional **commit** callbacks only after all payloads
in a batch succeed (matching prior per-scraper behavior).

Traceability: [DALC-REQ-SCRAPER-BASE-001] [DALC-REQ-SCRAPER-BASE-003]
"""

from __future__ import annotations

import time
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from hosted_agents.scrapers.metrics import (
    bounded_integration_label,
    classify_rag_submission_result,
    maybe_start_scraper_metrics_http,
    observe_rag_embed_attempt,
    observe_scraper_run,
    stop_scraper_metrics_http,
)


def integration_label(env_value: str, *, fallback: str) -> str:
    """Bounded Prometheus ``integration`` label from ``SCRAPER_INTEGRATION``."""
    return bounded_integration_label(env_value, fallback=fallback)


def ingest_embed_payloads(
    rag_base: str,
    integration: str,
    payloads: Iterable[dict[str, Any]],
    *,
    timeout: float = 120.0,
) -> None:
    """POST each payload to RAG ``/v1/embed``; record success/failure metrics."""
    rag = rag_base.strip().rstrip("/")
    with httpx.Client(timeout=timeout) as hx:
        for payload in payloads:
            try:
                r = hx.post(f"{rag}/v1/embed", json=payload)
                r.raise_for_status()
            except httpx.HTTPError as exc:
                observe_rag_embed_attempt(
                    integration, classify_rag_submission_result(exc)
                )
                raise
            observe_rag_embed_attempt(integration, "success")


@dataclass(frozen=True)
class ScrapedEmbeds:
    """Normalized RAG payloads from a source-specific scraper run."""

    payloads: list[dict[str, Any]]
    commit: Callable[[], None] | None = None


class ScraperIntegration(Protocol):
    """Integration hook: fetch + map upstream data into embed payloads only.

    Implementations **must not** call ``POST .../v1/embed`` or write cursor stores;
    this runtime performs ingestion and persistence after a successful embed batch.
    """

    def build_batch(self) -> ScrapedEmbeds: ...


def ingest_from_integration(
    *,
    rag_base: str,
    integration: str,
    scraper: ScraperIntegration,
    timeout: float = 120.0,
) -> None:
    """POST embed payloads from ``scraper.build_batch()`` then run optional commit."""
    ingest_scraped_embeds(rag_base, integration, scraper.build_batch(), timeout=timeout)


def ingest_scraped_embeds(
    rag_base: str,
    integration: str,
    batch: ScrapedEmbeds,
    *,
    timeout: float = 120.0,
) -> None:
    """Ingest payloads to RAG, then run **commit** (e.g. cursor/watermark) on full success."""
    if not batch.payloads:
        return
    ingest_embed_payloads(rag_base, integration, batch.payloads, timeout=timeout)
    if batch.commit is not None:
        batch.commit()


def run_scraper_main(integration: str, main: Callable[[], None]) -> None:
    """Metrics HTTP server, wall-clock timing, and ``observe_scraper_run`` wrapper."""
    t0 = time.perf_counter()
    httpd = maybe_start_scraper_metrics_http()
    run_ok = False
    try:
        main()
        run_ok = True
    finally:
        elapsed = time.perf_counter() - t0
        observe_scraper_run(integration, run_ok, elapsed)
        stop_scraper_metrics_http(httpd)
