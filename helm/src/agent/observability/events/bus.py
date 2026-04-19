"""In-process synchronous event bus (one instance per runtime process kind)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Mapping
from typing import Any

from .types import EventName, LifecycleEvent

Subscriber = Callable[[LifecycleEvent], None]


class SyncEventBus:
    """Publish/subscribe bus; subscribers run synchronously in publish order."""

    def __init__(self) -> None:
        self._subs: dict[EventName, list[Subscriber]] = defaultdict(list)

    def subscribe(self, event_name: EventName, subscriber: Subscriber) -> None:
        self._subs[event_name].append(subscriber)

    def publish(self, event: LifecycleEvent) -> None:
        for fn in self._subs.get(event.name, ()):
            fn(event)


def redact_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Placeholder for bounded-label / cardinality policy (expanded in Phase 2)."""

    return dict(payload)
