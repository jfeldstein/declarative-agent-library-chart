"""Lifecycle event bus (draft spec dalc-observability-lifecycle-events).

[DALC-REQ-OBS-LIFE-001]
"""

from __future__ import annotations

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.observability.events.types import ToolCallCompletedLifecycleEvent


def test_sync_event_bus_delivers_to_subscribers() -> None:
    """[DALC-REQ-OBS-LIFE-001] Publish invokes subscribers in registration order."""
    bus = SyncEventBus()
    seen: list[str] = []

    def first(ev: LifecycleEvent) -> None:
        seen.append(f"a:{ev.name}")

    def second(ev: LifecycleEvent) -> None:
        seen.append(f"b:{ev.name}")

    bus.subscribe(EventName.TOOL_CALL_COMPLETED, first)
    bus.subscribe(EventName.TOOL_CALL_COMPLETED, second)
    bus.publish(
        ToolCallCompletedLifecycleEvent(
            name=EventName.TOOL_CALL_COMPLETED,
            payload={
                "tool": "sample.echo",
                "started_at": 0.0,
                "ok": True,
            },
        )
    )
    assert seen == [
        "a:tool.call.completed",
        "b:tool.call.completed",
    ]
