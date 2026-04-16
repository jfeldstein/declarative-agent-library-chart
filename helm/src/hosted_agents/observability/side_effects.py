"""Logical checkpoints around user-visible side effects (e.g. Slack posts)."""

from __future__ import annotations

import threading
import time
import uuid
from dataclasses import dataclass

from hosted_agents.observability.run_context import (
    get_run_id,
    get_thread_id,
    get_tool_call_id,
)


@dataclass(frozen=True)
class SideEffectCheckpoint:
    checkpoint_id: str
    run_id: str
    thread_id: str
    tool_call_id: str
    tool_name: str
    external_ref: dict[str, str]
    created_at: float


class SideEffectCheckpointStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._records: list[SideEffectCheckpoint] = []

    def add(self, rec: SideEffectCheckpoint) -> None:
        with self._lock:
            self._records.append(rec)

    def by_thread(self, thread_id: str) -> list[SideEffectCheckpoint]:
        with self._lock:
            return [r for r in self._records if r.thread_id == thread_id]

    def reset(self) -> None:
        with self._lock:
            self._records.clear()


side_effect_checkpoints = SideEffectCheckpointStore()


def record_side_effect_checkpoint(
    *,
    tool_name: str,
    external_ref: dict[str, str],
    tool_call_id: str | None = None,
) -> SideEffectCheckpoint:
    """Persist metadata binding a visible side effect to run and tool identifiers."""

    tc = tool_call_id or get_tool_call_id() or f"tc-{uuid.uuid4().hex[:12]}"
    run_id = get_run_id() or "unknown-run"
    thread_id = get_thread_id() or "unknown-thread"
    cid = f"se-{uuid.uuid4().hex}"
    rec = SideEffectCheckpoint(
        checkpoint_id=cid,
        run_id=run_id,
        thread_id=thread_id,
        tool_call_id=tc,
        tool_name=tool_name,
        external_ref=dict(external_ref),
        created_at=time.time(),
    )
    from hosted_agents.observability.stores import get_side_effect_store

    get_side_effect_store().add(rec)
    return rec
