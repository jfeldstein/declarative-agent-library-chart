"""Skill load and MCP tool steps (shared by trigger pipeline and supervisor tools)."""

from __future__ import annotations

import json
import time
from typing import Any

from hosted_agents.metrics import observe_mcp_tool, observe_skill_load
from hosted_agents.o11y_logging import get_logger
from hosted_agents.run_context import next_tool_call_id
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.skills_state import unlock_tools, unlocked_tools
from hosted_agents.tools_impl.dispatch import invoke_tool
from hosted_agents.trigger_errors import TriggerHttpError


def run_skill_load_json(cfg: RuntimeConfig, name: str) -> str:
    start = time.perf_counter()
    entry = next((s for s in cfg.skills if str(s.get("name")) == name), None)
    if entry is None:
        observe_skill_load(name, "error", start)
        raise TriggerHttpError(404, "skill not found")
    raw_extra = entry.get("extraTools") or entry.get("extra_tools") or []
    extra = [str(x) for x in raw_extra] if isinstance(raw_extra, list) else []
    unlock_tools(extra)
    prompt = str(entry.get("prompt") or "")
    observe_skill_load(name, "success", start)
    return json.dumps({"name": name, "prompt": prompt, "activated_tools": extra})


def run_tool_json(cfg: RuntimeConfig, tool: str, arguments: dict[str, Any]) -> str:
    start = time.perf_counter()
    tool_call_id = next_tool_call_id()
    get_logger().debug(
        "mcp_tool_invoke",
        tool=tool,
        tool_call_id=tool_call_id,
    )
    allowed = set(cfg.enabled_mcp_tools) | set(unlocked_tools())
    if tool not in allowed:
        observe_mcp_tool(tool, "error", start)
        raise TriggerHttpError(403, "tool is not enabled for this deployment")
    try:
        result = invoke_tool(tool, arguments)
    except KeyError as exc:
        observe_mcp_tool(tool, "error", start)
        raise TriggerHttpError(404, str(exc)) from exc
    observe_mcp_tool(tool, "success", start)
    return json.dumps({"tool": tool, "result": result})
