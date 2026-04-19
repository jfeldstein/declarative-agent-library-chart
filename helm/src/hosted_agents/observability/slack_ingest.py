"""Slack reaction ingestion → human feedback + W&B patch (async-friendly hooks)."""

from __future__ import annotations

from typing import Any

from hosted_agents.observability.correlation import SlackMessageRef
from hosted_agents.observability.feedback import HumanFeedbackEvent, OrphanReactionEvent
from hosted_agents.observability.stores import (
    get_correlation_store,
    get_feedback_store,
)
from hosted_agents.observability.label_registry import get_label_registry
from hosted_agents.observability.settings import ObservabilitySettings
from hosted_agents.observability.trajectory import trajectory_recorder
from hosted_agents.observability.wandb_run_tags import wandb_mandatory_tags_for_run
from hosted_agents.observability.wandb_trace import WandbTraceSession


def handle_slack_reaction_event(
    payload: dict[str, Any],
    *,
    settings: ObservabilitySettings,
) -> dict[str, str]:
    """Handle a normalized reaction-added payload.

    Expected keys: ``channel_id``, ``message_ts``, ``reaction``, ``event_id``, ``user_id``.
    Returns a small status dict for HTTP clients.
    """

    if not settings.slack_feedback_enabled:
        return {"status": "ignored", "reason": "slack_feedback_disabled"}

    channel_id = str(payload.get("channel_id") or "")
    message_ts = str(payload.get("message_ts") or "")
    reaction = str(payload.get("reaction") or "")
    event_id = str(payload.get("event_id") or "") or None
    user_id = str(payload.get("user_id") or "unknown")

    ref = SlackMessageRef(channel_id=channel_id, message_ts=message_ts)
    corr = get_correlation_store().get_by_slack(ref)
    if corr is None:
        get_feedback_store().record_orphan_reaction(
            OrphanReactionEvent(
                channel_id=channel_id,
                message_ts=message_ts,
                reason="no_correlation",
                raw_event_id=event_id,
            )
        )
        return {"status": "orphan"}

    label_id = settings.slack_emoji_map.get(reaction) or reaction
    reg = get_label_registry()
    entry = reg.resolve(label_id)
    if entry is None:
        get_feedback_store().record_orphan_reaction(
            OrphanReactionEvent(
                channel_id=channel_id,
                message_ts=message_ts,
                reason="unknown_label",
                raw_event_id=event_id,
            )
        )
        return {"status": "orphan", "reason": "unknown_label"}

    dedupe_key = f"{user_id}:{corr.checkpoint_id or 'nocp'}:{label_id}"
    ev = HumanFeedbackEvent(
        registry_id=reg.registry_id,
        schema_version=reg.schema_version,
        label_id=entry.label_id,
        tool_call_id=corr.tool_call_id,
        checkpoint_id=corr.checkpoint_id,
        run_id=corr.run_id,
        thread_id=corr.thread_id,
        feedback_source="slack_reaction",
        dedupe_key=dedupe_key,
    )
    get_feedback_store().record_human(ev)

    trajectory_recorder.append(
        corr.run_id,
        "human_feedback",
        {
            "label_id": entry.label_id,
            "scalar": entry.scalar,
            "tool_call_id": corr.tool_call_id,
            "checkpoint_id": corr.checkpoint_id,
            "source": "slack_reaction",
        },
    )

    late: WandbTraceSession | None = None
    if settings.wandb_enabled:
        late = WandbTraceSession(
            settings=settings,
            run_name=corr.run_id,
            tags=wandb_mandatory_tags_for_run(thread_id=corr.thread_id),
        )
    try:
        if late is not None:
            late.log_feedback(
                tool_call_id=corr.tool_call_id,
                checkpoint_id=corr.checkpoint_id,
                feedback_label=entry.label_id,
                feedback_source="slack_reaction",
            )
    finally:
        if late is not None:
            late.finish()

    return {"status": "recorded", "label_id": entry.label_id}
