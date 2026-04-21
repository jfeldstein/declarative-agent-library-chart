"""Helm ``observability.plugins`` shape (scaffold for Phase 2+ provider plugins)."""

from __future__ import annotations

import os
from dataclasses import dataclass


def _truthy(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _trim(key: str) -> str:
    return os.environ.get(key, "").strip()


def _positive_float(key: str) -> float | None:
    raw = _trim(key)
    if not raw:
        return None
    try:
        v = float(raw)
    except ValueError:
        return None
    return v if v > 0 else None


def _truthy_any(*keys: str) -> bool:
    """True if any named env var is truthy (canonical ``HOSTED_AGENT_OBSERVABILITY_PLUGINS_*`` first)."""

    return any(_truthy(k, False) for k in keys)


def _trim_first(*keys: str) -> str:
    """First non-empty trimmed value among env keys (canonical ``HOSTED_AGENT_OBSERVABILITY_PLUGINS_*`` first)."""

    for k in keys:
        v = _trim(k)
        if v:
            return v
    return ""


def _positive_float_first(*keys: str) -> float | None:
    for k in keys:
        v = _positive_float(k)
        if v is not None:
            return v
    return None


def _comma_allowlist_env(key: str) -> tuple[str, ...]:
    raw = _trim(key)
    if not raw:
        return ()
    return tuple(p.strip() for p in raw.split(",") if p.strip())


@dataclass(frozen=True)
class PluginToggle:
    enabled: bool = False


@dataclass(frozen=True)
class LangfusePluginSettings:
    """Langfuse SDK plugin config (maps from ``observability.plugins.langfuse`` Helm / env keys)."""

    enabled: bool = False
    host: str | None = None
    public_key: str | None = None
    secret_key: str | None = None
    flush_interval_seconds: float | None = None


@dataclass(frozen=True)
class ConsumerPluginsSettings:
    """PEP 621 consumer hooks; non-empty ``entry_point_allowlist`` enables discovery.

    Traceability: [DALC-REQ-CUSTOM-O11Y-004]
    """

    entry_point_allowlist: tuple[str, ...] = ()
    json_config: str | None = None


@dataclass(frozen=True)
class ObservabilityPluginsConfig:
    """Parsed configuration for optional observability plugins (Helm/env)."""

    prometheus: PluginToggle = PluginToggle(enabled=False)
    langfuse: LangfusePluginSettings = LangfusePluginSettings()
    wandb: PluginToggle = PluginToggle(enabled=False)
    grafana: PluginToggle = PluginToggle(enabled=False)
    log_shipping: PluginToggle = PluginToggle(enabled=False)
    consumer_plugins: ConsumerPluginsSettings = ConsumerPluginsSettings()


def default_plugins_config() -> ObservabilityPluginsConfig:
    return ObservabilityPluginsConfig()


def plugins_config_from_env() -> ObservabilityPluginsConfig:
    """Env wiring for plugin toggles (mirrors Helm ``observability.plugins.*``).

    Canonical names use the ``HOSTED_AGENT_OBSERVABILITY_PLUGINS_*`` prefix (aligned with
    Prometheus). Legacy ``HOSTED_AGENT_LANGFUSE_*`` / ``HOSTED_AGENT_WANDB_ENABLED`` keys
    remain accepted for backward-compatible deployments.
    """

    lf = LangfusePluginSettings(
        enabled=_truthy_any(
            "HOSTED_AGENT_OBSERVABILITY_PLUGINS_LANGFUSE_ENABLED",
            "HOSTED_AGENT_LANGFUSE_ENABLED",
        ),
        host=_trim_first(
            "HOSTED_AGENT_OBSERVABILITY_PLUGINS_LANGFUSE_HOST",
            "HOSTED_AGENT_LANGFUSE_HOST",
        )
        or None,
        public_key=_trim_first(
            "HOSTED_AGENT_OBSERVABILITY_PLUGINS_LANGFUSE_PUBLIC_KEY",
            "HOSTED_AGENT_LANGFUSE_PUBLIC_KEY",
        )
        or None,
        secret_key=_trim_first(
            "HOSTED_AGENT_OBSERVABILITY_PLUGINS_LANGFUSE_SECRET_KEY",
            "HOSTED_AGENT_LANGFUSE_SECRET_KEY",
        )
        or None,
        flush_interval_seconds=_positive_float_first(
            "HOSTED_AGENT_OBSERVABILITY_PLUGINS_LANGFUSE_FLUSH_INTERVAL_SECONDS",
            "HOSTED_AGENT_LANGFUSE_FLUSH_INTERVAL_SECONDS",
        ),
    )
    wandb_enabled = _truthy_any(
        "HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED",
        "HOSTED_AGENT_WANDB_ENABLED",
    )
    consumer = ConsumerPluginsSettings(
        entry_point_allowlist=_comma_allowlist_env(
            "HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS",
        ),
        json_config=_trim("HOSTED_AGENT_OBSERVABILITY_PLUGINS_CONSUMER_CONFIG_JSON")
        or None,
    )
    return ObservabilityPluginsConfig(
        prometheus=PluginToggle(
            enabled=_truthy("HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED"),
        ),
        langfuse=lf,
        wandb=PluginToggle(enabled=wandb_enabled),
        grafana=PluginToggle(
            enabled=_truthy("HOSTED_AGENT_OBSERVABILITY_PLUGINS_GRAFANA_ENABLED"),
        ),
        log_shipping=PluginToggle(
            enabled=_truthy(
                "HOSTED_AGENT_OBSERVABILITY_PLUGINS_LOG_SHIPPING_ENABLED",
            ),
        ),
        consumer_plugins=consumer,
    )
