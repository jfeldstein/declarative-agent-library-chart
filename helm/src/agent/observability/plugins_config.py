"""Helm ``observability.plugins`` shape (scaffold for Phase 2+ provider plugins)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _truthy(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


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


def plugins_config_from_env() -> ObservabilityPluginsConfig:
    """Best-effort plugin toggles from env (W&B mirrors ``HOSTED_AGENT_WANDB_ENABLED``)."""

    return ObservabilityPluginsConfig(
        wandb=PluginToggle(enabled=_truthy("HOSTED_AGENT_WANDB_ENABLED")),
    )
