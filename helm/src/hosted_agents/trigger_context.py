"""Per-request context for the trigger pipeline."""

from __future__ import annotations

from dataclasses import dataclass

from hosted_agents.agent_models import TriggerBody
from hosted_agents.observability.settings import ObservabilitySettings
from hosted_agents.runtime_config import RuntimeConfig


@dataclass(frozen=True)
class TriggerContext:
    cfg: RuntimeConfig
    body: TriggerBody | None
    system_prompt: str
    request_id: str
    run_id: str
    thread_id: str
    ephemeral: bool = False
    tenant_id: str | None = None
    observability: ObservabilitySettings | None = None
    # Populated when the trigger originates from Slack app_mention (slack-trigger bridge).
    slack_channel_id: str | None = None
    slack_thread_ts: str | None = None
    slack_message_ts: str | None = None
    # Populated when the trigger originates from Jira webhooks (jira-trigger bridge).
    jira_issue_key: str | None = None
    jira_project_key: str | None = None
    jira_webhook_event: str | None = None
    jira_webhook_delivery_id: str | None = None
