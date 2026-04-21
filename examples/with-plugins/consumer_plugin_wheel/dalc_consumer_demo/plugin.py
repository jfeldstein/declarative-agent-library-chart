"""Example consumer observability plugin for ``examples/with-plugins``.

When this wheel is installed alongside the ``declarative-agent-library-chart`` runtime
(``agent`` package), hooks receive library types:

- ``cfg``: :class:`agent.observability.plugins_config.ObservabilityPluginsConfig`
- ``bus``: :class:`agent.observability.events.SyncEventBus` in ``attach``

Expected hook shape (optional; duck typing):

``attach(process_kind, cfg, bus) -> None``

where ``process_kind`` is ``\"agent\"`` or ``\"scraper\"``. See :mod:`agent.observability.bootstrap`.

**Lifecycle events:** subscribe with :meth:`SyncEventBus.subscribe`. The canonical list of
event names is :class:`agent.observability.events.types.EventName` (defined in the runtime
tree at ``helm/src/agent/observability/events/types.py``). Payload shapes per event live in
:mod:`agent.observability.events.payloads`.

For scraper CronJobs, keep hooks light (lazy-import heavy SDKs inside the handler body).
"""

from __future__ import annotations

import structlog
from typing import TYPE_CHECKING, Literal

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus

if TYPE_CHECKING:
    from agent.observability.plugins_config import ObservabilityPluginsConfig

log = structlog.get_logger(__name__)


class WithPluginsDemoPlugin:
    """Registers a trivial ``run.started`` subscriber (hello-world pattern)."""

    def attach(
        self,
        process_kind: Literal["agent", "scraper"],
        cfg: ObservabilityPluginsConfig,
        bus: SyncEventBus,
    ) -> None:
        def on_run_started(event: LifecycleEvent) -> None:
            payload = event.payload
            run_id = str(payload.get("run_id", "")) if isinstance(payload, dict) else ""
            log.info(
                "consumer_plugin_demo_hello_world",
                process_kind=process_kind,
                run_id=run_id,
                consumer_plugin_allowlist_len=len(
                    cfg.consumer_plugins.entry_point_allowlist,
                ),
            )

        bus.subscribe(EventName.RUN_STARTED, on_run_started)


PLUGIN = WithPluginsDemoPlugin()
