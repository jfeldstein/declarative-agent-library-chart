"""Stable identifiers for tool calls and runs (contextvars)."""

from __future__ import annotations

import contextvars
from typing import Any
from uuid import uuid4

_run_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "obs_run_id", default=None
)
_thread_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "obs_thread_id", default=None
)
_tool_call_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "obs_tool_call_id", default=None
)
_request_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "obs_request_correlation_id", default=None
)
_wandb_session: contextvars.ContextVar[Any | None] = contextvars.ContextVar(
    "obs_wandb_session", default=None
)


def bind_run_context(
    *,
    run_id: str,
    thread_id: str,
    request_correlation_id: str | None = None,
) -> None:
    _run_id.set(run_id)
    _thread_id.set(thread_id)
    _request_correlation_id.set(request_correlation_id or run_id)


def get_run_id() -> str | None:
    return _run_id.get()


def get_thread_id() -> str | None:
    return _thread_id.get()


def get_tool_call_id() -> str | None:
    return _tool_call_id.get()


def get_request_correlation_id() -> str | None:
    return _request_correlation_id.get()


def new_tool_call_id(*, prefix: str = "tc") -> str:
    tid = f"{prefix}-{uuid4().hex[:16]}"
    _tool_call_id.set(tid)
    return tid


def clear_tool_call_id() -> None:
    _tool_call_id.set(None)


def set_wandb_session(session: Any | None) -> None:
    _wandb_session.set(session)


def get_wandb_session() -> Any | None:
    return _wandb_session.get()
