"""Dispatch ``tool`` id to implementation."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from hosted_agents.tools_impl import (
    sample_echo,
    slack_chat_and_history,
    slack_post,
    slack_reactions,
)
from hosted_agents.tools_impl.jira import TOOL_IDS as JIRA_TOOL_IDS
from hosted_agents.tools_impl.jira import invoke as invoke_jira_tool

# Authoritative allowlist for Helm `mcp.enabledTools` contract tests (`tests/test_chart_values_contract.py`).
REGISTERED_MCP_TOOL_IDS: frozenset[str] = frozenset(
    {
        "sample.echo",
        "slack.post_message",
        "slack.reactions_add",
        "slack.reactions_remove",
        "slack.chat_update",
        "slack.conversations_history",
        "slack.conversations_replies",
    }
) | JIRA_TOOL_IDS

_NON_JIRA_DISPATCH: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "sample.echo": sample_echo.run,
    "slack.post_message": slack_post.run,
    "slack.reactions_add": slack_reactions.reactions_add,
    "slack.reactions_remove": slack_reactions.reactions_remove,
    "slack.chat_update": slack_chat_and_history.chat_update,
    "slack.conversations_history": slack_chat_and_history.conversations_history,
    "slack.conversations_replies": slack_chat_and_history.conversations_replies,
}


def invoke_tool(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Dispatch by tool id to shared module entrypoints (same dict shapes as LangChain wrappers)."""
    if tool in JIRA_TOOL_IDS:
        return invoke_jira_tool(tool, arguments)
    impl = _NON_JIRA_DISPATCH.get(tool)
    if impl is None:
        msg = f"unknown tool: {tool}"
        raise KeyError(msg)
    return impl(arguments)
