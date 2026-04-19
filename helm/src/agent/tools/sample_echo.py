"""Reference tool: echo a string (name: ``sample.echo``)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from agent.tools.contract import ToolSpec


class SampleEchoArgs(BaseModel):
    message: str = ""


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    message = str(arguments.get("message", ""))
    return {"echo": message}


TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        id="sample.echo",
        description="Echo back a string (bundled sample MCP tool).",
        args_schema=SampleEchoArgs,
        handler=run,
    ),
)
