"""LangGraph checkpointer construction (memory, Postgres, Redis contract).

In-process ``memory`` / ``MemorySaver`` defaults are for automated tests and simple
local development only (ADR 0008); they do not satisfy durability when multiple
replicas share state or execution persistence must survive restarts—use Postgres
when those requirements apply.
"""

from __future__ import annotations

from typing import Any

from agent.observability.settings import ObservabilitySettings

_cp_pool: Any | None = None
_cp_pool_url: str | None = None


def _checkpoint_connection_pool_cls() -> type:
    from psycopg_pool import ConnectionPool

    return ConnectionPool


def _checkpoint_postgres_saver_cls() -> type:
    from langgraph.checkpoint.postgres import PostgresSaver

    return PostgresSaver


def _validate_postgres_url(url: str) -> None:
    u = url.strip()
    if not u.startswith(("postgresql://", "postgres://")):
        msg = (
            "Postgres URL must start with postgres:// or postgresql:// "
            "(set HOSTED_AGENT_POSTGRES_URL)"
        )
        raise RuntimeError(msg)


def reset_checkpoint_postgres_pool() -> None:
    """Close cached checkpoint pool (tests / env change)."""

    global _cp_pool, _cp_pool_url
    if _cp_pool is not None:
        try:
            _cp_pool.close()
        except Exception:
            pass
    _cp_pool = None
    _cp_pool_url = None


def _build_postgres_checkpointer(settings: ObservabilitySettings) -> Any:
    url = settings.checkpoint_postgres_url
    if not url:
        msg = (
            "HOSTED_AGENT_CHECKPOINT_BACKEND=postgres requires "
            "HOSTED_AGENT_POSTGRES_URL"
        )
        raise RuntimeError(msg)
    _validate_postgres_url(url)
    try:
        from psycopg.rows import dict_row
    except ImportError as exc:
        msg = (
            "Postgres checkpointing requires optional dependencies. "
            "Install with `uv sync --extra postgres` (or pip install "
            "`declarative-agent-library-chart[postgres]`). "
            f"Import error: {exc}"
        )
        raise RuntimeError(msg) from exc

    global _cp_pool, _cp_pool_url
    max_size = max(1, min(50, settings.postgres_pool_max))
    Pool = _checkpoint_connection_pool_cls()
    Saver = _checkpoint_postgres_saver_cls()
    if _cp_pool is None or _cp_pool_url != url:
        if _cp_pool is not None:
            try:
                _cp_pool.close()
            except Exception:
                pass
        try:
            _cp_pool = Pool(
                conninfo=url,
                min_size=1,
                max_size=max_size,
                kwargs={
                    "autocommit": True,
                    "prepare_threshold": 0,
                    "row_factory": dict_row,
                },
            )
            _cp_pool_url = url
        except Exception as exc:
            _cp_pool = None
            _cp_pool_url = None
            msg = (
                "Could not open Postgres connection pool for LangGraph checkpoints. "
                "Verify HOSTED_AGENT_POSTGRES_URL (host, port, credentials, "
                "TLS/sslmode) and that the database is reachable from this pod. "
                f"Underlying error: {exc!s}"
            )
            raise RuntimeError(msg) from exc

    assert _cp_pool is not None
    saver = Saver(_cp_pool)
    try:
        saver.setup()
    except Exception as exc:
        msg = (
            "Connected to Postgres but LangGraph checkpoint setup/migrations failed. "
            "Ensure the DB role can CREATE TABLE and run migrations from "
            "langgraph-checkpoint-postgres. "
            f"Underlying error: {exc!s}"
        )
        raise RuntimeError(msg) from exc
    return saver


def build_checkpointer(settings: ObservabilitySettings) -> Any | None:
    """Return a LangGraph checkpointer or ``None`` when checkpointing is disabled.

    * **memory** — ``MemorySaver`` (tests and local dev only; not durable across
      replicas or restarts—see ADR 0008); ``thread_id`` and ``checkpoint_id``
      follow LangGraph semantics (see runbook).
    * **postgres** — ``langgraph-checkpoint-postgres`` + ``psycopg`` pool (optional ``[postgres]`` extra).
      Set ``HOSTED_AGENT_POSTGRES_URL``.
    * **redis** — same pattern as Postgres; reserved until a saver is pinned.
    """
    if not settings.checkpoints_enabled:
        return None
    backend = settings.checkpoint_backend.lower()
    if backend == "memory":
        from langgraph.checkpoint.memory import MemorySaver

        return MemorySaver()
    if backend == "postgres":
        return _build_postgres_checkpointer(settings)
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

    reset_checkpoint_postgres_pool()
    from agent import trigger_graph

    trigger_graph._compiled_graph = None  # noqa: SLF001
    trigger_graph._compiled_graph_key = None  # noqa: SLF001
