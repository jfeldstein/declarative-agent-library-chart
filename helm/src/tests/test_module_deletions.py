"""Removed supervisor coupling modules stay deleted."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest


def test_mcp_langchain_tools_module_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        __import__("agent.mcp_langchain_tools")


def test_subagent_units_module_removed() -> None:
    with pytest.raises(ModuleNotFoundError):
        __import__("agent.subagent_units")


def test_supervisor_has_no_toolset_imports() -> None:
    path = Path(__file__).resolve().parents[1] / "agent" / "supervisor.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    banned_mods = {
        "agent.tools.slack",
        "agent.tools.jira",
        "agent.tools.sample_echo",
        "agent.mcp_langchain_tools",
        "agent.subagent_units",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module not in banned_mods, node.module
