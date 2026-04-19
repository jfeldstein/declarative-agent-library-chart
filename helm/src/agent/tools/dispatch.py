"""Dispatch ``tool`` id to implementation via the entry-point registry.

[DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-002] Same handler objects as supervisor ``_bind`` → ``run_tool_json`` → ``invoke_tool``.
"""

from __future__ import annotations

from typing import Any

from agent.tools.registry import load_registry, registered_ids


def invoke_tool(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch by tool id to registered ToolSpec handlers."""
    reg = load_registry()
    spec = reg.get(tool)
    if spec is None:
        msg = f"unknown tool: {tool}"
        raise KeyError(msg)
    return spec.handler(arguments)


def __getattr__(name: str) -> Any:
    if name == "REGISTERED_MCP_TOOL_IDS":
        return registered_ids()
    msg = f"module {__name__!r} has no attribute {name!r}"
    raise AttributeError(msg)
