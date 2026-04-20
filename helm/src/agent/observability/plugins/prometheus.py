"""Prometheus exposition via ``dalc_*`` metrics subscribed to :class:`~agent.observability.events.SyncEventBus`.

Traceability: [DALC-REQ-O11Y-SCRAPE-001] [DALC-REQ-O11Y-SCRAPE-002] [DALC-REQ-O11Y-SCRAPE-003] [DALC-REQ-TOKEN-MET-001]
[DALC-REQ-TOKEN-MET-002] [DALC-REQ-TOKEN-MET-003] [DALC-REQ-TOKEN-MET-004]
[DALC-REQ-TOKEN-MET-005] [DALC-REQ-TOKEN-MET-006] [DALC-REQ-SLACK-TOOLS-006]
[DALC-REQ-SLACK-TRIGGER-005] [DALC-REQ-JIRA-TRIGGER-005]
"""

from __future__ import annotations

import math
import os
import time
from typing import Any

from prometheus_client import Counter, Histogram

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.observability.metric_semantics import BinaryResult, TriggerResult
from agent.trigger_context import TriggerContext

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

DALC_TRIGGER_REQUESTS = Counter(
    "dalc_trigger_requests_total",
    "Inbound trigger handling outcomes (trigger axis replaces legacy per-bridge counters).",
    ("trigger", "transport", "result"),
)
DALC_TRIGGER_DURATION = Histogram(
    "dalc_trigger_duration_seconds",
    "Latency of inbound trigger handling.",
    ("trigger", "transport", "result"),
    buckets=_DURATION_BUCKETS,
)

DALC_TRIGGER_REQUEST_BYTES = Histogram(
    "dalc_trigger_request_bytes",
    "Serialized POST /api/v1/trigger JSON body length (HTTP trigger path).",
    (),
    buckets=_PAYLOAD_BUCKETS,
)
DALC_TRIGGER_RESPONSE_BYTES = Histogram(
    "dalc_trigger_response_bytes",
    "Plain-text HTTP response body length for successful HTTP trigger responses.",
    (),
    buckets=_PAYLOAD_BUCKETS,
)

DALC_LLM_INPUT_TOKENS = Counter(
    "dalc_llm_input_tokens_total",
    "Provider-reported cumulative input tokens for completed LLM generations.",
    ("agent_id", "model_id", "result"),
)
DALC_LLM_OUTPUT_TOKENS = Counter(
    "dalc_llm_output_tokens_total",
    "Provider-reported cumulative output tokens for completed LLM generations.",
    ("agent_id", "model_id", "result"),
)
DALC_LLM_USAGE_MISSING = Counter(
    "dalc_llm_usage_missing_total",
    "LLM completions where provider-reported token usage was incomplete.",
    ("agent_id", "model_id", "result"),
)
DALC_LLM_TTFT = Histogram(
    "dalc_llm_time_to_first_token_seconds",
    "Wall time from chat model start to first streamed output token.",
    ("agent_id", "model_id", "result", "streaming"),
    buckets=_TTFT_BUCKETS,
)
DALC_LLM_ESTIMATED_COST_USD = Counter(
    "dalc_llm_estimated_cost_usd_total",
    "Runtime-estimated USD cost from provider tokens (estimate only; not billing).",
    ("agent_id", "model_id", "result"),
)

DALC_TOOL_CALLS = Counter(
    "dalc_tool_calls_total",
    "Tool invocations (label-driven tool id).",
    ("tool", "result"),
)
DALC_TOOL_DURATION = Histogram(
    "dalc_tool_duration_seconds",
    "Latency of tool invocations.",
    ("tool", "result"),
    buckets=_DURATION_BUCKETS,
)

DALC_SUBAGENT_INVOCATIONS = Counter(
    "dalc_subagent_invocations_total",
    "Subagent invocations.",
    ("subagent", "result"),
)
DALC_SUBAGENT_DURATION = Histogram(
    "dalc_subagent_duration_seconds",
    "Latency of subagent invocations.",
    ("subagent", "result"),
    buckets=_DURATION_BUCKETS,
)

DALC_SKILL_LOADS = Counter(
    "dalc_skill_loads_total",
    "Skill load operations.",
    ("skill", "result"),
)
DALC_SKILL_LOAD_DURATION = Histogram(
    "dalc_skill_load_duration_seconds",
    "Latency of skill load operations.",
    ("skill", "result"),
    buckets=_DURATION_BUCKETS,
)

DALC_SLACK_TOOL_WEB_API_CALLS = Counter(
    "dalc_slack_tool_web_api_calls_total",
    "Slack Web API calls issued from LLM-time tools.",
    ("method", "result"),
)
DALC_SLACK_TOOL_WEB_API_DURATION = Histogram(
    "dalc_slack_tool_web_api_duration_seconds",
    "Latency of Slack Web API calls from LLM-time tools.",
    ("method", "result"),
    buckets=_DURATION_BUCKETS,
)


def _elapsed(start: float) -> float:
    return max(time.perf_counter() - start, 0.0)


def _max_trigger_payload_bytes() -> int:
    raw = os.environ.get(
        "HOSTED_AGENT_METRICS_TRIGGER_PAYLOAD_MAX_BYTES", "262144"
    ).strip()
    try:
        n = int(raw)
    except ValueError:
        return 262_144
    return max(n, 1)


def _clamp_payload_observation(n: int) -> float:
    if n < 0:
        n = 0
    if n > _max_trigger_payload_bytes():
        return float("inf")
    return float(n)


def _first_env(*keys: str) -> str | None:
    for k in keys:
        v = os.environ.get(k, "").strip()
        if v:
            return v
    return None


def tagify_metric_label(value: str, max_len: int = 64) -> str:
    """Bound label values: short strings pass through; long values are hashed."""
    import hashlib

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


def observe_http_trigger(result: TriggerResult, start: float) -> None:
    dt = _elapsed(start)
    DALC_TRIGGER_REQUESTS.labels(trigger="http", transport="http", result=result).inc()
    DALC_TRIGGER_DURATION.labels(
        trigger="http", transport="http", result=result
    ).observe(dt)


def observe_trigger_http_payloads(
    request_bytes: int,
    response_bytes: int | None,
) -> None:
    DALC_TRIGGER_REQUEST_BYTES.observe(_clamp_payload_observation(request_bytes))
    if response_bytes is not None:
        DALC_TRIGGER_RESPONSE_BYTES.observe(
            _clamp_payload_observation(response_bytes),
        )


def observe_mcp_tool(tool: str, result: BinaryResult, start: float) -> None:
    dt = _elapsed(start)
    DALC_TOOL_CALLS.labels(tool=tool, result=result).inc()
    DALC_TOOL_DURATION.labels(tool=tool, result=result).observe(dt)


def observe_subagent(subagent: str, result: BinaryResult, start: float) -> None:
    dt = _elapsed(start)
    DALC_SUBAGENT_INVOCATIONS.labels(subagent=subagent, result=result).inc()
    DALC_SUBAGENT_DURATION.labels(subagent=subagent, result=result).observe(dt)


def observe_skill_load(skill: str, result: BinaryResult, start: float) -> None:
    dt = _elapsed(start)
    DALC_SKILL_LOADS.labels(skill=skill, result=result).inc()
    DALC_SKILL_LOAD_DURATION.labels(skill=skill, result=result).observe(dt)


def observe_slack_tool_api(
    method: str, result: BinaryResult, start: float | None = None
) -> None:
    dt = _elapsed(start) if start is not None else 0.0
    DALC_SLACK_TOOL_WEB_API_CALLS.labels(method=method, result=result).inc()
    if start is not None:
        DALC_SLACK_TOOL_WEB_API_DURATION.labels(method=method, result=result).observe(
            dt,
        )


def observe_slack_trigger_inbound(transport: str, result: str) -> None:
    DALC_TRIGGER_REQUESTS.labels(
        trigger="slack", transport=transport, result=result
    ).inc()


def observe_jira_trigger_inbound(transport: str, result: str) -> None:
    DALC_TRIGGER_REQUESTS.labels(
        trigger="jira", transport=transport, result=result
    ).inc()


def observe_llm_time_to_first_token(
    ctx: TriggerContext,
    seconds: float,
    *,
    streaming_label: str,
    result: str,
) -> None:
    labels = _metric_labels_from_ctx(ctx, result=result)
    DALC_LLM_TTFT.labels(
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
    labels = _metric_labels_from_ctx(ctx, result=result)
    lbl = (
        labels["agent_id"],
        labels["model_id"],
        labels["result"],
    )
    missing = input_tokens is None or output_tokens is None
    if missing:
        DALC_LLM_USAGE_MISSING.labels(*lbl).inc()
    if input_tokens is not None:
        DALC_LLM_INPUT_TOKENS.labels(*lbl).inc(input_tokens)
    if output_tokens is not None:
        DALC_LLM_OUTPUT_TOKENS.labels(*lbl).inc(output_tokens)

    if (
        input_rate_usd is not None
        and output_rate_usd is not None
        and input_tokens is not None
        and output_tokens is not None
    ):
        delta = input_tokens * input_rate_usd + output_tokens * output_rate_usd
        if math.isfinite(delta) and delta >= 0:
            DALC_LLM_ESTIMATED_COST_USD.labels(*lbl).inc(delta)


def register_prometheus_agent_plugin(bus: SyncEventBus) -> None:
    """Subscribe agent-process lifecycle events and record ``dalc_*`` metrics."""

    bus.subscribe(EventName.TRIGGER_REQUEST_RESPONDED, _on_trigger_responded)
    bus.subscribe(EventName.TOOL_CALL_COMPLETED, _on_tool_call_completed)
    bus.subscribe(EventName.TOOL_CALL_FAILED, _on_tool_call_failed)
    bus.subscribe(EventName.SKILL_LOAD_COMPLETED, _on_skill_completed)
    bus.subscribe(EventName.SKILL_LOAD_FAILED, _on_skill_failed)
    bus.subscribe(EventName.SUBAGENT_INVOCATION_COMPLETED, _on_subagent_completed)
    bus.subscribe(EventName.SUBAGENT_INVOCATION_FAILED, _on_subagent_failed)
    bus.subscribe(EventName.LLM_GENERATION_FIRST_TOKEN, _on_llm_first_token)
    bus.subscribe(EventName.LLM_GENERATION_COMPLETED, _on_llm_completed)
    bus.subscribe(EventName.RAG_EMBED_COMPLETED, _on_rag_embed)
    bus.subscribe(EventName.RAG_QUERY_COMPLETED, _on_rag_query)


def register_prometheus_scraper_plugin(bus: SyncEventBus) -> None:
    """Subscribe scraper CronJob lifecycle events and record scraper ``dalc_*`` metrics."""

    bus.subscribe(EventName.SCRAPER_RUN_COMPLETED, _on_scraper_run)
    bus.subscribe(EventName.SCRAPER_RAG_EMBED_ATTEMPT, _on_rag_embed_attempt)


def _on_trigger_responded(event: LifecycleEvent) -> None:
    p = event.payload
    trigger = str(p.get("trigger") or "")
    if trigger == "http":
        observe_http_trigger(
            str(p.get("http_result") or "success"),
            float(p["started_at"]),
        )
        rb = int(p.get("request_bytes") or 0)
        rsp = p.get("response_bytes")
        observe_trigger_http_payloads(rb, int(rsp) if rsp is not None else None)
        return
    if trigger == "slack":
        observe_slack_trigger_inbound(
            str(p.get("transport") or "http"),
            str(p.get("outcome") or "ignored"),
        )
        return
    if trigger == "jira":
        observe_jira_trigger_inbound(
            str(p.get("transport") or "http"),
            str(p.get("outcome") or "ignored"),
        )


def _tool_result_label(ok: Any) -> str:
    return "success" if ok else "error"


def _on_tool_call_completed(event: LifecycleEvent) -> None:
    p = event.payload
    tool = str(p["tool"])
    started_at = float(p["started_at"])
    ok = bool(p.get("ok", True))
    observe_mcp_tool(tool, _tool_result_label(ok), started_at)


def _on_tool_call_failed(event: LifecycleEvent) -> None:
    p = event.payload
    tool = str(p["tool"])
    started_at = float(p["started_at"])
    observe_mcp_tool(tool, "error", started_at)


def _on_skill_completed(event: LifecycleEvent) -> None:
    p = event.payload
    observe_skill_load(
        str(p["skill"]),
        "success",
        float(p["started_at"]),
    )


def _on_skill_failed(event: LifecycleEvent) -> None:
    p = event.payload
    observe_skill_load(
        str(p["skill"]),
        "error",
        float(p["started_at"]),
    )


def _on_subagent_completed(event: LifecycleEvent) -> None:
    p = event.payload
    observe_subagent(
        str(p["subagent"]),
        "success",
        float(p["started_at"]),
    )


def _on_subagent_failed(event: LifecycleEvent) -> None:
    p = event.payload
    observe_subagent(
        str(p["subagent"]),
        "error",
        float(p["started_at"]),
    )


def _on_llm_first_token(event: LifecycleEvent) -> None:
    p = event.payload
    ctx = p["ctx"]
    if not isinstance(ctx, TriggerContext):
        return
    observe_llm_time_to_first_token(
        ctx,
        float(p["seconds"]),
        streaming_label=str(p.get("streaming_label") or "false"),
        result=str(p.get("result") or "success"),
    )


def _on_llm_completed(event: LifecycleEvent) -> None:
    p = event.payload
    ctx = p["ctx"]
    if not isinstance(ctx, TriggerContext):
        return
    observe_llm_completion_metrics(
        ctx,
        input_tokens=p.get("input_tokens"),
        output_tokens=p.get("output_tokens"),
        input_rate_usd=p.get("input_rate_usd"),
        output_rate_usd=p.get("output_rate_usd"),
        result=str(p.get("result") or "success"),
    )


def _on_rag_embed(event: LifecycleEvent) -> None:
    from agent.rag.metrics import observe_rag_embed as rag_observe_embed

    p = event.payload
    rag_observe_embed(str(p["result"]), float(p["elapsed_seconds"]))


def _on_rag_query(event: LifecycleEvent) -> None:
    from agent.rag.metrics import observe_rag_query as rag_observe_query

    p = event.payload
    rag_observe_query(str(p["result"]), float(p["elapsed_seconds"]))


def _on_scraper_run(event: LifecycleEvent) -> None:
    from agent.scrapers.metrics import observe_scraper_run

    p = event.payload
    observe_scraper_run(
        str(p["integration"]),
        bool(p.get("success")),
        float(p["elapsed_seconds"]),
    )


def _on_rag_embed_attempt(event: LifecycleEvent) -> None:
    from agent.scrapers.metrics import observe_rag_embed_attempt

    p = event.payload
    observe_rag_embed_attempt(str(p["integration"]), str(p["result"]))
