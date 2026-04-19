"""Repository protocols for correlation, feedback, side-effects, and span summaries."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from agent.observability.correlation import SlackMessageRef, ToolCorrelation
from agent.observability.feedback import HumanFeedbackEvent, OrphanReactionEvent
from agent.observability.side_effects import SideEffectCheckpoint
from agent.observability.span_summaries import ToolSpanSummary


@runtime_checkable
class CorrelationRepository(Protocol):
    def put_slack_message(
        self, ref: SlackMessageRef, corr: ToolCorrelation
    ) -> None: ...
    def get_by_slack(self, ref: SlackMessageRef) -> ToolCorrelation | None: ...


@runtime_checkable
class FeedbackRepository(Protocol):
    def record_human(self, ev: HumanFeedbackEvent) -> HumanFeedbackEvent | None: ...
    def retract_human(self, dedupe_key: str) -> bool: ...
    def record_orphan_reaction(self, ev: OrphanReactionEvent) -> None: ...
    def human_events(self) -> list[HumanFeedbackEvent]: ...
    def orphans(self) -> list[OrphanReactionEvent]: ...


@runtime_checkable
class SideEffectRepository(Protocol):
    def add(self, rec: SideEffectCheckpoint) -> None: ...
    def by_thread(self, thread_id: str) -> list[SideEffectCheckpoint]: ...


@runtime_checkable
class SpanSummaryRepository(Protocol):
    def record(self, row: ToolSpanSummary) -> None: ...
