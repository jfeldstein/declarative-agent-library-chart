"""Dispatch layer uses the registry exclusively."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from pydantic import BaseModel

from agent.tools.contract import ToolSpec
from agent.tools.dispatch import REGISTERED_MCP_TOOL_IDS, invoke_tool
from agent.tools.registry import (
    _reset_for_tests,
    load_registry,
    register_toolspec,
    registered_ids,
)


def test_sample_echo() -> None:
    out = invoke_tool("sample.echo", {"message": "hi"})
    assert out == {"echo": "hi"}


def test_invoke_tool_dispatches_via_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_for_tests()

    class M(BaseModel):
        k: str = ""

    register_toolspec(
        ToolSpec(
            id="x.y",
            description="d",
            args_schema=M,
            handler=lambda args: {"echo": args.get("k")},
        ),
    )
    assert invoke_tool("x.y", {"k": "v"}) == {"echo": "v"}


def test_invoke_tool_unknown_raises_keyerror() -> None:
    load_registry()
    with pytest.raises(KeyError, match="unknown tool: zzz"):
        invoke_tool("zzz", {})


def test_registered_mcp_tool_ids_is_frozenset_attribute() -> None:
    assert isinstance(REGISTERED_MCP_TOOL_IDS, frozenset)
    assert REGISTERED_MCP_TOOL_IDS == registered_ids()


def test_dispatch_has_no_toolset_imports() -> None:
    path = Path(__file__).resolve().parents[1] / "agent" / "tools" / "dispatch.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    banned = {"slack", "jira", "sample_echo"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            root = node.module.split(".")[0]
            assert root not in banned, node.module
