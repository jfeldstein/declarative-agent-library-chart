"""Request-scoped identifiers for trigger runs (tool calls, tracing, correlation)."""

from __future__ import annotations

from contextvars import ContextVar, Token
from dataclasses import dataclass
from uuid import uuid4


@dataclass(frozen=True)
class TriggerRunIds:
    """Stable ids for one ``POST /api/v1/trigger`` invocation."""

    run_id: str
    thread_id: str
    request_id: str


_trigger_ids: ContextVar[TriggerRunIds | None] = ContextVar(
    "agent_trigger_ids", default=None
)
_tool_seq: ContextVar[int] = ContextVar("agent_tool_seq", default=0)


def current_trigger_ids() -> TriggerRunIds | None:
    return _trigger_ids.get()


def set_trigger_ids(ids: TriggerRunIds) -> Token:
    return _trigger_ids.set(ids)


def reset_trigger_ids(token: Token) -> None:
    _trigger_ids.reset(token)


def reset_tool_sequence() -> None:
    _tool_seq.set(0)


def next_tool_call_id() -> str:
    """Monotonic per-request tool id (``run_id`` prefix for global uniqueness)."""
    ids = current_trigger_ids()
    prefix = ids.run_id if ids else "norun"
    n = _tool_seq.get() + 1
    _tool_seq.set(n)
    return f"{prefix}-tool-{n}"


def fresh_tool_call_id() -> str:
    """Single-use id without run context (e.g. tests)."""
    return str(uuid4())
