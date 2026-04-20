"""Map :class:`~agent.observability.plugins_config.ObservabilityPluginsConfig` to bus wiring.

Bootstrap (:mod:`agent.observability.bootstrap`) stays free of provider-specific imports;
this module is the single place that decides which optional plugins attach for a process.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from agent.observability.events import EventName, SyncEventBus
from agent.observability.events.bus import Subscriber
from agent.observability.plugins.langfuse_bridge import (
    build_langfuse_client,
    register_langfuse_plugin,
)
from agent.observability.plugins.prometheus import enqueue_prometheus_subscriptions
from agent.observability.plugins.wandb.plugin import register_wandb_trace_plugin
from agent.observability.plugins_config import ObservabilityPluginsConfig


def enqueue_plugins_from_config(
    cfg: ObservabilityPluginsConfig,
    enqueue: Callable[[EventName, Subscriber], None],
) -> None:
    """Append ``(EventName, handler)`` pairs for plugins that use the pre-bus subscription queue."""

    if cfg.prometheus.enabled:
        enqueue_prometheus_subscriptions(enqueue)


def attach_plugins_from_config(
    process: Literal["agent", "scraper"],
    cfg: ObservabilityPluginsConfig,
    bus: SyncEventBus,
) -> None:
    """Subscribe plugins that attach directly to an existing :class:`SyncEventBus`."""

    register_langfuse_plugin(bus, build_langfuse_client(cfg.langfuse))
    if process == "agent":
        register_wandb_trace_plugin(bus, cfg)
