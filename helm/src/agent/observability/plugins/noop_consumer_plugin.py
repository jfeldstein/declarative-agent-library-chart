"""Built-in no-op consumer plugin (tests / documentation baseline)."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from agent.observability.events import SyncEventBus
    from agent.observability.plugins_config import ObservabilityPluginsConfig


class NoopConsumerObservabilityPlugin:
    """Minimal plugin object: optional ``attach`` hook is a no-op."""

    def attach(
        self,
        process_kind: Literal["agent", "scraper"],
        cfg: ObservabilityPluginsConfig,
        bus: SyncEventBus,
    ) -> None:
        del process_kind, cfg, bus


PLUGIN = NoopConsumerObservabilityPlugin()
