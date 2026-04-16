"""Human feedback, idempotency, and orphan handling."""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class HumanFeedbackEvent:
    registry_id: str
    schema_version: str
    label_id: str
    tool_call_id: str
    checkpoint_id: str | None
    run_id: str
    thread_id: str
    feedback_source: str
    agent_id: str | None = None
    dedupe_key: str | None = None
    created_at: float = field(default_factory=time.time)


@dataclass(frozen=True)
class OrphanReactionEvent:
    channel_id: str
    message_ts: str
    reason: str
    raw_event_id: str | None
    created_at: float = field(default_factory=time.time)


class FeedbackStore:
    """In-memory persistence for tests; swap for durable storage in production."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._human: list[HumanFeedbackEvent] = []
        self._orphans: list[OrphanReactionEvent] = []
        self._idempotency: dict[str, HumanFeedbackEvent] = {}

    def record_human(self, ev: HumanFeedbackEvent) -> HumanFeedbackEvent | None:
        """Upsert by dedupe_key when set; latest wins for same user/checkpoint policy key."""

        with self._lock:
            key = ev.dedupe_key
            if key:
                existing = self._idempotency.get(key)
                if existing:
                    self._human.remove(existing)
                self._idempotency[key] = ev
            self._human.append(ev)
            return ev

    def record_orphan_reaction(self, ev: OrphanReactionEvent) -> None:
        with self._lock:
            self._orphans.append(ev)

    def human_events(self) -> list[HumanFeedbackEvent]:
        with self._lock:
            return list(self._human)

    def orphans(self) -> list[OrphanReactionEvent]:
        with self._lock:
            return list(self._orphans)

    def reset(self) -> None:
        with self._lock:
            self._human.clear()
            self._orphans.clear()
            self._idempotency.clear()


feedback_store = FeedbackStore()
