"""Discover and invoke optional consumer observability plugins via PEP 621 entry points.

Traceability: [DALC-REQ-CUSTOM-O11Y-001] [DALC-REQ-CUSTOM-O11Y-002] [DALC-REQ-CUSTOM-O11Y-005] [DALC-REQ-CUSTOM-O11Y-006]
"""

from __future__ import annotations

from collections.abc import Callable
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Literal

import structlog

from agent.observability.events import SyncEventBus
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


def _load_plugin_or_none(ep: EntryPoint) -> Any | None:
    try:
        return _materialize_plugin(ep)
    except Exception:
        log.warning(
            "consumer_observability_plugin_load_failed",
            entry_point=ep.name,
            exc_info=True,
        )
        return None


def _require_callable_attach(ep: EntryPoint, plugin: Any) -> Callable[..., None]:
    hook = getattr(plugin, "attach", None)
    if hook is None:
        msg = (
            f"Consumer observability plugin {ep.name!r} ({ep.value}) is allowlisted "
            "but exposes no 'attach' method; implement attach(process_kind, cfg, bus)."
        )
        raise ValueError(msg)
    if not callable(hook):
        msg = (
            f"Consumer observability plugin {ep.name!r} ({ep.value}) has non-callable "
            f"'attach' ({type(hook).__name__!r}); expected attach(process_kind, cfg, bus)."
        )
        raise TypeError(msg)
    return hook


def _invoke_attach_safely(
    ep: EntryPoint, hook: Callable[..., None], *args: object
) -> None:
    try:
        hook(*args)
    except Exception:
        log.warning(
            "consumer_observability_attach_failed",
            entry_point=ep.name,
            exc_info=True,
        )


def _attach_one(
    ep: EntryPoint,
    process: Literal["agent", "scraper"],
    cfg: ObservabilityPluginsConfig,
    bus: SyncEventBus,
) -> None:
    plugin = _load_plugin_or_none(ep)
    if plugin is None:
        return
    hook = _require_callable_attach(ep, plugin)
    _invoke_attach_safely(ep, hook, process, cfg, bus)


def attach_consumer_plugins(
    process: Literal["agent", "scraper"],
    cfg: ObservabilityPluginsConfig,
    bus: SyncEventBus,
) -> None:
    """Invoke consumer ``attach`` hooks after built-in attach wiring."""
    allowlist = cfg.consumer_plugins.entry_point_allowlist
    if not allowlist:
        return
    for ep in _selected_entry_points(allowlist):
        _attach_one(ep, process, cfg, bus)
