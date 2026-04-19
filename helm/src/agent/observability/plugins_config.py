"""Helm ``observability.plugins`` shape (scaffold for Phase 2+ provider plugins)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _truthy_plugin(key: str, *, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class PluginToggle:
    enabled: bool = False


@dataclass(frozen=True)
class ObservabilityPluginsConfig:
    """Parsed configuration for optional observability plugins (Helm/env)."""

    prometheus: PluginToggle = PluginToggle(enabled=False)
    langfuse: PluginToggle = PluginToggle(enabled=False)
    wandb: PluginToggle = PluginToggle(enabled=False)
    grafana: PluginToggle = PluginToggle(enabled=False)
    log_shipping: PluginToggle = PluginToggle(enabled=False)


def default_plugins_config() -> ObservabilityPluginsConfig:
    return ObservabilityPluginsConfig()


def plugins_config_from_env() -> ObservabilityPluginsConfig:
    """Env wiring for plugin toggles (mirrors Helm ``observability.plugins.*``)."""

    return ObservabilityPluginsConfig(
        prometheus=PluginToggle(
            enabled=_truthy_plugin(
                "HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED"
            ),
        ),
        langfuse=PluginToggle(
            enabled=_truthy_plugin(
                "HOSTED_AGENT_OBSERVABILITY_PLUGINS_LANGFUSE_ENABLED"
            ),
        ),
        wandb=PluginToggle(
            enabled=_truthy_plugin("HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED"),
        ),
        grafana=PluginToggle(
            enabled=_truthy_plugin(
                "HOSTED_AGENT_OBSERVABILITY_PLUGINS_GRAFANA_ENABLED"
            ),
        ),
        log_shipping=PluginToggle(
            enabled=_truthy_plugin(
                "HOSTED_AGENT_OBSERVABILITY_PLUGINS_LOG_SHIPPING_ENABLED",
            ),
        ),
    )
