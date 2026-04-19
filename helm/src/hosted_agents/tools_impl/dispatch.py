"""Dispatch ``tool`` id to implementation."""

from __future__ import annotations

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


def invoke_tool(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if tool == "sample.echo":
        return sample_echo.run(arguments)
    if tool == "slack.post_message":
        return slack_post.run(arguments)
    if tool == "slack.reactions_add":
        return slack_reactions.reactions_add(arguments)
    if tool == "slack.reactions_remove":
        return slack_reactions.reactions_remove(arguments)
    if tool == "slack.chat_update":
        return slack_chat_and_history.chat_update(arguments)
    if tool == "slack.conversations_history":
        return slack_chat_and_history.conversations_history(arguments)
    if tool == "slack.conversations_replies":
        return slack_chat_and_history.conversations_replies(arguments)
    if tool in JIRA_TOOL_IDS:
        return invoke_jira_tool(tool, arguments)
    msg = f"unknown tool: {tool}"
    raise KeyError(msg)
