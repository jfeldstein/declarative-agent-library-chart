"""Slack Web API metrics subscriber (generic tool events + namespaced ``extra``).

[DALC-REQ-SLACK-TOOLS-006]
"""

from __future__ import annotations

from prometheus_client import generate_latest

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.observability.plugins.prometheus import register_prometheus_agent_plugin
from agent.observability.plugins.slack_tool_metrics_plugin import (
    register_slack_tool_metrics_plugin,
)


def test_slack_tool_metrics_plugin_observes_web_api_method() -> None:
    """[DALC-REQ-SLACK-TOOLS-006] ``dalc_slack_*`` from ``extra['slack']['web_api_method']``."""
    bus = SyncEventBus()
    register_prometheus_agent_plugin(bus)
    register_slack_tool_metrics_plugin(bus)
    bus.publish(
        LifecycleEvent(
            EventName.TOOL_CALL_COMPLETED,
            {
                "tool": "slack.post_message",
                "started_at": 0.0,
                "ok": True,
                "extra": {"slack": {"web_api_method": "chat.postMessage"}},
            },
        ),
    )
    text = generate_latest().decode()
    assert "dalc_slack_tool_web_api_calls_total" in text
    assert 'method="chat.postMessage"' in text
