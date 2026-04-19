"""Load-time aggregation of ToolSpecs via Python entry points."""

from __future__ import annotations

import re
from importlib.metadata import entry_points
from typing import Iterable

from agent.tools.contract import ToolSpec

ENTRY_POINT_GROUP = "declarative_agent.tools"
_SANITIZE_RE = re.compile(r"[^a-zA-Z0-9_]+")

_REGISTRY: dict[str, ToolSpec] | None = None


def sanitize_tool_name(raw: str) -> str:
    """Same mapping the supervisor uses when calling ``@tool(name=...)``."""
    s = _SANITIZE_RE.sub("_", raw.strip()).strip("_")
    if not s:
        msg = f"ToolSpec.id sanitizes to empty langchain name: {raw!r}"
        raise ValueError(msg)
    return s


def _iter_entry_point_specs() -> Iterable[ToolSpec]:
    eps = entry_points()
    selected = eps.select(group=ENTRY_POINT_GROUP)
    for ep in selected:
        loaded = ep.load()
        specs = loaded() if callable(loaded) else loaded
        for spec in specs:
            if not isinstance(spec, ToolSpec):
                msg = (
                    f"entry point {ep.name!r} yielded {type(spec).__name__}; "
                    "expected ToolSpec"
                )
                raise TypeError(msg)
            yield spec


def _merge(
    into: dict[str, ToolSpec],
    spec: ToolSpec,
    sanitized: dict[str, str],
) -> None:
    if spec.id in into:
        msg = f"duplicate ToolSpec id: {spec.id!r}"
        raise ValueError(msg)
    safe = sanitize_tool_name(spec.id)
    if safe in sanitized and sanitized[safe] != spec.id:
        msg = (
            f"ToolSpec ids {sanitized[safe]!r} and {spec.id!r} "
            f"both sanitize to {safe!r}"
        )
        raise ValueError(msg)
    into[spec.id] = spec
    sanitized[safe] = spec.id


def load_registry() -> dict[str, ToolSpec]:
    """Discover and memoize all ToolSpecs via entry points. Idempotent."""
    global _REGISTRY
    if _REGISTRY is not None:
        return _REGISTRY
    out: dict[str, ToolSpec] = {}
    sanitized: dict[str, str] = {}
    for spec in _iter_entry_point_specs():
        _merge(out, spec, sanitized)
    _REGISTRY = out
    return _REGISTRY


def register_toolspec(spec: ToolSpec) -> None:
    """Programmatic registration (tests / runtime composition)."""
    reg = load_registry()
    sanitized: dict[str, str] = {sanitize_tool_name(tid): tid for tid in reg.keys()}
    _merge(reg, spec, sanitized)


def registered_ids() -> frozenset[str]:
    return frozenset(load_registry().keys())


def _reset_for_tests() -> None:
    global _REGISTRY
    _REGISTRY = None
