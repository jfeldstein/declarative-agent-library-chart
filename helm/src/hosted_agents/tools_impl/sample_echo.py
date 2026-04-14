"""Reference tool: echo a string (name: ``sample.echo``)."""

from __future__ import annotations

from typing import Any


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    message = str(arguments.get("message", ""))
    return {"echo": message}
