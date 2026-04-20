"""Dispatch Slack ``app_mention`` into :func:`agent.trigger_graph.run_trigger_graph`."""

from __future__ import annotations

import os
import uuid
from typing import Any, Literal

from slack_sdk import WebClient

from agent.agent_models import TriggerBody
from agent.env import system_prompt_from_env
from agent.observability.middleware import publish_slack_trigger_inbound
from agent.observability.settings import ObservabilitySettings
from agent.runtime_config import RuntimeConfig
from agent.o11y_logging import get_logger
from agent.triggers.slack.mention import (
    extract_app_mention,
    slack_thread_id_for_event,
)
from agent.tools.slack.support import optional_tools_client, timeout_seconds
from agent.triggers.guarded_run import run_guarded
from agent.runtime_identity import resolve_run_identity
from agent.trigger_graph import TriggerContext, run_trigger_graph

Transport = Literal["http", "socket"]


def _slack_client_for_trigger_reply() -> WebClient | None:
    """Prefer Slack tools token; otherwise use trigger bot token (same app, ``chat:write``)."""

    client = optional_tools_client()
    if client is not None:
        return client
    tok = os.environ.get("HOSTED_AGENT_SLACK_TRIGGER_BOT_TOKEN", "").strip()
    if tok:
        return WebClient(token=tok, timeout=timeout_seconds())
    return None


def _post_slack_trigger_reply(ctx: TriggerContext, text: str) -> None:
    """Deliver plain-text trigger output back to Slack for ``app_mention`` runs."""

    body = str(text or "").strip()
    channel = str(ctx.slack_channel_id or "").strip()
    if not body or not channel:
        return

    client = _slack_client_for_trigger_reply()
    if client is None:
        get_logger().warning(
            "slack_trigger_reply_skipped_no_token",
            channel_id=channel,
            reason="no_slack_tools_or_trigger_bot_token",
        )
        return

    thread_ts = str(ctx.slack_thread_ts or "").strip()
    kwargs: dict[str, Any] = {"channel": channel, "text": body}
    if thread_ts:
        kwargs["thread_ts"] = thread_ts

    try:
        client.chat_postMessage(**kwargs)
    except Exception:
        get_logger().exception(
            "slack_trigger_reply_post_failed",
            channel_id=channel,
        )


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
        publish_slack_trigger_inbound(transport=transport, outcome="ignored")
        return

    event_id = ""
    if settings_event_dedupe:
        event_id = str(body.get("event_id") or "").strip()

    if settings_event_dedupe and deduper is not None and event_id:
        if deduper.is_duplicate(event_id):
            publish_slack_trigger_inbound(transport=transport, outcome="deduped")
            return

    if str(event.get("bot_id") or "").strip():
        publish_slack_trigger_inbound(transport=transport, outcome="ignored")
        return

    parsed = extract_app_mention(event)
    if parsed is None:
        publish_slack_trigger_inbound(transport=transport, outcome="ignored")
        return

    message, channel_id, thread_ts, message_ts = parsed
    thread_id = slack_thread_id_for_event(event)
    if not thread_id:
        publish_slack_trigger_inbound(transport=transport, outcome="ignored")
        return

    payload = TriggerBody(message=message or None, thread_id=thread_id)
    cfg = RuntimeConfig.from_env()
    obs = ObservabilitySettings.from_env()
    run_id = str(uuid.uuid4())
    ctx = TriggerContext(
        cfg=cfg,
        run_identity=resolve_run_identity(body=payload),
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

    def _run_and_reply() -> str:
        out = run_trigger_graph(ctx)
        _post_slack_trigger_reply(ctx, out)
        publish_slack_trigger_inbound(transport=transport, outcome="ok")
        return out

    run_guarded(
        _run_and_reply,
        on_error=lambda: publish_slack_trigger_inbound(
            transport=transport, outcome="error"
        ),
    )


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
