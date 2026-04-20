"""Vendor-agnostic lifecycle event names and discriminated :class:`LifecycleEvent` subtypes."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Literal, TypeAlias

from .payloads import (
    FeedbackRecordedPayload,
    LlmGenerationCompletedPayload,
    LlmGenerationFirstTokenPayload,
    RagEmbedCompletedPayload,
    RagQueryCompletedPayload,
    ReservedLifecyclePayload,
    RunEndedPayload,
    RunStartedPayload,
    ScraperRagEmbedAttemptPayload,
    ScraperRunCompletedPayload,
    SkillLoadCompletedPayload,
    SkillLoadFailedPayload,
    SubagentInvocationCompletedPayload,
    SubagentInvocationFailedPayload,
    ToolCallCompletedPayload,
    ToolCallFailedPayload,
    TriggerRequestRespondedPayload,
)


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


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


@dataclass(frozen=True, slots=True, kw_only=True)
class LifecycleEventBase:
    """Shared fields for all published lifecycle events."""

    occurred_at: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True, slots=True, kw_only=True)
class RunStartedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.RUN_STARTED]
    payload: RunStartedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class RunEndedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.RUN_ENDED]
    payload: RunEndedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class TriggerRequestReceivedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.TRIGGER_REQUEST_RECEIVED]
    payload: ReservedLifecyclePayload


@dataclass(frozen=True, slots=True, kw_only=True)
class TriggerRequestRespondedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.TRIGGER_REQUEST_RESPONDED]
    payload: TriggerRequestRespondedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class TriggerRequestFailedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.TRIGGER_REQUEST_FAILED]
    payload: ReservedLifecyclePayload


@dataclass(frozen=True, slots=True, kw_only=True)
class LlmGenerationStartedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.LLM_GENERATION_STARTED]
    payload: ReservedLifecyclePayload


@dataclass(frozen=True, slots=True, kw_only=True)
class LlmGenerationFirstTokenLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.LLM_GENERATION_FIRST_TOKEN]
    payload: LlmGenerationFirstTokenPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class LlmGenerationCompletedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.LLM_GENERATION_COMPLETED]
    payload: LlmGenerationCompletedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class LlmGenerationFailedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.LLM_GENERATION_FAILED]
    payload: ReservedLifecyclePayload


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolCallStartedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.TOOL_CALL_STARTED]
    payload: ReservedLifecyclePayload


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolCallCompletedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.TOOL_CALL_COMPLETED]
    payload: ToolCallCompletedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolCallFailedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.TOOL_CALL_FAILED]
    payload: ToolCallFailedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class SubagentInvocationStartedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.SUBAGENT_INVOCATION_STARTED]
    payload: ReservedLifecyclePayload


@dataclass(frozen=True, slots=True, kw_only=True)
class SubagentInvocationCompletedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.SUBAGENT_INVOCATION_COMPLETED]
    payload: SubagentInvocationCompletedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class SubagentInvocationFailedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.SUBAGENT_INVOCATION_FAILED]
    payload: SubagentInvocationFailedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillLoadStartedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.SKILL_LOAD_STARTED]
    payload: ReservedLifecyclePayload


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillLoadCompletedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.SKILL_LOAD_COMPLETED]
    payload: SkillLoadCompletedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class SkillLoadFailedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.SKILL_LOAD_FAILED]
    payload: SkillLoadFailedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class RagEmbedCompletedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.RAG_EMBED_COMPLETED]
    payload: RagEmbedCompletedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class RagQueryCompletedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.RAG_QUERY_COMPLETED]
    payload: RagQueryCompletedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class ScraperRunCompletedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.SCRAPER_RUN_COMPLETED]
    payload: ScraperRunCompletedPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class ScraperRagEmbedAttemptLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.SCRAPER_RAG_EMBED_ATTEMPT]
    payload: ScraperRagEmbedAttemptPayload


@dataclass(frozen=True, slots=True, kw_only=True)
class FeedbackRecordedLifecycleEvent(LifecycleEventBase):
    name: Literal[EventName.FEEDBACK_RECORDED]
    payload: FeedbackRecordedPayload


LifecycleEvent: TypeAlias = (
    RunStartedLifecycleEvent
    | RunEndedLifecycleEvent
    | TriggerRequestReceivedLifecycleEvent
    | TriggerRequestRespondedLifecycleEvent
    | TriggerRequestFailedLifecycleEvent
    | LlmGenerationStartedLifecycleEvent
    | LlmGenerationFirstTokenLifecycleEvent
    | LlmGenerationCompletedLifecycleEvent
    | LlmGenerationFailedLifecycleEvent
    | ToolCallStartedLifecycleEvent
    | ToolCallCompletedLifecycleEvent
    | ToolCallFailedLifecycleEvent
    | SubagentInvocationStartedLifecycleEvent
    | SubagentInvocationCompletedLifecycleEvent
    | SubagentInvocationFailedLifecycleEvent
    | SkillLoadStartedLifecycleEvent
    | SkillLoadCompletedLifecycleEvent
    | SkillLoadFailedLifecycleEvent
    | RagEmbedCompletedLifecycleEvent
    | RagQueryCompletedLifecycleEvent
    | ScraperRunCompletedLifecycleEvent
    | ScraperRagEmbedAttemptLifecycleEvent
    | FeedbackRecordedLifecycleEvent
)


__all__ = [
    "EventName",
    "FeedbackRecordedLifecycleEvent",
    "LifecycleEvent",
    "LifecycleEventBase",
    "LlmGenerationCompletedLifecycleEvent",
    "LlmGenerationFirstTokenLifecycleEvent",
    "RunEndedLifecycleEvent",
    "RunStartedLifecycleEvent",
    "ToolCallCompletedLifecycleEvent",
    "TriggerRequestRespondedLifecycleEvent",
]
