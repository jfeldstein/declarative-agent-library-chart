"""TypedDict payload shapes for each :class:`EventName` (OpenSpec lifecycle events)."""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypeAlias, TypedDict


# --- Reserved / not yet emitted by middleware (empty payload) ---


class ReservedLifecyclePayload(TypedDict, total=False):
    """Payload for event names reserved for future instrumentation."""


# --- run.* ---


class RunStartedPayload(TypedDict):
    run_id: str
    run_name: str
    thread_id: str
    run_identity: dict[str, str]
    request_correlation_id: str
    observability: Any


class RunEndedPayload(TypedDict, total=False):
    """Paired with :func:`~agent.observability.middleware.publish_run_ended`; no fields."""


# --- trigger.request.* ---


class TriggerHttpRespondedPayload(TypedDict):
    trigger: Literal["http"]
    http_result: str
    started_at: float
    request_bytes: int
    response_bytes: int | None


class TriggerSlackRespondedPayload(TypedDict):
    trigger: Literal["slack"]
    transport: str
    outcome: str


class TriggerJiraRespondedPayload(TypedDict):
    trigger: Literal["jira"]
    transport: str
    outcome: str


TriggerRequestRespondedPayload: TypeAlias = (
    TriggerHttpRespondedPayload
    | TriggerSlackRespondedPayload
    | TriggerJiraRespondedPayload
)


# --- llm.generation.* ---


class LlmGenerationFirstTokenPayload(TypedDict):
    ctx: Any
    seconds: float
    streaming_label: str
    result: str


class LlmGenerationCompletedPayload(TypedDict):
    ctx: Any
    input_tokens: int | None
    output_tokens: int | None
    input_rate_usd: float | None
    output_rate_usd: float | None
    result: str


# --- tool.call.* ---


class ToolCallCompletedPayload(TypedDict):
    tool: str
    started_at: float
    ok: bool
    tool_call_id: NotRequired[str]
    duration_s: NotRequired[float]
    extra: NotRequired[dict[str, Any]]
    slack_web_api_method: NotRequired[str]


class ToolCallFailedPayload(TypedDict):
    tool: str
    started_at: float
    extra: NotRequired[dict[str, Any]]
    slack_web_api_method: NotRequired[str]


# --- skill.load.* ---


class SkillLoadCompletedPayload(TypedDict):
    skill: str
    started_at: float


class SkillLoadFailedPayload(TypedDict):
    skill: str
    started_at: float


# --- subagent.invocation.* ---


class SubagentInvocationCompletedPayload(TypedDict):
    subagent: str
    started_at: float


class SubagentInvocationFailedPayload(TypedDict):
    subagent: str
    started_at: float


# --- rag.* ---


class RagEmbedCompletedPayload(TypedDict):
    result: str
    elapsed_seconds: float


class RagQueryCompletedPayload(TypedDict):
    result: str
    elapsed_seconds: float


# --- scraper.* ---


class ScraperRunCompletedPayload(TypedDict):
    integration: str
    success: bool
    elapsed_seconds: float


class ScraperRagEmbedAttemptPayload(TypedDict):
    integration: str
    result: str


# --- feedback.recorded ---


class FeedbackRecordedPayload(TypedDict):
    observability_settings: Any
    run_id: str
    thread_id: str
    run_identity: dict[str, str]
    request_correlation_id: NotRequired[str]
    tool_call_id: str
    checkpoint_id: str | None
    feedback_label: str
    feedback_source: str
    feedback_scalar: NotRequired[int | None]
