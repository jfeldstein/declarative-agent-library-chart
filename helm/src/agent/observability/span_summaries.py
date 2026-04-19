"""Tool invocation span summaries (operator queries, optional Postgres persistence)."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class ToolSpanSummary:
    tool_call_id: str
    run_id: str
    thread_id: str
    tool_name: str
    duration_ms: int
    outcome: str
    args_hash: str | None = None


def redacted_args_hash(arguments: dict[str, object]) -> str:
    """Stable short hash of tool arguments after dropping obviously sensitive keys."""

    redacted = {k: v for k, v in arguments.items() if "secret" not in k.lower()}
    raw = json.dumps(redacted, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


class MemorySpanSummaryStore:
    """In-process span summaries (dev / tests)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._rows: list[ToolSpanSummary] = []

    def record(self, row: ToolSpanSummary) -> None:
        with self._lock:
            self._rows.append(row)
            if len(self._rows) > 10_000:
                self._rows = self._rows[-5000:]

    def by_run(self, run_id: str) -> list[ToolSpanSummary]:
        with self._lock:
            return [r for r in self._rows if r.run_id == run_id]

    def reset(self) -> None:
        with self._lock:
            self._rows.clear()
