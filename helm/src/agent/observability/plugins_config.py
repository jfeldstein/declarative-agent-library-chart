"""Helm ``observability.plugins`` shape (scaffold for Phase 2+ provider plugins)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PluginToggle:
    enabled: bool = False


@dataclass(frozen=True)
class ObservabilityPluginsConfig:
    """Parsed configuration for optional observability plugins (future wiring from Helm/env)."""

    prometheus: PluginToggle = PluginToggle(enabled=False)
    langfuse: PluginToggle = PluginToggle(enabled=False)
    wandb: PluginToggle = PluginToggle(enabled=False)
    grafana: PluginToggle = PluginToggle(enabled=False)
    log_shipping: PluginToggle = PluginToggle(enabled=False)


def default_plugins_config() -> ObservabilityPluginsConfig:
    return ObservabilityPluginsConfig()
