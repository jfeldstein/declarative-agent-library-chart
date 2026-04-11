"""Dispatch ``tool`` id to implementation."""

from __future__ import annotations

from typing import Any

from hosted_agents.tools_impl import sample_echo


def invoke_tool(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if tool == "sample.echo":
        return sample_echo.run(arguments)
    msg = f"unknown tool: {tool}"
    raise KeyError(msg)
