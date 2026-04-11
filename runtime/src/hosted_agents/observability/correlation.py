"""Durable mapping from Slack ``(channel_id, message_ts)`` to run identifiers."""

from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class SlackMessageRef:
    channel_id: str
    message_ts: str


@dataclass(frozen=True)
class ToolCorrelation:
    tool_call_id: str
    run_id: str
    thread_id: str
    checkpoint_id: str | None
    tool_name: str
    wandb_run_id: str | None = None


class CorrelationStore:
    """Process-local store (replace with SQL/Redis in production)."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._by_slack: dict[tuple[str, str], ToolCorrelation] = {}

    def put_slack_message(self, ref: SlackMessageRef, corr: ToolCorrelation) -> None:
        key = (ref.channel_id, ref.message_ts)
        with self._lock:
            self._by_slack[key] = corr

    def get_by_slack(self, ref: SlackMessageRef) -> ToolCorrelation | None:
        key = (ref.channel_id, ref.message_ts)
        with self._lock:
            return self._by_slack.get(key)

    def reset(self) -> None:
        with self._lock:
            self._by_slack.clear()


correlation_store = CorrelationStore()
