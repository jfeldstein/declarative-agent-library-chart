"""Dispatch verified Jira webhooks into :func:`hosted_agents.trigger_graph.run_trigger_graph`."""

from __future__ import annotations

import uuid
from typing import Any

from hosted_agents.agent_models import TriggerBody
from hosted_agents.env import system_prompt_from_env
from hosted_agents.jira_trigger.payload import (
    build_jira_trigger_message,
    extract_issue_context,
    stable_thread_suffix,
)
from hosted_agents.metrics import observe_jira_trigger_inbound
from hosted_agents.observability.settings import ObservabilitySettings
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.trigger_graph import TriggerContext, run_trigger_graph


def dispatch_jira_webhook(
    payload: dict[str, Any],
    *,
    raw_body: bytes,
    request_id: str,
    delivery_header: str,
    deduper: Any | None,
    settings_event_dedupe: bool,
) -> None:
    """Run trigger graph for a parsed Jira webhook JSON object."""
    if settings_event_dedupe and deduper is not None:
        dedupe_key = delivery_header.strip()
        if dedupe_key and deduper.is_duplicate(dedupe_key):
            observe_jira_trigger_inbound("http", "deduped")
            return

    issue_key, project_key, webhook_event = extract_issue_context(payload)
    if not issue_key:
        observe_jira_trigger_inbound("http", "ignored")
        return

    message = build_jira_trigger_message(payload).strip() or (
        f"[{issue_key}] ({webhook_event or 'jira:event'})"
    )
    suffix = stable_thread_suffix(
        header_delivery_id=delivery_header,
        payload=payload,
        raw_body=raw_body,
    )
    thread_id = f"jira:{issue_key}:{suffix}"[:256]

    body = TriggerBody(message=message, thread_id=thread_id)
    cfg = RuntimeConfig.from_env()
    obs = ObservabilitySettings.from_env()
    run_id = str(uuid.uuid4())
    ctx = TriggerContext(
        cfg=cfg,
        body=body,
        system_prompt=system_prompt_from_env(),
        request_id=request_id,
        run_id=run_id,
        thread_id=thread_id,
        ephemeral=False,
        tenant_id=None,
        observability=obs,
        jira_issue_key=issue_key,
        jira_project_key=project_key,
        jira_webhook_event=webhook_event or None,
        jira_webhook_delivery_id=delivery_header.strip() or None,
    )
    try:
        run_trigger_graph(ctx)
        observe_jira_trigger_inbound("http", "ok")
    except Exception:
        observe_jira_trigger_inbound("http", "error")
        raise
