"""Example consumer observability plugin for ``examples/with-plugins``.

When this wheel is installed alongside the ``declarative-agent-library-chart`` runtime
(``agent`` package), hooks receive library types:

- ``cfg``: :class:`agent.observability.plugins_config.ObservabilityPluginsConfig`
- ``bus``: :class:`agent.observability.events.SyncEventBus` in ``attach``

Expected hook shape (optional; duck typing):

``attach(process_kind, cfg, bus) -> None``

where ``process_kind`` is ``\"agent\"`` or ``\"scraper\"``. See :mod:`agent.observability.bootstrap`.

For scraper CronJobs, keep hooks light (lazy-import heavy SDKs inside the method body).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from agent.observability.events import SyncEventBus
    from agent.observability.plugins_config import ObservabilityPluginsConfig


class WithPluginsDemoPlugin:
    """No-op implementation."""

    def attach(
        self,
        process_kind: Literal["agent", "scraper"],
        cfg: ObservabilityPluginsConfig,
        bus: SyncEventBus,
    ) -> None:
        del process_kind, cfg, bus


PLUGIN = WithPluginsDemoPlugin()
