"""Prometheus metrics for the hosted agent runtime (agent_runtime_* prefix)."""

from __future__ import annotations

import time
from typing import Literal

from prometheus_client import Counter, Histogram

_DURATION_BUCKETS = (
    0.001,
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    float("inf"),
)

TriggerResult = Literal["success", "client_error", "server_error"]
BinaryResult = Literal["success", "error"]

HTTP_TRIGGER_REQUESTS = Counter(
    "agent_runtime_http_trigger_requests_total",
    "Count of POST /api/v1/trigger invocations",
    ("result",),
)
HTTP_TRIGGER_DURATION = Histogram(
    "agent_runtime_http_trigger_duration_seconds",
    "Latency of POST /api/v1/trigger handling",
    ("result",),
    buckets=_DURATION_BUCKETS,
)

MCP_TOOL_CALLS = Counter(
    "agent_runtime_mcp_tool_calls_total",
    "Count of MCP-style tool invocations",
    ("tool", "result"),
)
MCP_TOOL_DURATION = Histogram(
    "agent_runtime_mcp_tool_duration_seconds",
    "Latency of MCP-style tool invocations",
    ("tool", "result"),
    buckets=_DURATION_BUCKETS,
)

SUBAGENT_INVOCATIONS = Counter(
    "agent_runtime_subagent_invocations_total",
    "Count of subagent invocations",
    ("subagent", "result"),
)
SUBAGENT_DURATION = Histogram(
    "agent_runtime_subagent_duration_seconds",
    "Latency of subagent invocations",
    ("subagent", "result"),
    buckets=_DURATION_BUCKETS,
)

SKILL_LOADS = Counter(
    "agent_runtime_skill_loads_total",
    "Count of skill load operations",
    ("skill", "result"),
)
SKILL_LOAD_DURATION = Histogram(
    "agent_runtime_skill_load_duration_seconds",
    "Latency of skill load operations",
    ("skill", "result"),
    buckets=_DURATION_BUCKETS,
)


def _elapsed(start: float) -> float:
    return max(time.perf_counter() - start, 0.0)


def observe_http_trigger(result: TriggerResult, start: float) -> None:
    dt = _elapsed(start)
    HTTP_TRIGGER_REQUESTS.labels(result=result).inc()
    HTTP_TRIGGER_DURATION.labels(result=result).observe(dt)


def observe_mcp_tool(tool: str, result: BinaryResult, start: float) -> None:
    dt = _elapsed(start)
    MCP_TOOL_CALLS.labels(tool=tool, result=result).inc()
    MCP_TOOL_DURATION.labels(tool=tool, result=result).observe(dt)


def observe_subagent(subagent: str, result: BinaryResult, start: float) -> None:
    dt = _elapsed(start)
    SUBAGENT_INVOCATIONS.labels(subagent=subagent, result=result).inc()
    SUBAGENT_DURATION.labels(subagent=subagent, result=result).observe(dt)


def observe_skill_load(skill: str, result: BinaryResult, start: float) -> None:
    dt = _elapsed(start)
    SKILL_LOADS.labels(skill=skill, result=result).inc()
    SKILL_LOAD_DURATION.labels(skill=skill, result=result).observe(dt)
