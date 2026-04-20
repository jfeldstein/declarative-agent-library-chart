"""Ensure built-in pyproject declares tool entry points."""

from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import pytest

from agent.tools.registry import ENTRY_POINT_GROUP


def test_pyproject_declares_three_builtin_entry_points() -> None:
    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    raw = pyproject.read_text(encoding="utf-8")
    assert '[project.entry-points."declarative_agent.tools"]' in raw
    assert 'builtin-sample = "agent.tools.sample_echo:TOOLS"' in raw
    assert 'builtin-slack = "agent.tools.slack:TOOLS"' in raw
    assert 'builtin-jira = "agent.tools.jira:TOOLS"' in raw
    assert '[project.entry-points."declarative_agent.observability_plugins"]' in raw
    assert (
        'noop-consumer = "agent.observability.plugins.noop_consumer_plugin:PLUGIN"'
        in raw
    )


def test_entry_point_group_matches_registry_constant() -> None:
    assert ENTRY_POINT_GROUP == "declarative_agent.tools"


@pytest.mark.parametrize(
    "name",
    ["builtin-sample", "builtin-slack", "builtin-jira"],
)
def test_entry_points_resolve_to_tuple_of_toolspec(name: str) -> None:
    group = ENTRY_POINT_GROUP
    eps = entry_points().select(group=group)
    matched = [ep for ep in eps if ep.name == name]
    assert matched, name
    loaded = matched[0].load()
    specs = loaded() if callable(loaded) else loaded
    assert isinstance(specs, tuple)
    from agent.tools.contract import ToolSpec

    assert specs and all(isinstance(s, ToolSpec) for s in specs)


def test_observability_plugins_entry_point_resolves() -> None:
    eps = entry_points().select(group="declarative_agent.observability_plugins")
    noop = [ep for ep in eps if ep.name == "noop-consumer"]
    assert noop
    loaded = noop[0].load()
    plugin = loaded() if callable(loaded) else loaded
    assert hasattr(plugin, "attach")
