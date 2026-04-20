"""Example consumer observability plugin for ``examples/with-plugins``.

When this wheel is installed alongside the ``declarative-agent-library-chart`` runtime
(``agent`` package), hooks receive library types:

- ``cfg``: :class:`agent.observability.plugins_config.ObservabilityPluginsConfig`
- ``enqueue_subscription``: ``Callable[[EventName, Subscriber], None]`` before the bus exists
- ``bus``: :class:`agent.observability.events.SyncEventBus` in ``attach``

Expected hook shapes (implement any subset; duck typing):

``enqueue(process_kind, cfg, enqueue_subscription) -> None``

``attach(process_kind, cfg, bus) -> None``

where ``process_kind`` is ``\"agent\"`` or ``\"scraper\"``. See :mod:`agent.observability.bootstrap`.

For scraper CronJobs, keep hooks light (lazy-import heavy SDKs inside the method body).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from agent.observability.events import EventName, SyncEventBus
    from agent.observability.events.bus import Subscriber
    from agent.observability.plugins_config import ObservabilityPluginsConfig


class WithPluginsDemoPlugin:
    """No-op implementation."""

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


PLUGIN = WithPluginsDemoPlugin()
