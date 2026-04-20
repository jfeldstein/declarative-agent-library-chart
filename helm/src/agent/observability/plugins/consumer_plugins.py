"""Discover and invoke optional consumer observability plugins via PEP 621 entry points.

Traceability: [DALC-REQ-CUSTOM-O11Y-001] [DALC-REQ-CUSTOM-O11Y-002] [DALC-REQ-CUSTOM-O11Y-005] [DALC-REQ-CUSTOM-O11Y-006]
"""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Literal

import structlog

from agent.observability.events import EventName, SyncEventBus
from agent.observability.events.bus import Subscriber
from agent.observability.plugins_config import ObservabilityPluginsConfig

log = structlog.get_logger(__name__)

OBSERVABILITY_PLUGINS_ENTRY_POINT_GROUP = "declarative_agent.observability_plugins"


def _selected_entry_points(allowlist: tuple[str, ...]) -> list[EntryPoint]:
    eps = entry_points().select(group=OBSERVABILITY_PLUGINS_ENTRY_POINT_GROUP)
    entries = list(eps)
    if allowlist:
        allowed = frozenset(allowlist)
        entries = [ep for ep in entries if ep.name in allowed]
    return entries


def _materialize_plugin(ep: EntryPoint) -> Any:
    loaded = ep.load()
    return loaded() if callable(loaded) else loaded


def _enqueue_one(
    ep: EntryPoint,
    process: Literal["agent", "scraper"],
    cfg: ObservabilityPluginsConfig,
    enqueue: Callable[[EventName, Subscriber], None],
    *,
    strict: bool,
) -> None:
    try:
        plugin = _materialize_plugin(ep)
        hook = getattr(plugin, "enqueue", None)
        if hook is None:
            return
        hook(process, cfg, enqueue)
    except Exception:
        if strict:
            raise
        log.warning(
            "consumer_observability_enqueue_failed",
            entry_point=ep.name,
            exc_info=True,
        )


def _attach_one(
    ep: EntryPoint,
    process: Literal["agent", "scraper"],
    cfg: ObservabilityPluginsConfig,
    bus: SyncEventBus,
    *,
    strict: bool,
) -> None:
    try:
        plugin = _materialize_plugin(ep)
        hook = getattr(plugin, "attach", None)
        if hook is None:
            return
        hook(process, cfg, bus)
    except Exception:
        if strict:
            raise
        log.warning(
            "consumer_observability_attach_failed",
            entry_point=ep.name,
            exc_info=True,
        )


def enqueue_consumer_plugins(
    process: Literal["agent", "scraper"],
    cfg: ObservabilityPluginsConfig,
    enqueue: Callable[[EventName, Subscriber], None],
) -> None:
    """Invoke consumer ``enqueue`` hooks after built-in enqueue wiring."""
    consumer = cfg.consumer_plugins
    if not consumer.enabled:
        return
    strict = consumer.strict
    allowlist = consumer.entry_point_allowlist
    for ep in _selected_entry_points(allowlist):
        _enqueue_one(ep, process, cfg, enqueue, strict=strict)


def attach_consumer_plugins(
    process: Literal["agent", "scraper"],
    cfg: ObservabilityPluginsConfig,
    bus: SyncEventBus,
) -> None:
    """Invoke consumer ``attach`` hooks after built-in attach wiring."""
    consumer = cfg.consumer_plugins
    if not consumer.enabled:
        return
    strict = consumer.strict
    allowlist = consumer.entry_point_allowlist
    for ep in _selected_entry_points(allowlist):
        _attach_one(ep, process, cfg, bus, strict=strict)
