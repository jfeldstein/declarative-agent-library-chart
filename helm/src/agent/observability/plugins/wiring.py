"""Map :class:`~agent.observability.plugins_config.ObservabilityPluginsConfig` to bus wiring.

Bootstrap (:mod:`agent.observability.bootstrap`) stays free of provider-specific imports;
this module is the single place that decides which optional plugins attach for a process.

Plugin toggles are gated here explicitly (ADR 0017). Built-in ``register_*`` runs only
when the matching toggle is on; Langfuse validates credentials inside
``register_langfuse_plugin``.
"""

from __future__ import annotations

from typing import Literal

from agent.observability.events import SyncEventBus
from agent.observability.plugins.prometheus import register_prometheus_plugin
from agent.observability.plugins.wandb.plugin import register_wandb_trace_plugin
from agent.observability.plugins_config import ObservabilityPluginsConfig


def attach_plugins_from_config(
    process: Literal["agent", "scraper"],
    cfg: ObservabilityPluginsConfig,
    bus: SyncEventBus,
) -> None:
    """Subscribe plugins that attach directly to an existing :class:`SyncEventBus`."""

    if cfg.prometheus.enabled:
        register_prometheus_plugin(bus)
    if cfg.langfuse.enabled:
        from agent.observability.plugins.langfuse_bridge import register_langfuse_plugin

        register_langfuse_plugin(bus, cfg.langfuse)
    if process == "agent" and cfg.wandb.enabled:
        register_wandb_trace_plugin(bus, cfg)
