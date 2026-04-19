"""Select in-memory vs Postgres observability repositories (per-process pool cache)."""

from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Iterator

from agent.observability.correlation import correlation_store
from agent.observability.feedback import feedback_store
from agent.observability.repositories import (
    CorrelationRepository,
    FeedbackRepository,
    SideEffectRepository,
    SpanSummaryRepository,
)
from agent.observability.settings import ObservabilitySettings
from agent.observability.side_effects import side_effect_checkpoints
from agent.observability.span_summaries import MemorySpanSummaryStore

_stores_ctx: ContextVar[ObservabilityStores | None] = ContextVar(
    "agent_observability_stores", default=None
)

_obs_pool_cache: dict[str, object] = {}
_bundle_cache: tuple[str, ObservabilityStores] | None = None


@dataclass(frozen=True)
class ObservabilityStores:
    correlation: CorrelationRepository
    feedback: FeedbackRepository
    side_effects: SideEffectRepository
    span_summaries: SpanSummaryRepository


_memory_spans = MemorySpanSummaryStore()


def _pool_max(settings: ObservabilitySettings) -> int:
    return max(1, min(50, settings.postgres_pool_max))


def _pool_for_url(
    url: str,
    settings: ObservabilitySettings,
    *,
    create_pool: object,
    ensure_schema: object,
) -> object:
    if url in _obs_pool_cache:
        return _obs_pool_cache[url]
    pool = create_pool(url, min_size=1, max_size=_pool_max(settings))  # type: ignore[operator]
    ensure_schema(pool)  # type: ignore[operator]
    _obs_pool_cache[url] = pool
    return pool


def _bundle_key(settings: ObservabilitySettings) -> str:
    url = settings.effective_observability_postgres_url() or ""
    return f"{settings.observability_store}|{url}"


def build_observability_stores(settings: ObservabilitySettings) -> ObservabilityStores:
    """Return repository bundle for this settings snapshot (cached per store mode + URL)."""

    global _bundle_cache
    key = _bundle_key(settings)
    if _bundle_cache and _bundle_cache[0] == key:
        return _bundle_cache[1]

    if settings.observability_store == "postgres":
        try:
            from agent.observability.postgres_repos import (
                create_observability_pool,
                ensure_observability_schema,
                PostgresCorrelationStore,
                PostgresFeedbackStore,
                PostgresSideEffectStore,
                PostgresSpanSummaryStore,
            )
        except ImportError as exc:
            msg = (
                "HOSTED_AGENT_OBSERVABILITY_STORE=postgres requires optional dependencies. "
                "Install with `uv sync --extra postgres`. "
                f"Import error: {exc}"
            )
            raise RuntimeError(msg) from exc
        url = settings.effective_observability_postgres_url()
        if not url:
            msg = (
                "HOSTED_AGENT_OBSERVABILITY_STORE=postgres requires "
                "HOSTED_AGENT_POSTGRES_URL"
            )
            raise RuntimeError(msg)
        pool = _pool_for_url(
            url,
            settings,
            create_pool=create_observability_pool,
            ensure_schema=ensure_observability_schema,
        )
        bundle = ObservabilityStores(
            correlation=PostgresCorrelationStore(pool),  # type: ignore[arg-type]
            feedback=PostgresFeedbackStore(pool),  # type: ignore[arg-type]
            side_effects=PostgresSideEffectStore(pool),  # type: ignore[arg-type]
            span_summaries=PostgresSpanSummaryStore(pool),  # type: ignore[arg-type]
        )
    else:
        bundle = ObservabilityStores(
            correlation=correlation_store,
            feedback=feedback_store,
            side_effects=side_effect_checkpoints,
            span_summaries=_memory_spans,
        )
    _bundle_cache = (key, bundle)
    return bundle


def reset_observability_stores_cache() -> None:
    """Clear cached Postgres pools and bundles (tests / reload)."""

    global _bundle_cache, _obs_pool_cache
    _bundle_cache = None
    _memory_spans.reset()
    for _k, pool in list(_obs_pool_cache.items()):
        try:
            pool.close()  # type: ignore[attr-defined]
        except Exception:
            pass
    _obs_pool_cache.clear()


def get_observability_stores() -> ObservabilityStores:
    """Active bundle: context override, else cached default from env."""

    ctx = _stores_ctx.get()
    if ctx is not None:
        return ctx
    return build_observability_stores(ObservabilitySettings.from_env())


def get_correlation_store() -> CorrelationRepository:
    return get_observability_stores().correlation


def get_feedback_store() -> FeedbackRepository:
    return get_observability_stores().feedback


def get_side_effect_store() -> SideEffectRepository:
    return get_observability_stores().side_effects


def get_span_summary_store() -> SpanSummaryRepository:
    return get_observability_stores().span_summaries


@contextmanager
def bind_observability_stores(stores: ObservabilityStores) -> Iterator[None]:
    token = _stores_ctx.set(stores)
    try:
        yield
    finally:
        _stores_ctx.reset(token)
