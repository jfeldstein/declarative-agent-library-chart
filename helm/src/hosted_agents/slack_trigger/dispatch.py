"""Dispatch Slack ``app_mention`` into :func:`hosted_agents.trigger_graph.run_trigger_graph`."""

from __future__ import annotations

import uuid
from typing import Any, Literal

from hosted_agents.agent_models import TriggerBody
from hosted_agents.env import system_prompt_from_env
from hosted_agents.metrics import observe_slack_trigger_inbound
from hosted_agents.observability.settings import ObservabilitySettings
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.slack_trigger.mention import (
    extract_app_mention,
    slack_thread_id_for_event,
)
from hosted_agents.trigger_graph import TriggerContext, run_trigger_graph

Transport = Literal["http", "socket"]


def dispatch_app_mention(
    body: dict[str, Any],
    *,
    transport: Transport,
    request_id: str,
    deduper: Any | None,
    settings_event_dedupe: bool,
) -> None:
    """Run trigger graph for a normalized Events API body (inner ``event`` dict)."""
    event = body.get("event")
    if not isinstance(event, dict):
        observe_slack_trigger_inbound(transport, "ignored")
        return

    event_id = ""
    if settings_event_dedupe:
        event_id = str(body.get("event_id") or "").strip()

    if settings_event_dedupe and deduper is not None and event_id:
        if deduper.is_duplicate(event_id):
            observe_slack_trigger_inbound(transport, "deduped")
            return

    if str(event.get("bot_id") or "").strip():
        observe_slack_trigger_inbound(transport, "ignored")
        return

    parsed = extract_app_mention(event)
    if parsed is None:
        observe_slack_trigger_inbound(transport, "ignored")
        return

    message, channel_id, thread_ts, message_ts = parsed
    thread_id = slack_thread_id_for_event(event)
    if not thread_id:
        observe_slack_trigger_inbound(transport, "ignored")
        return

    payload = TriggerBody(message=message or None, thread_id=thread_id)
    cfg = RuntimeConfig.from_env()
    obs = ObservabilitySettings.from_env()
    run_id = str(uuid.uuid4())
    ctx = TriggerContext(
        cfg=cfg,
        body=payload,
        system_prompt=system_prompt_from_env(),
        request_id=request_id,
        run_id=run_id,
        thread_id=thread_id,
        ephemeral=False,
        tenant_id=None,
        observability=obs,
        slack_channel_id=channel_id,
        slack_thread_ts=thread_ts,
        slack_message_ts=message_ts,
    )
    try:
        run_trigger_graph(ctx)
        observe_slack_trigger_inbound(transport, "ok")
    except Exception:
        observe_slack_trigger_inbound(transport, "error")
        raise


def dispatch_raw_app_mention_event(
    event: dict[str, Any],
    *,
    transport: Transport,
    request_id: str,
    outer_event_id: str | None,
    deduper: Any | None,
    settings_event_dedupe: bool,
) -> None:
    """Socket Mode delivers the inner ``event`` dict; wrap like an Events API envelope."""
    synthetic: dict[str, Any] = {"event": event}
    if outer_event_id:
        synthetic["event_id"] = outer_event_id
    dispatch_app_mention(
        synthetic,
        transport=transport,
        request_id=request_id,
        deduper=deduper,
        settings_event_dedupe=settings_event_dedupe,
    )
