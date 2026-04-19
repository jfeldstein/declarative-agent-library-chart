"""Environment-backed settings for the Jira trigger bridge."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agent.triggers.env_bool import env_truthy


@dataclass(frozen=True)
class JiraTriggerSettings:
    """Keys are disjoint from ``scrapers.jira`` and ``HOSTED_AGENT_JIRA_TOOLS_*``."""

    enabled: bool
    webhook_secret: str
    event_dedupe: bool
    http_path: str

    @classmethod
    def from_env(cls) -> JiraTriggerSettings:
        return cls(
            enabled=env_truthy("HOSTED_AGENT_JIRA_TRIGGER_ENABLED"),
            webhook_secret=os.environ.get(
                "HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET", ""
            ).strip(),
            event_dedupe=env_truthy("HOSTED_AGENT_JIRA_TRIGGER_EVENT_DEDUPE"),
            http_path=(
                os.environ.get(
                    "HOSTED_AGENT_JIRA_TRIGGER_HTTP_PATH",
                    "/api/v1/integrations/jira/webhook",
                ).strip()
                or "/api/v1/integrations/jira/webhook"
            ),
        )

    def http_configured(self) -> bool:
        """HTTP listener is registered only when enabled and a verification secret is set."""
        return self.enabled and bool(self.webhook_secret)
