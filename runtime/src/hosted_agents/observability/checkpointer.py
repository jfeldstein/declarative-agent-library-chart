"""LangGraph checkpointer construction (memory today; Postgres/Redis contract)."""

from __future__ import annotations

from typing import Any

from hosted_agents.observability.settings import ObservabilitySettings


def build_checkpointer(settings: ObservabilitySettings) -> Any | None:
    """Return a LangGraph checkpointer or ``None`` when checkpointing is disabled.

    * **memory** — ``MemorySaver`` (dev / single replica); ``thread_id`` and ``checkpoint_id``
      follow LangGraph semantics (see runbook).
    * **postgres** — wire ``HOSTED_AGENT_CHECKPOINT_POSTGRES_URL`` to your deployment’s
      LangGraph Postgres checkpointer package when added to the image.
    * **redis** — same pattern as Postgres; reserved until a saver is pinned.
    """
    if not settings.checkpoints_enabled:
        return None
    backend = settings.checkpoint_backend.lower()
    if backend == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    if backend == "postgres":
        if not settings.checkpoint_postgres_url:
            msg = (
                "HOSTED_AGENT_CHECKPOINT_BACKEND=postgres requires "
                "HOSTED_AGENT_CHECKPOINT_POSTGRES_URL"
            )
            raise RuntimeError(msg)
        msg = (
            "Postgres checkpointing is configured but this image only bundles the memory saver. "
            "Add a LangGraph Postgres checkpointer dependency and wire it in "
            "hosted_agents.observability.checkpointer.build_checkpointer (see runbook)."
        )
        raise RuntimeError(msg)
    if backend == "redis":
        msg = (
            "HOSTED_AGENT_CHECKPOINT_BACKEND=redis is reserved until a Redis checkpointer "
            "is added to the runtime image (see runbook)."
        )
        raise RuntimeError(msg)
    msg = f"unknown HOSTED_AGENT_CHECKPOINT_BACKEND={settings.checkpoint_backend!r}"
    raise ValueError(msg)


def reset_compiled_trigger_graph_cache() -> None:
    """Clear lazy graph singleton (tests)."""

    from hosted_agents import trigger_graph

    trigger_graph._compiled_graph = None  # noqa: SLF001
    trigger_graph._compiled_graph_key = None  # noqa: SLF001
