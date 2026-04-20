"""Instrumentation helpers — publish lifecycle events (legacy metrics subscribe in Phase 1)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast

from agent.observability.bootstrap import agent_event_bus
from agent.observability.events import SyncEventBus
from agent.observability.events.payloads import (
    FeedbackRecordedPayload,
    RunStartedPayload,
    ToolCallCompletedPayload,
    ToolCallFailedPayload,
)
from agent.observability.events.types import (
    EventName,
    FeedbackRecordedLifecycleEvent,
    LlmGenerationCompletedLifecycleEvent,
    LlmGenerationFirstTokenLifecycleEvent,
    RagEmbedCompletedLifecycleEvent,
    RagQueryCompletedLifecycleEvent,
    RunEndedLifecycleEvent,
    RunStartedLifecycleEvent,
    ScraperRagEmbedAttemptLifecycleEvent,
    ScraperRunCompletedLifecycleEvent,
    SkillLoadCompletedLifecycleEvent,
    SkillLoadFailedLifecycleEvent,
    SubagentInvocationCompletedLifecycleEvent,
    SubagentInvocationFailedLifecycleEvent,
    ToolCallCompletedLifecycleEvent,
    ToolCallFailedLifecycleEvent,
    TriggerRequestRespondedLifecycleEvent,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def publish_run_started(
    *,
    run_id: str,
    thread_id: str,
    run_identity: dict[str, str],
    request_correlation_id: str,
    observability: Any,
    bus: SyncEventBus | None = None,
) -> None:
    """Emit when a trigger run begins (LangGraph invoke wrapper)."""

    b = bus or agent_event_bus()
    payload: RunStartedPayload = {
        "run_id": run_id,
        "run_name": run_id,
        "thread_id": thread_id,
        "run_identity": dict(run_identity),
        "request_correlation_id": request_correlation_id,
        "observability": observability,
    }
    b.publish(
        RunStartedLifecycleEvent(
            name=EventName.RUN_STARTED,
            payload=payload,
            occurred_at=_utc_now(),
        )
    )


def publish_run_ended(*, bus: SyncEventBus | None = None) -> None:
    """Emit when a trigger run completes (paired with :func:`publish_run_started`)."""

    b = bus or agent_event_bus()
    b.publish(
        RunEndedLifecycleEvent(
            name=EventName.RUN_ENDED,
            payload={},
            occurred_at=_utc_now(),
        )
    )


def publish_feedback_recorded(
    *,
    observability_settings: Any,
    run_id: str,
    thread_id: str,
    run_identity: dict[str, str],
    tool_call_id: str,
    checkpoint_id: str | None,
    feedback_label: str,
    feedback_source: str,
    request_correlation_id: str | None = None,
    feedback_scalar: int | None = None,
    bus: SyncEventBus | None = None,
) -> None:
    """Emit after durable human feedback is recorded (Slack reactions, API, …)."""

    b = bus or agent_event_bus()
    fb: FeedbackRecordedPayload = {
        "observability_settings": observability_settings,
        "run_id": run_id,
        "thread_id": thread_id,
        "run_identity": dict(run_identity),
        "tool_call_id": tool_call_id,
        "checkpoint_id": checkpoint_id,
        "feedback_label": feedback_label,
        "feedback_source": feedback_source,
    }
    if request_correlation_id is not None:
        fb["request_correlation_id"] = request_correlation_id
    if feedback_scalar is not None:
        fb["feedback_scalar"] = feedback_scalar
    b.publish(
        FeedbackRecordedLifecycleEvent(
            name=EventName.FEEDBACK_RECORDED,
            payload=fb,
            occurred_at=_utc_now(),
        )
    )


def publish_http_trigger_response(
    *,
    http_result: str,
    started_at: float,
    request_bytes: int,
    response_bytes: int | None,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        TriggerRequestRespondedLifecycleEvent(
            name=EventName.TRIGGER_REQUEST_RESPONDED,
            payload={
                "trigger": "http",
                "http_result": http_result,
                "started_at": started_at,
                "request_bytes": request_bytes,
                "response_bytes": response_bytes,
            },
            occurred_at=_utc_now(),
        )
    )


def publish_slack_trigger_inbound(
    *,
    transport: str,
    outcome: str,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        TriggerRequestRespondedLifecycleEvent(
            name=EventName.TRIGGER_REQUEST_RESPONDED,
            payload={
                "trigger": "slack",
                "transport": transport,
                "outcome": outcome,
            },
            occurred_at=_utc_now(),
        )
    )


def publish_jira_trigger_inbound(
    *,
    transport: str,
    outcome: str,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        TriggerRequestRespondedLifecycleEvent(
            name=EventName.TRIGGER_REQUEST_RESPONDED,
            payload={
                "trigger": "jira",
                "transport": transport,
                "outcome": outcome,
            },
            occurred_at=_utc_now(),
        )
    )


def publish_tool_call_completed(
    *,
    tool: str,
    started_at: float,
    ok: bool,
    tool_call_id: str | None = None,
    duration_s: float | None = None,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    payload: dict[str, Any] = {
        "tool": tool,
        "started_at": started_at,
        "ok": ok,
    }
    if tool_call_id is not None:
        payload["tool_call_id"] = tool_call_id
    if duration_s is not None:
        payload["duration_s"] = duration_s
    b.publish(
        ToolCallCompletedLifecycleEvent(
            name=EventName.TOOL_CALL_COMPLETED,
            payload=cast(ToolCallCompletedPayload, payload),
            occurred_at=_utc_now(),
        )
    )


def publish_tool_call_failed(
    *,
    tool: str,
    started_at: float,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        ToolCallFailedLifecycleEvent(
            name=EventName.TOOL_CALL_FAILED,
            payload=cast(
                ToolCallFailedPayload,
                {"tool": tool, "started_at": started_at},
            ),
            occurred_at=_utc_now(),
        )
    )


def publish_skill_load_completed(
    *,
    skill: str,
    started_at: float,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        SkillLoadCompletedLifecycleEvent(
            name=EventName.SKILL_LOAD_COMPLETED,
            payload={"skill": skill, "started_at": started_at},
            occurred_at=_utc_now(),
        )
    )


def publish_skill_load_failed(
    *,
    skill: str,
    started_at: float,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        SkillLoadFailedLifecycleEvent(
            name=EventName.SKILL_LOAD_FAILED,
            payload={"skill": skill, "started_at": started_at},
            occurred_at=_utc_now(),
        )
    )


def publish_subagent_completed(
    *,
    subagent: str,
    started_at: float,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        SubagentInvocationCompletedLifecycleEvent(
            name=EventName.SUBAGENT_INVOCATION_COMPLETED,
            payload={"subagent": subagent, "started_at": started_at},
            occurred_at=_utc_now(),
        )
    )


def publish_subagent_failed(
    *,
    subagent: str,
    started_at: float,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        SubagentInvocationFailedLifecycleEvent(
            name=EventName.SUBAGENT_INVOCATION_FAILED,
            payload={"subagent": subagent, "started_at": started_at},
            occurred_at=_utc_now(),
        )
    )


def publish_llm_first_token(
    *,
    ctx: Any,
    seconds: float,
    streaming_label: str,
    result: str,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        LlmGenerationFirstTokenLifecycleEvent(
            name=EventName.LLM_GENERATION_FIRST_TOKEN,
            payload={
                "ctx": ctx,
                "seconds": seconds,
                "streaming_label": streaming_label,
                "result": result,
            },
            occurred_at=_utc_now(),
        )
    )


def publish_llm_generation_completed(
    *,
    ctx: Any,
    input_tokens: int | None,
    output_tokens: int | None,
    input_rate_usd: float | None,
    output_rate_usd: float | None,
    result: str,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        LlmGenerationCompletedLifecycleEvent(
            name=EventName.LLM_GENERATION_COMPLETED,
            payload={
                "ctx": ctx,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "input_rate_usd": input_rate_usd,
                "output_rate_usd": output_rate_usd,
                "result": result,
            },
            occurred_at=_utc_now(),
        )
    )


def publish_rag_embed_completed(
    *,
    result: str,
    elapsed_seconds: float,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        RagEmbedCompletedLifecycleEvent(
            name=EventName.RAG_EMBED_COMPLETED,
            payload={"result": result, "elapsed_seconds": elapsed_seconds},
            occurred_at=_utc_now(),
        )
    )


def publish_rag_query_completed(
    *,
    result: str,
    elapsed_seconds: float,
    bus: SyncEventBus | None = None,
) -> None:
    b = bus or agent_event_bus()
    b.publish(
        RagQueryCompletedLifecycleEvent(
            name=EventName.RAG_QUERY_COMPLETED,
            payload={"result": result, "elapsed_seconds": elapsed_seconds},
            occurred_at=_utc_now(),
        )
    )


def publish_scraper_run_completed(
    *,
    integration: str,
    success: bool,
    elapsed_seconds: float,
    bus: SyncEventBus | None = None,
) -> None:
    from agent.observability.bootstrap import scraper_event_bus

    b = bus or scraper_event_bus()
    b.publish(
        ScraperRunCompletedLifecycleEvent(
            name=EventName.SCRAPER_RUN_COMPLETED,
            payload={
                "integration": integration,
                "success": success,
                "elapsed_seconds": elapsed_seconds,
            },
            occurred_at=_utc_now(),
        )
    )


def publish_scraper_rag_embed_attempt(
    *,
    integration: str,
    result: str,
    bus: SyncEventBus | None = None,
) -> None:
    from agent.observability.bootstrap import scraper_event_bus

    b = bus or scraper_event_bus()
    b.publish(
        ScraperRagEmbedAttemptLifecycleEvent(
            name=EventName.SCRAPER_RAG_EMBED_ATTEMPT,
            payload={"integration": integration, "result": result},
            occurred_at=_utc_now(),
        )
    )
