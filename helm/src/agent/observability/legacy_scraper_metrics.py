"""Mirror scraper lifecycle events into ``dalc_scraper_*`` metrics (separate registry)."""

from __future__ import annotations

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.scrapers.metrics import observe_rag_embed_attempt, observe_scraper_run


def register_scraper_legacy_metrics(bus: SyncEventBus) -> None:
    bus.subscribe(EventName.SCRAPER_RUN_COMPLETED, _on_scraper_run)
    bus.subscribe(EventName.SCRAPER_RAG_EMBED_ATTEMPT, _on_rag_embed_attempt)


def _on_scraper_run(event: LifecycleEvent) -> None:
    p = event.payload
    observe_scraper_run(
        str(p["integration"]),
        bool(p.get("success")),
        float(p["elapsed_seconds"]),
    )


def _on_rag_embed_attempt(event: LifecycleEvent) -> None:
    p = event.payload
    observe_rag_embed_attempt(str(p["integration"]), str(p["result"]))
