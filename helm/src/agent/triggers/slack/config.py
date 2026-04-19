"""Environment-backed settings for the Slack trigger bridge."""

from __future__ import annotations

import os
from dataclasses import dataclass

from agent.triggers.env_bool import env_truthy


@dataclass(frozen=True)
class SlackTriggerSettings:
    """Keys are disjoint from ``scrapers`` / ``SLACK_*`` CronJob env and ``HOSTED_AGENT_SLACK_TOOLS_*``."""

    enabled: bool
    signing_secret: str
    app_token: str
    bot_token: str
    socket_mode: bool
    event_dedupe: bool
    http_path: str

    @classmethod
    def from_env(cls) -> SlackTriggerSettings:
        return cls(
            enabled=env_truthy("HOSTED_AGENT_SLACK_TRIGGER_ENABLED"),
            signing_secret=os.environ.get(
                "HOSTED_AGENT_SLACK_TRIGGER_SIGNING_SECRET", ""
            ).strip(),
            app_token=os.environ.get(
                "HOSTED_AGENT_SLACK_TRIGGER_APP_TOKEN", ""
            ).strip(),
            bot_token=os.environ.get(
                "HOSTED_AGENT_SLACK_TRIGGER_BOT_TOKEN", ""
            ).strip(),
            socket_mode=env_truthy("HOSTED_AGENT_SLACK_TRIGGER_SOCKET_MODE"),
            event_dedupe=env_truthy("HOSTED_AGENT_SLACK_TRIGGER_EVENT_DEDUPE"),
            http_path=(
                os.environ.get(
                    "HOSTED_AGENT_SLACK_TRIGGER_HTTP_PATH",
                    "/api/v1/integrations/slack/events",
                ).strip()
                or "/api/v1/integrations/slack/events"
            ),
        )

    def http_events_configured(self) -> bool:
        return bool(self.signing_secret)

    def socket_mode_configured(self) -> bool:
        return self.socket_mode and bool(self.app_token) and bool(self.bot_token)
