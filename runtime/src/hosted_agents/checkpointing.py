"""LangGraph checkpointer selection (OpenSpec: ``runtime-langgraph-checkpoints``)."""

from __future__ import annotations

import os
from typing import Any

_COMPILE_KEYS: dict[str, Any] = {}
_MEMORY_SAVER: Any | None = None


def effective_checkpoint_store() -> str:
    """Return the active store kind.

    * unset / empty → ``memory`` (default-on persistence in-process)
    * ``none`` → no checkpointer (ephemeral deployments)
    * ``memory`` → :class:`langgraph.checkpoint.memory.MemorySaver`
    * ``postgres`` / ``redis`` → reserved; raises until wired
    """
    raw = os.environ.get("HOSTED_AGENT_CHECKPOINT_STORE", "").strip().lower()
    return raw if raw else "memory"


def checkpoints_globally_enabled() -> bool:
    return effective_checkpoint_store() != "none"


def resolve_checkpointer() -> tuple[Any | None, str]:
    """Return ``(checkpointer_or_none, compile_cache_key)``."""
    store = effective_checkpoint_store()
    if store == "none":
        return None, "none"
    if store == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        global _MEMORY_SAVER
        if _MEMORY_SAVER is None:
            _MEMORY_SAVER = MemorySaver()
        return _MEMORY_SAVER, "memory"
    if store in ("postgres", "redis"):
        raise RuntimeError(
            f"HOSTED_AGENT_CHECKPOINT_STORE={store!r} is not implemented yet; "
            "use 'memory' or 'none'."
        )
    raise ValueError(f"Unknown HOSTED_AGENT_CHECKPOINT_STORE={store!r}")


def compiled_graph_cache() -> dict[str, Any]:
    return _COMPILE_KEYS


def clear_compiled_graph_cache() -> None:
    _COMPILE_KEYS.clear()


def clear_memory_checkpointer() -> None:
    """Test helper: reset in-process checkpoint storage."""
    global _MEMORY_SAVER
    _MEMORY_SAVER = None
    clear_compiled_graph_cache()
