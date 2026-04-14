"""JSON-in-env configuration for subagents, skills, MCP tool allowlists, and RAG URL."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any


def _load_json_list(key: str) -> list[dict[str, Any]]:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        msg = f"{key} must be a JSON array"
        raise ValueError(msg)
    return [x for x in data if isinstance(x, dict)]


def _load_json_str_list(key: str) -> list[str]:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        msg = f"{key} must be a JSON array of strings"
        raise ValueError(msg)
    return [str(x) for x in data]


@dataclass(frozen=True)
class RuntimeConfig:
    """Process configuration derived from environment (typically ConfigMap → env)."""

    rag_base_url: str
    subagents: list[dict[str, Any]]
    skills: list[dict[str, Any]]
    enabled_mcp_tools: list[str]

    @classmethod
    def from_env(cls) -> RuntimeConfig:
        rag = os.environ.get("HOSTED_AGENT_RAG_BASE_URL", "").strip()
        return cls(
            rag_base_url=rag,
            subagents=_load_json_list("HOSTED_AGENT_SUBAGENTS_JSON"),
            skills=_load_json_list("HOSTED_AGENT_SKILLS_JSON"),
            enabled_mcp_tools=_load_json_str_list(
                "HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON"
            ),
        )


def subagent_system_prompt(entry: dict[str, Any]) -> str:
    """Return configured prompt text for a subagent definition."""
    for key in ("systemPrompt", "system_prompt"):
        val = entry.get(key)
        if isinstance(val, str) and val.strip():
            return val
    return ""
