"""Slack reactions add/remove tools."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from hosted_agents.tools.slack.support import (
    api_start,
    finish_ok,
    normalize_channel_id,
    optional_tools_client,
    slack_api_error_payload,
    slack_response_ok,
)


def _emoji_name(raw: Any) -> str:
    return str(raw or "").strip().strip(":")


def _reaction_tool(
    arguments: dict[str, Any],
    *,
    tool_id: str,
    metric_method: str,
    invoke: Callable[[WebClient, str, str, str], Any],
) -> dict[str, Any]:
    channel_id = normalize_channel_id(arguments)
    ts = str(arguments.get("timestamp") or arguments.get("ts") or "").strip()
    name = _emoji_name(arguments.get("name") or arguments.get("emoji"))
    if not channel_id or not ts or not name:
        raise ValueError(
            f"{tool_id} requires channel_id, timestamp (or ts), and name (emoji)"
        )

    client = optional_tools_client()
    if client is None:
        return {
            "ok": True,
            "simulated": True,
            "channel_id": channel_id,
            "timestamp": ts,
            "name": name,
        }

    start = api_start()
    try:
        resp = invoke(client, channel_id, ts, name)
    except SlackApiError as exc:
        return slack_api_error_payload(exc, method=metric_method, start=start)

    ok = slack_response_ok(resp)
    return finish_ok(
        metric_method,
        {"ok": ok, "channel_id": channel_id, "timestamp": ts, "name": name},
        start,
    )


def reactions_add(arguments: dict[str, Any]) -> dict[str, Any]:
    return _reaction_tool(
        arguments,
        tool_id="slack.reactions_add",
        metric_method="reactions.add",
        invoke=lambda c, ch, ts, nm: c.reactions_add(channel=ch, timestamp=ts, name=nm),
    )


def reactions_remove(arguments: dict[str, Any]) -> dict[str, Any]:
    return _reaction_tool(
        arguments,
        tool_id="slack.reactions_remove",
        metric_method="reactions.remove",
        invoke=lambda c, ch, ts, nm: c.reactions_remove(
            channel=ch, timestamp=ts, name=nm
        ),
    )
