"""No-op consumer observability plugin for packaging tests and documentation examples."""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

from agent.observability.events import EventName
from agent.observability.events.bus import Subscriber

if TYPE_CHECKING:
    from agent.observability.events import SyncEventBus
    from agent.observability.plugins_config import ObservabilityPluginsConfig


class NoopConsumerObservabilityPlugin:
    """Minimal plugin object: optional hooks are no-ops (proves registration without SDKs)."""

    def enqueue(
        self,
        process_kind: Literal["agent", "scraper"],
        cfg: ObservabilityPluginsConfig,
        enqueue_subscription: Callable[[EventName, Subscriber], None],
    ) -> None:
        del process_kind, cfg, enqueue_subscription

    def attach(
        self,
        process_kind: Literal["agent", "scraper"],
        cfg: ObservabilityPluginsConfig,
        bus: SyncEventBus,
    ) -> None:
        del process_kind, cfg, bus


PLUGIN = NoopConsumerObservabilityPlugin()
