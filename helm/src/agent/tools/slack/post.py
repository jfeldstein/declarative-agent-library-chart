"""Slack ``chat.postMessage`` tool — simulated without token, otherwise Slack Web API."""

from __future__ import annotations

import time
from typing import Any

from slack_sdk.errors import SlackApiError

from agent.observability.correlation import SlackMessageRef, ToolCorrelation
from agent.observability.run_context import (
    get_run_id,
    get_thread_id,
    get_tool_call_id,
)
from agent.observability.side_effects import record_side_effect_checkpoint
from agent.observability.stores import get_correlation_store
from agent.tools.slack.support import (
    finish_ok,
    normalize_channel_id,
    optional_tools_client,
    slack_api_error_payload,
    slack_response_data,
)


def _record_post_message_correlation(
    channel_id: str, message_ts: str
) -> tuple[str, str]:
    tool_call_id = get_tool_call_id() or "tc-unknown"
    run_id = get_run_id() or "unknown-run"
    thread_ctx = get_thread_id() or "unknown-thread"
    se = record_side_effect_checkpoint(
        tool_name="slack.post_message",
        external_ref={"channel_id": channel_id, "message_ts": message_ts},
        tool_call_id=tool_call_id,
    )
    get_correlation_store().put_slack_message(
        SlackMessageRef(channel_id=channel_id, message_ts=message_ts),
        ToolCorrelation(
            tool_call_id=tool_call_id,
            run_id=run_id,
            thread_id=thread_ctx,
            checkpoint_id=se.checkpoint_id,
            tool_name="slack.post_message",
            wandb_run_id=None,
        ),
    )
    return tool_call_id, se.checkpoint_id


def _simulated_post(arguments: dict[str, Any]) -> dict[str, Any]:
    channel_id = normalize_channel_id(arguments)
    text = str(arguments.get("text") or "")
    if not channel_id:
        msg = "slack.post_message requires channel_id or channel"
        raise ValueError(msg)

    message_ts = str(
        arguments.get("mock_ts") or arguments.get("ts") or f"{time.time():.6f}"
    )
    tool_call_id, checkpoint_id = _record_post_message_correlation(
        channel_id, message_ts
    )
    return {
        "ok": True,
        "simulated": True,
        "channel_id": channel_id,
        "ts": message_ts,
        "text": text,
        "tool_call_id": tool_call_id,
        "checkpoint_id": checkpoint_id,
    }


def _response_ts(resp: object) -> str:
    return str(slack_response_data(resp).get("ts") or "")


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    channel_id = normalize_channel_id(arguments)
    text = str(arguments.get("text") or "")
    if not channel_id:
        msg = "slack.post_message requires channel_id or channel"
        raise ValueError(msg)

    thread_raw = arguments.get("thread_ts") or arguments.get("reply_to_ts")
    thread_ts = str(thread_raw).strip() if thread_raw else ""

    client = optional_tools_client()
    if client is None:
        return _simulated_post(arguments)

    kwargs: dict[str, Any] = {"channel": channel_id, "text": text}
    if thread_ts:
        kwargs["thread_ts"] = thread_ts
    try:
        resp = client.chat_postMessage(**kwargs)
    except SlackApiError as exc:
        return slack_api_error_payload(exc, method="chat.postMessage")

    message_ts = _response_ts(resp)
    if not message_ts:
        return finish_ok(
            "chat.postMessage",
            {"ok": False, "error": "missing_ts", "channel_id": channel_id},
        )

    tool_call_id, checkpoint_id = _record_post_message_correlation(
        channel_id, message_ts
    )

    return finish_ok(
        "chat.postMessage",
        {
            "ok": True,
            "simulated": False,
            "channel_id": channel_id,
            "ts": message_ts,
            "text": text,
            "tool_call_id": tool_call_id,
            "checkpoint_id": checkpoint_id,
        },
    )


send_message = run
