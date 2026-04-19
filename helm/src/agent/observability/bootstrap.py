"""Per-process lifecycle bus factories (agent pod vs scraper CronJob)."""

from __future__ import annotations

from typing import Literal

from agent.observability.events import SyncEventBus
from agent.observability.plugins.prometheus import (
    register_prometheus_agent_plugin,
    register_prometheus_scraper_plugin,
)
from agent.observability.plugins_config import (
    ObservabilityPluginsConfig,
    plugins_config_from_env,
)

ProcessKind = Literal["agent", "scraper"]

_agent_bus: SyncEventBus | None = None
_scraper_bus: SyncEventBus | None = None


def build_event_bus(
    process: ProcessKind,
    config: ObservabilityPluginsConfig | None = None,
) -> SyncEventBus:
    """Construct an isolated bus instance and attach optional observability plugins."""

    cfg = config or plugins_config_from_env()
    bus = SyncEventBus()
    if cfg.prometheus.enabled:
        if process == "agent":
            register_prometheus_agent_plugin(bus)
        else:
            register_prometheus_scraper_plugin(bus)
    return bus


def ensure_agent_observability(
    config: ObservabilityPluginsConfig | None = None,
) -> SyncEventBus:
    """Idempotent agent-process setup (FastAPI ``create_app``)."""

    global _agent_bus
    if _agent_bus is None:
        _agent_bus = build_event_bus("agent", config or plugins_config_from_env())
    return _agent_bus


def ensure_scraper_observability(
    config: ObservabilityPluginsConfig | None = None,
) -> SyncEventBus:
    """Idempotent scraper CronJob setup (:func:`agent.scrapers.base.run_scraper_main`)."""

    global _scraper_bus
    if _scraper_bus is None:
        _scraper_bus = build_event_bus("scraper", config or plugins_config_from_env())
    return _scraper_bus


def agent_event_bus() -> SyncEventBus:
    """Return the agent bus, creating it with legacy subscribers if needed."""

    return ensure_agent_observability()


def scraper_event_bus() -> SyncEventBus:
    return ensure_scraper_observability()


def reset_observability_for_tests() -> None:
    """Clear singleton buses (pytest isolation)."""

    global _agent_bus, _scraper_bus
    _agent_bus = None
    _scraper_bus = None
