"""Single exchange type between tool authors and the agent runtime."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class ToolSpec:
    """Stable id + model-facing metadata + typed args + dict-shaped handler."""

    id: str
    description: str
    args_schema: type[BaseModel]
    handler: Callable[[dict[str, Any]], dict[str, Any]]
