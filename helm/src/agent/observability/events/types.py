"""Vendor-agnostic lifecycle event names (OpenSpec contract; Phase 1).

Plugins subscribe to these names; legacy Prometheus instrumentation mirrors them until Phase 2.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum
from typing import Any, Mapping


class EventName(StrEnum):
    """Stable event identifiers published by instrumentation middleware."""

    RUN_STARTED = "run.started"
    RUN_ENDED = "run.ended"

    TRIGGER_REQUEST_RECEIVED = "trigger.request.received"
    TRIGGER_REQUEST_RESPONDED = "trigger.request.responded"
    TRIGGER_REQUEST_FAILED = "trigger.request.failed"

    LLM_GENERATION_STARTED = "llm.generation.started"
    LLM_GENERATION_FIRST_TOKEN = "llm.generation.first_token"
    LLM_GENERATION_COMPLETED = "llm.generation.completed"
    LLM_GENERATION_FAILED = "llm.generation.failed"

    TOOL_CALL_STARTED = "tool.call.started"
    TOOL_CALL_COMPLETED = "tool.call.completed"
    TOOL_CALL_FAILED = "tool.call.failed"

    SUBAGENT_INVOCATION_STARTED = "subagent.invocation.started"
    SUBAGENT_INVOCATION_COMPLETED = "subagent.invocation.completed"
    SUBAGENT_INVOCATION_FAILED = "subagent.invocation.failed"

    SKILL_LOAD_STARTED = "skill.load.started"
    SKILL_LOAD_COMPLETED = "skill.load.completed"
    SKILL_LOAD_FAILED = "skill.load.failed"

    RAG_EMBED_COMPLETED = "rag.embed.completed"
    RAG_QUERY_COMPLETED = "rag.query.completed"

    SCRAPER_RUN_COMPLETED = "scraper.run.completed"
    SCRAPER_RAG_EMBED_ATTEMPT = "scraper.rag.embed.attempt"

    FEEDBACK_RECORDED = "feedback.recorded"


class LifecycleEvent:
    """Single published unit on the lifecycle bus."""

    __slots__ = ("name", "payload", "occurred_at")

    def __init__(
        self,
        name: EventName,
        payload: Mapping[str, Any],
        *,
        occurred_at: datetime | None = None,
    ) -> None:
        self.name = name
        self.payload = payload
        self.occurred_at = occurred_at or datetime.now(timezone.utc)
