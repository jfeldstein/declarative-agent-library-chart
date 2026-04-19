"""Subscribe lifecycle events and mirror legacy ``dalc_*`` Prometheus metrics."""

from __future__ import annotations

from typing import Any

from agent import metrics as legacy_metrics
from agent.rag.metrics import observe_rag_embed as rag_observe_embed
from agent.rag.metrics import observe_rag_query as rag_observe_query
from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.trigger_context import TriggerContext


def register_agent_legacy_metrics(bus: SyncEventBus) -> None:
    """Wire event bus to existing :mod:`agent.metrics` observe_* functions (Phase 1 shim)."""

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


def _on_trigger_responded(event: LifecycleEvent) -> None:
    p = event.payload
    trigger = str(p.get("trigger") or "")
    if trigger == "http":
        legacy_metrics.observe_http_trigger(
            str(p.get("http_result") or "success"),
            float(p["started_at"]),
        )
        rb = int(p.get("request_bytes") or 0)
        rsp = p.get("response_bytes")
        legacy_metrics.observe_trigger_http_payloads(
            rb, int(rsp) if rsp is not None else None
        )
        return
    if trigger == "slack":
        legacy_metrics.observe_slack_trigger_inbound(
            str(p.get("transport") or "http"),
            str(p.get("outcome") or "ignored"),
        )
        return
    if trigger == "jira":
        legacy_metrics.observe_jira_trigger_inbound(
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
    legacy_metrics.observe_mcp_tool(tool, _tool_result_label(ok), started_at)
    method = p.get("slack_web_api_method")
    if isinstance(method, str) and method.strip():
        legacy_metrics.observe_slack_tool_api(
            method.strip(),
            _tool_result_label(ok),
            started_at,
        )


def _on_tool_call_failed(event: LifecycleEvent) -> None:
    p = event.payload
    tool = str(p["tool"])
    started_at = float(p["started_at"])
    legacy_metrics.observe_mcp_tool(tool, "error", started_at)
    method = p.get("slack_web_api_method")
    if isinstance(method, str) and method.strip():
        legacy_metrics.observe_slack_tool_api(method.strip(), "error", started_at)


def _on_skill_completed(event: LifecycleEvent) -> None:
    p = event.payload
    legacy_metrics.observe_skill_load(
        str(p["skill"]),
        "success",
        float(p["started_at"]),
    )


def _on_skill_failed(event: LifecycleEvent) -> None:
    p = event.payload
    legacy_metrics.observe_skill_load(
        str(p["skill"]),
        "error",
        float(p["started_at"]),
    )


def _on_subagent_completed(event: LifecycleEvent) -> None:
    p = event.payload
    legacy_metrics.observe_subagent(
        str(p["subagent"]),
        "success",
        float(p["started_at"]),
    )


def _on_subagent_failed(event: LifecycleEvent) -> None:
    p = event.payload
    legacy_metrics.observe_subagent(
        str(p["subagent"]),
        "error",
        float(p["started_at"]),
    )


def _on_llm_first_token(event: LifecycleEvent) -> None:
    p = event.payload
    ctx = p["ctx"]
    if not isinstance(ctx, TriggerContext):
        return
    legacy_metrics.observe_llm_time_to_first_token(
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
    legacy_metrics.observe_llm_completion_metrics(
        ctx,
        input_tokens=p.get("input_tokens"),
        output_tokens=p.get("output_tokens"),
        input_rate_usd=p.get("input_rate_usd"),
        output_rate_usd=p.get("output_rate_usd"),
        result=str(p.get("result") or "success"),
    )


def _on_rag_embed(event: LifecycleEvent) -> None:
    p = event.payload
    rag_observe_embed(str(p["result"]), float(p["elapsed_seconds"]))


def _on_rag_query(event: LifecycleEvent) -> None:
    p = event.payload
    rag_observe_query(str(p["result"]), float(p["elapsed_seconds"]))
