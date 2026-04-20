"""Slack Web API Prometheus series from integration-namespaced ``extra`` on tool events.

Traceability: [DALC-REQ-SLACK-TOOLS-006]
See ADR 0015 — core Prometheus subscribers stay integration-agnostic.
"""

from __future__ import annotations

from typing import Any

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.observability.plugins.prometheus import observe_slack_tool_api


def register_slack_tool_metrics_plugin(bus: SyncEventBus) -> None:
    """Subscribe to generic ``tool.call.*`` events and emit ``dalc_slack_*`` when applicable."""

    bus.subscribe(EventName.TOOL_CALL_COMPLETED, _on_tool_call_completed)
    bus.subscribe(EventName.TOOL_CALL_FAILED, _on_tool_call_failed)


def _slack_web_api_method(payload: dict[str, Any]) -> str | None:
    extra = payload.get("extra")
    if not isinstance(extra, dict):
        return None
    slack = extra.get("slack")
    if not isinstance(slack, dict):
        return None
    raw = slack.get("web_api_method")
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return None


def _on_tool_call_completed(event: LifecycleEvent) -> None:
    p = event.payload
    method = _slack_web_api_method(p)
    if method is None:
        return
    started_at = float(p["started_at"])
    ok = bool(p.get("ok", True))
    result_label = "success" if ok else "error"
    observe_slack_tool_api(method, result_label, started_at)


def _on_tool_call_failed(event: LifecycleEvent) -> None:
    p = event.payload
    method = _slack_web_api_method(p)
    if method is None:
        return
    started_at = float(p["started_at"])
    observe_slack_tool_api(method, "error", started_at)
