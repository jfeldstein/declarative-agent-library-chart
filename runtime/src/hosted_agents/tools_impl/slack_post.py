"""Simulated Slack post tool: records correlation + side-effect checkpoint metadata."""

from __future__ import annotations

import time
from typing import Any

from hosted_agents.observability.correlation import SlackMessageRef, ToolCorrelation, correlation_store
from hosted_agents.observability.run_context import get_run_id, get_thread_id, get_tool_call_id
from hosted_agents.observability.side_effects import record_side_effect_checkpoint


def run(arguments: dict[str, Any]) -> dict[str, Any]:
    channel_id = str(arguments.get("channel_id") or arguments.get("channel") or "")
    text = str(arguments.get("text") or "")
    if not channel_id:
        msg = "slack.post_message requires channel_id or channel"
        raise ValueError(msg)

    message_ts = str(arguments.get("ts") or f"{time.time():.6f}")
    tool_call_id = get_tool_call_id() or "tc-unknown"
    run_id = get_run_id() or "unknown-run"
    thread_id = get_thread_id() or "unknown-thread"

    se = record_side_effect_checkpoint(
        tool_name="slack.post_message",
        external_ref={"channel_id": channel_id, "message_ts": message_ts},
        tool_call_id=tool_call_id,
    )
    correlation_store.put_slack_message(
        SlackMessageRef(channel_id=channel_id, message_ts=message_ts),
        ToolCorrelation(
            tool_call_id=tool_call_id,
            run_id=run_id,
            thread_id=thread_id,
            checkpoint_id=se.checkpoint_id,
            tool_name="slack.post_message",
            wandb_run_id=None,
        ),
    )
    return {
        "ok": True,
        "channel_id": channel_id,
        "ts": message_ts,
        "text": text,
        "tool_call_id": tool_call_id,
        "checkpoint_id": se.checkpoint_id,
    }
