"""Slack ``chat.update`` and bounded ``conversations.*`` read tools."""

from __future__ import annotations

from typing import Any

from slack_sdk.errors import SlackApiError

from hosted_agents.tools_impl.slack_support import (
    api_start,
    finish_ok,
    history_limit,
    normalize_channel_id,
    optional_tools_client,
    slack_api_error_payload,
    slack_response_data,
)


def chat_update(arguments: dict[str, Any]) -> dict[str, Any]:
    channel_id = normalize_channel_id(arguments)
    ts = str(arguments.get("ts") or arguments.get("timestamp") or "").strip()
    text = str(arguments.get("text") or "")
    if not channel_id or not ts:
        raise ValueError("slack.chat_update requires channel_id and ts")

    client = optional_tools_client()
    if client is None:
        return {
            "ok": True,
            "simulated": True,
            "channel_id": channel_id,
            "ts": ts,
            "text": text,
        }

    start = api_start()
    try:
        resp = client.chat_update(channel=channel_id, ts=ts, text=text)
    except SlackApiError as exc:
        return slack_api_error_payload(exc, method="chat.update", start=start)

    data = slack_response_data(resp)
    out_ts = str(data.get("ts") or ts)
    return finish_ok(
        "chat.update",
        {
            "ok": bool(data.get("ok", True)),
            "channel_id": channel_id,
            "ts": out_ts,
            "text": text,
        },
        start,
    )


def _normalize_messages(raw: object) -> list[dict[str, Any]]:
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw:
        if isinstance(item, dict):
            out.append(
                {
                    "ts": str(item.get("ts") or ""),
                    "user": str(item.get("user") or ""),
                    "text": str(item.get("text") or ""),
                    "type": str(item.get("type") or ""),
                }
            )
    return out


def conversations_history(arguments: dict[str, Any]) -> dict[str, Any]:
    channel_id = normalize_channel_id(arguments)
    if not channel_id:
        raise ValueError("slack.conversations_history requires channel_id")

    lim = history_limit(arguments.get("limit"))

    client = optional_tools_client()
    if client is None:
        return {
            "ok": True,
            "simulated": True,
            "channel_id": channel_id,
            "messages": [],
            "limit": lim,
        }

    start = api_start()
    try:
        resp = client.conversations_history(channel=channel_id, limit=lim)
    except SlackApiError as exc:
        return slack_api_error_payload(exc, method="conversations.history", start=start)

    data = slack_response_data(resp)
    messages = _normalize_messages(data.get("messages"))
    return finish_ok(
        "conversations.history",
        {
            "ok": bool(data.get("ok", True)),
            "channel_id": channel_id,
            "messages": messages,
            "limit": lim,
        },
        start,
    )


def conversations_replies(arguments: dict[str, Any]) -> dict[str, Any]:
    channel_id = normalize_channel_id(arguments)
    thread_ts = str(arguments.get("thread_ts") or arguments.get("ts") or "").strip()
    if not channel_id or not thread_ts:
        raise ValueError(
            "slack.conversations_replies requires channel_id and thread_ts"
        )

    lim = history_limit(arguments.get("limit"))

    client = optional_tools_client()
    if client is None:
        return {
            "ok": True,
            "simulated": True,
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "messages": [],
            "limit": lim,
        }

    start = api_start()
    try:
        resp = client.conversations_replies(
            channel=channel_id,
            ts=thread_ts,
            limit=lim,
        )
    except SlackApiError as exc:
        return slack_api_error_payload(exc, method="conversations.replies", start=start)

    data = slack_response_data(resp)
    messages = _normalize_messages(data.get("messages"))
    return finish_ok(
        "conversations.replies",
        {
            "ok": bool(data.get("ok", True)),
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "messages": messages,
            "limit": lim,
        },
        start,
    )
