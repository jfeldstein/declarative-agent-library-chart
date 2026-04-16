"""Prometheus metrics for the hosted agent runtime (agent_runtime_* prefix).

Traceability: [DALC-REQ-TOKEN-MET-001] [DALC-REQ-TOKEN-MET-002] [DALC-REQ-TOKEN-MET-003]
[DALC-REQ-TOKEN-MET-004] [DALC-REQ-TOKEN-MET-005] [DALC-REQ-TOKEN-MET-006]
"""

from __future__ import annotations

import hashlib
import math
import os
import time
from typing import Literal

from prometheus_client import Counter, Histogram

from hosted_agents.trigger_context import TriggerContext

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

_TTFT_BUCKETS = (
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
    30.0,
    float("inf"),
)

_PAYLOAD_BUCKETS = (
    64.0,
    128.0,
    256.0,
    512.0,
    1024.0,
    2048.0,
    4096.0,
    8192.0,
    16384.0,
    32768.0,
    65536.0,
    131072.0,
    262144.0,
    float("inf"),
)


def _max_trigger_payload_bytes() -> int:
    """Upper clamp for trigger payload histograms (read per observation, not at import)."""
    raw = os.environ.get(
        "HOSTED_AGENT_METRICS_TRIGGER_PAYLOAD_MAX_BYTES", "262144"
    ).strip()
    try:
        n = int(raw)
    except ValueError:
        return 262_144
    return max(n, 1)


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

HTTP_TRIGGER_REQUEST_BYTES = Histogram(
    "agent_runtime_http_trigger_request_bytes",
    "Serialized POST /api/v1/trigger JSON body length in bytes (runtime-measured; large values clamped).",
    (),
    buckets=_PAYLOAD_BUCKETS,
)
HTTP_TRIGGER_RESPONSE_BYTES = Histogram(
    "agent_runtime_http_trigger_response_bytes",
    "Plain-text HTTP response body length in bytes for successful trigger responses (UTF-8 encoded size).",
    (),
    buckets=_PAYLOAD_BUCKETS,
)

LLM_INPUT_TOKENS = Counter(
    "agent_runtime_llm_input_tokens_total",
    "Provider-reported cumulative input (prompt) tokens for completed LLM generations.",
    ("agent_id", "model_id", "result"),
)
LLM_OUTPUT_TOKENS = Counter(
    "agent_runtime_llm_output_tokens_total",
    "Provider-reported cumulative output (completion) tokens for completed LLM generations.",
    ("agent_id", "model_id", "result"),
)
LLM_USAGE_MISSING = Counter(
    "agent_runtime_llm_usage_missing_total",
    "Count of LLM completions where provider-reported token usage was incomplete (input and/or output missing).",
    ("agent_id", "model_id", "result"),
)
LLM_TTFT = Histogram(
    "agent_runtime_llm_time_to_first_token_seconds",
    "Wall time from chat model start to first streamed output token, or full completion for non-streaming paths (provider-reported timing boundary via runtime).",
    ("agent_id", "model_id", "result", "streaming"),
    buckets=_TTFT_BUCKETS,
)
LLM_ESTIMATED_COST_USD = Counter(
    "agent_runtime_llm_estimated_cost_usd_total",
    "Runtime-estimated USD cost from provider-reported token counts and configured per-token rates (estimate only; not billing).",
    ("agent_id", "model_id", "result"),
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


def _clamp_payload_observation(n: int) -> float:
    if n < 0:
        n = 0
    if n > _max_trigger_payload_bytes():
        return float("inf")
    return float(n)


def observe_http_trigger(result: TriggerResult, start: float) -> None:
    dt = _elapsed(start)
    HTTP_TRIGGER_REQUESTS.labels(result=result).inc()
    HTTP_TRIGGER_DURATION.labels(result=result).observe(dt)


def observe_trigger_http_payloads(
    request_bytes: int,
    response_bytes: int | None,
) -> None:
    """Record trigger JSON request size; optional successful response body size in bytes."""
    HTTP_TRIGGER_REQUEST_BYTES.observe(_clamp_payload_observation(request_bytes))
    if response_bytes is not None:
        HTTP_TRIGGER_RESPONSE_BYTES.observe(_clamp_payload_observation(response_bytes))


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


def _first_env(*keys: str) -> str | None:
    for k in keys:
        v = os.environ.get(k, "").strip()
        if v:
            return v
    return None


def tagify_metric_label(value: str, max_len: int = 64) -> str:
    """Bound label values: short strings pass through; long values are hashed."""
    v = value.strip()
    if not v:
        return "unknown"
    if len(v) <= max_len:
        return v
    digest = hashlib.sha256(v.encode()).hexdigest()[:12]
    return f"h_{digest}"


def llm_metric_label_values(_ctx: TriggerContext, *, result: str) -> dict[str, str]:
    """Bounded labels for LLM metrics (agent_id, model_id, result)."""
    agent_raw = _first_env("HOSTED_AGENT_ID", "HOSTED_AGENT_AGENT_ID") or "unknown"
    model_raw = (
        _first_env("HOSTED_AGENT_CHAT_MODEL", "HOSTED_AGENT_MODEL_ID") or "unknown"
    )
    res = result if result in ("success", "error") else "success"
    return {
        "agent_id": tagify_metric_label(agent_raw),
        "model_id": tagify_metric_label(model_raw),
        "result": res,
    }


def _metric_labels_from_ctx(ctx: TriggerContext, *, result: str) -> dict[str, str]:
    return llm_metric_label_values(ctx, result=result)


def observe_llm_time_to_first_token(
    ctx: TriggerContext,
    seconds: float,
    *,
    streaming_label: str,
    result: str,
) -> None:
    labels = _metric_labels_from_ctx(ctx, result=result)
    LLM_TTFT.labels(
        agent_id=labels["agent_id"],
        model_id=labels["model_id"],
        result=labels["result"],
        streaming=streaming_label,
    ).observe(max(seconds, 0.0))


def observe_llm_completion_metrics(
    ctx: TriggerContext,
    *,
    input_tokens: int | None,
    output_tokens: int | None,
    input_rate_usd: float | None,
    output_rate_usd: float | None,
    result: str,
) -> None:
    """Increment token counters, missing usage, and optional estimated cost."""
    labels = _metric_labels_from_ctx(ctx, result=result)
    lbl = (
        labels["agent_id"],
        labels["model_id"],
        labels["result"],
    )
    missing = input_tokens is None or output_tokens is None
    if missing:
        LLM_USAGE_MISSING.labels(*lbl).inc()
    if input_tokens is not None:
        LLM_INPUT_TOKENS.labels(*lbl).inc(input_tokens)
    if output_tokens is not None:
        LLM_OUTPUT_TOKENS.labels(*lbl).inc(output_tokens)

    if (
        input_rate_usd is not None
        and output_rate_usd is not None
        and input_tokens is not None
        and output_tokens is not None
    ):
        delta = input_tokens * input_rate_usd + output_tokens * output_rate_usd
        if math.isfinite(delta) and delta >= 0:
            LLM_ESTIMATED_COST_USD.labels(*lbl).inc(delta)
