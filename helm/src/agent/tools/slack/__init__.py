"""LLM-time Slack Web API tools (``slack.*`` MCP ids); distinct from scraper CronJobs."""

from __future__ import annotations

from agent.tools.contract import ToolSpec
from agent.tools.slack.history import (
    chat_update,
    conversations_history,
    conversations_replies,
)
from agent.tools.slack.post import run, send_message
from agent.tools.slack.reactions import reactions_add, reactions_remove
from agent.tools.slack.schemas import (
    SlackChatUpdateArgs,
    SlackHistoryArgs,
    SlackPostMessageArgs,
    SlackReactionArgs,
    SlackRepliesArgs,
)
from agent.tools.slack.support import (
    api_start,
    default_history_limit,
    finish_ok,
    history_limit,
    normalize_channel_id,
    optional_tools_client,
    slack_api_error_payload,
    slack_response_data,
    slack_response_ok,
    timeout_seconds,
)

TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        id="slack.post_message",
        description=(
            "Post a Slack message (chat.postMessage). "
            "Provide channel_id or channel; optional thread_ts or reply_to_ts for replies."
        ),
        args_schema=SlackPostMessageArgs,
        handler=run,
    ),
    ToolSpec(
        id="slack.reactions_add",
        description="Add an emoji reaction to a Slack message (reactions.add).",
        args_schema=SlackReactionArgs,
        handler=reactions_add,
    ),
    ToolSpec(
        id="slack.reactions_remove",
        description="Remove an emoji reaction from a Slack message (reactions.remove).",
        args_schema=SlackReactionArgs,
        handler=reactions_remove,
    ),
    ToolSpec(
        id="slack.chat_update",
        description="Update a Slack message posted by the bot (chat.update).",
        args_schema=SlackChatUpdateArgs,
        handler=chat_update,
    ),
    ToolSpec(
        id="slack.conversations_history",
        description="Fetch recent messages from a Slack channel (conversations.history).",
        args_schema=SlackHistoryArgs,
        handler=conversations_history,
    ),
    ToolSpec(
        id="slack.conversations_replies",
        description="Fetch replies in a Slack thread (conversations.replies).",
        args_schema=SlackRepliesArgs,
        handler=conversations_replies,
    ),
)

__all__ = [
    "TOOLS",
    "api_start",
    "chat_update",
    "conversations_history",
    "conversations_replies",
    "default_history_limit",
    "finish_ok",
    "history_limit",
    "normalize_channel_id",
    "optional_tools_client",
    "reactions_add",
    "reactions_remove",
    "run",
    "send_message",
    "slack_api_error_payload",
    "slack_response_data",
    "slack_response_ok",
    "timeout_seconds",
]
