"""Skill load and MCP tool steps (shared by trigger pipeline and supervisor tools)."""

from __future__ import annotations

import json
import time
from typing import Any

from agent.observability.middleware import (
    publish_skill_load_completed,
    publish_skill_load_failed,
    publish_tool_call_completed,
    publish_tool_call_failed,
)
from agent.o11y_logging import get_logger
from agent.observability.run_context import get_run_id, get_thread_id
from agent.observability.span_summaries import (
    ToolSpanSummary,
    redacted_args_hash,
)
from agent.observability.stores import get_span_summary_store
from agent.observability.trajectory import trajectory_recorder
from agent.run_context import next_tool_call_id
from agent.runtime_config import RuntimeConfig
from agent.skills_state import unlock_tools, unlocked_tools
from agent.tools.dispatch import invoke_tool
from agent.trigger_errors import TriggerHttpError


def run_skill_load_json(cfg: RuntimeConfig, name: str) -> str:
    start = time.perf_counter()
    entry = next((s for s in cfg.skills if str(s.get("name")) == name), None)
    if entry is None:
        publish_skill_load_failed(skill=name, started_at=start)
        raise TriggerHttpError(404, "skill not found")
    raw_extra = entry.get("extraTools") or entry.get("extra_tools") or []
    extra = [str(x) for x in raw_extra] if isinstance(raw_extra, list) else []
    unlock_tools(extra)
    prompt = str(entry.get("prompt") or "")
    publish_skill_load_completed(skill=name, started_at=start)
    return json.dumps({"name": name, "prompt": prompt, "activated_tools": extra})


def run_tool_json(cfg: RuntimeConfig, tool: str, arguments: dict[str, Any]) -> str:
    tool_call_id = next_tool_call_id()
    start = time.perf_counter()
    get_logger().debug(
        "mcp_tool_invoke",
        tool=tool,
        tool_call_id=tool_call_id,
    )
    allowed = set(cfg.enabled_mcp_tools) | set(unlocked_tools())
    if tool not in allowed:
        publish_tool_call_failed(tool=tool, started_at=start)
        raise TriggerHttpError(403, "tool is not enabled for this deployment")
    try:
        result = invoke_tool(tool, arguments)
    except KeyError as exc:
        publish_tool_call_failed(tool=tool, started_at=start)
        raise TriggerHttpError(404, str(exc)) from exc
    ok = True
    if isinstance(result, dict) and result.get("ok") is False:
        ok = False
    duration = time.perf_counter() - start
    publish_tool_call_completed(
        tool=tool,
        started_at=start,
        ok=ok,
        tool_call_id=tool_call_id,
        duration_s=duration,
    )
    run_id = get_run_id()
    if run_id:
        trajectory_recorder.append(
            run_id,
            "tool",
            {
                "tool": tool,
                "tool_call_id": tool_call_id,
                "arguments": arguments,
                "result": result,
            },
        )
        get_span_summary_store().record(
            ToolSpanSummary(
                tool_call_id=tool_call_id,
                run_id=run_id,
                thread_id=get_thread_id() or "",
                tool_name=tool,
                duration_ms=max(0, int(duration * 1000)),
                outcome="success",
                args_hash=redacted_args_hash(arguments),
            )
        )
    return json.dumps({"tool": tool, "result": result})
