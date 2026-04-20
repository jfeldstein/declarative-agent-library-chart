"""Slack reaction ingestion → human feedback + W&B patch (async-friendly hooks)."""

from __future__ import annotations

from typing import Any

from agent.observability.correlation import SlackMessageRef
from agent.observability.feedback import HumanFeedbackEvent, OrphanReactionEvent
from agent.observability.stores import (
    get_correlation_store,
    get_feedback_store,
)
from agent.observability.label_registry import get_label_registry
from agent.observability.settings import ObservabilitySettings
from agent.observability.trajectory import trajectory_recorder
from agent.observability.middleware import publish_feedback_recorded
from agent.runtime_identity import resolve_run_identity


def _feedback_dedupe_key(user_id: str, checkpoint_id: str | None, label_id: str) -> str:
    return f"{user_id}:{checkpoint_id or 'nocp'}:{label_id}"


def _normalize_event_type(payload: dict[str, Any]) -> str:
    raw = (
        payload.get("event_type")
        or payload.get("type")
        or payload.get("slack_event_type")
        or "reaction_added"
    )
    et = str(raw).lower()
    if et in ("reaction_added", "reaction_removed"):
        return et
    return "reaction_added"


def handle_slack_reaction_event(
    payload: dict[str, Any],
    *,
    settings: ObservabilitySettings,
) -> dict[str, str]:
    """Handle normalized Slack reaction payloads (added or removed).

    Expected keys: ``channel_id``, ``message_ts``, ``reaction``, ``event_id``, ``user_id``.

    Optional:

    - ``event_type`` — ``reaction_added`` (default) or ``reaction_removed``
    - ``type`` / ``slack_event_type`` — aliases accepted for compatibility
    """

    if not settings.slack_feedback_enabled:
        return {"status": "ignored", "reason": "slack_feedback_disabled"}

    channel_id = str(payload.get("channel_id") or "")
    message_ts = str(payload.get("message_ts") or "")
    reaction = str(payload.get("reaction") or "")
    event_id = str(payload.get("event_id") or "") or None
    user_id = str(payload.get("user_id") or "unknown")
    event_type = _normalize_event_type(payload)

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

    label_input = settings.slack_emoji_map.get(reaction) or reaction
    reg = get_label_registry()
    entry = reg.resolve(label_input)
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

    cp_id = corr.checkpoint_id
    dk = _feedback_dedupe_key(user_id, cp_id, entry.label_id)

    if event_type == "reaction_removed":
        removed = get_feedback_store().retract_human(dk)
        if removed:
            return {"status": "retracted", "label_id": entry.label_id}
        return {"status": "ignored", "reason": "no_prior_feedback"}

    # reaction_added: drop opposite scalar labels for this user + checkpoint
    for opp_id in reg.opposing_scalar_label_ids(entry.label_id):
        get_feedback_store().retract_human(_feedback_dedupe_key(user_id, cp_id, opp_id))

    ev = HumanFeedbackEvent(
        registry_id=reg.registry_id,
        schema_version=reg.schema_version,
        label_id=entry.label_id,
        tool_call_id=corr.tool_call_id,
        checkpoint_id=corr.checkpoint_id,
        run_id=corr.run_id,
        thread_id=corr.thread_id,
        feedback_source="slack_reaction",
        dedupe_key=dk,
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

    ri = (
        corr.run_identity
        if corr.run_identity is not None
        else resolve_run_identity(body=None)
    )
    publish_feedback_recorded(
        observability_settings=settings,
        run_id=corr.run_id,
        thread_id=corr.thread_id,
        run_identity=ri.as_flat_str_dict(),
        tool_call_id=corr.tool_call_id,
        checkpoint_id=corr.checkpoint_id,
        feedback_label=entry.label_id,
        feedback_source="slack_reaction",
        feedback_scalar=entry.scalar,
    )

    return {"status": "recorded", "label_id": entry.label_id}
