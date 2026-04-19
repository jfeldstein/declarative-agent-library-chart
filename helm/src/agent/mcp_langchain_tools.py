"""Typed LangChain ``@tool`` factories for in-process MCP tool ids (supervisor runtime).

[DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-002] Wrappers call ``run_tool_json`` → ``invoke_tool`` (same dicts as dispatch).
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from langchain_core.tools import tool

from agent.tools.dispatch import REGISTERED_MCP_TOOL_IDS
from agent.trigger_context import TriggerContext
from agent.trigger_steps import run_tool_json


def _json_fail(tool_id: str, safe_name: str, ctx: TriggerContext) -> Any:
    """Legacy wrapper: pass a single JSON object string (skill-unlocked or future ids)."""

    desc = (
        f"In-process MCP tool `{tool_id}`. "
        "Pass arguments as a JSON object string (e.g. '{{}}' or '{{\"key\": \"v\"}}')."
    )

    @tool(safe_name, description=desc)
    def generic_mcp_tool(arguments_json: str = "{}") -> str:
        try:
            args = json.loads(arguments_json) if arguments_json.strip() else {}
        except json.JSONDecodeError as exc:
            msg = f"invalid JSON arguments: {exc}"
            raise ValueError(msg) from exc
        return run_tool_json(ctx.cfg, tool_id, args)

    return generic_mcp_tool


def _tool_sample_echo(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(safe_name)
    def sample_echo(message: str) -> str:
        """Echo back a string (bundled sample MCP tool)."""
        return run_tool_json(ctx.cfg, "sample.echo", {"message": message})

    return sample_echo


def _tool_slack_post_message(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name,
        description=(
            "Post a Slack message (chat.postMessage). "
            "Provide channel_id or channel; optional thread_ts or reply_to_ts for replies."
        ),
    )
    def slack_post_message(
        text: str,
        channel_id: str = "",
        channel: str = "",
        thread_ts: str = "",
        reply_to_ts: str = "",
    ) -> str:
        args: dict[str, Any] = {"text": text}
        if channel_id:
            args["channel_id"] = channel_id
        elif channel:
            args["channel"] = channel
        if thread_ts:
            args["thread_ts"] = thread_ts
        elif reply_to_ts:
            args["reply_to_ts"] = reply_to_ts
        return run_tool_json(ctx.cfg, "slack.post_message", args)

    return slack_post_message


def _tool_slack_reactions_add(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name,
        description="Add an emoji reaction to a Slack message (reactions.add).",
    )
    def slack_reactions_add(
        channel_id: str,
        name: str,
        timestamp: str = "",
        ts: str = "",
    ) -> str:
        stamp = (timestamp or ts).strip()
        return run_tool_json(
            ctx.cfg,
            "slack.reactions_add",
            {"channel_id": channel_id, "timestamp": stamp, "name": name},
        )

    return slack_reactions_add


def _tool_slack_reactions_remove(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name,
        description="Remove an emoji reaction from a Slack message (reactions.remove).",
    )
    def slack_reactions_remove(
        channel_id: str,
        name: str,
        timestamp: str = "",
        ts: str = "",
    ) -> str:
        stamp = (timestamp or ts).strip()
        return run_tool_json(
            ctx.cfg,
            "slack.reactions_remove",
            {"channel_id": channel_id, "timestamp": stamp, "name": name},
        )

    return slack_reactions_remove


def _tool_slack_chat_update(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name, description="Update a Slack message posted by the bot (chat.update)."
    )
    def slack_chat_update(
        channel_id: str,
        ts: str,
        text: str,
    ) -> str:
        return run_tool_json(
            ctx.cfg,
            "slack.chat_update",
            {"channel_id": channel_id, "ts": ts, "text": text},
        )

    return slack_chat_update


def _tool_slack_conversations_history(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name,
        description="Fetch recent messages from a Slack channel (conversations.history).",
    )
    def slack_conversations_history(
        channel_id: str,
        limit: int | None = None,
    ) -> str:
        args: dict[str, Any] = {"channel_id": channel_id}
        if limit is not None:
            args["limit"] = limit
        return run_tool_json(ctx.cfg, "slack.conversations_history", args)

    return slack_conversations_history


def _tool_slack_conversations_replies(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name,
        description="Fetch replies in a Slack thread (conversations.replies).",
    )
    def slack_conversations_replies(
        channel_id: str,
        thread_ts: str,
        limit: int | None = None,
    ) -> str:
        args: dict[str, Any] = {"channel_id": channel_id, "thread_ts": thread_ts}
        if limit is not None:
            args["limit"] = limit
        return run_tool_json(ctx.cfg, "slack.conversations_replies", args)

    return slack_conversations_replies


def _tool_jira_search_issues(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name,
        description="Search Jira issues with JQL (bounded by deployment caps).",
    )
    def jira_search_issues(
        jql: str,
        max_results: int | None = None,
    ) -> str:
        args: dict[str, Any] = {"jql": jql}
        if max_results is not None:
            args["max_results"] = max_results
        return run_tool_json(ctx.cfg, "jira.search_issues", args)

    return jira_search_issues


def _tool_jira_get_issue(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(safe_name, description="Fetch a Jira issue by key.")
    def jira_get_issue(
        issue_key: str,
        fields: list[str] | None = None,
    ) -> str:
        args: dict[str, Any] = {"issue_key": issue_key}
        if fields:
            args["fields"] = fields
        return run_tool_json(ctx.cfg, "jira.get_issue", args)

    return jira_get_issue


def _tool_jira_add_comment(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(safe_name, description="Add a plain-text comment to a Jira issue.")
    def jira_add_comment(
        issue_key: str,
        body: str,
    ) -> str:
        return run_tool_json(
            ctx.cfg,
            "jira.add_comment",
            {"issue_key": issue_key, "body": body},
        )

    return jira_add_comment


def _tool_jira_transition_issue(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name,
        description="Transition a Jira issue; use transition_id or transition_name.",
    )
    def jira_transition_issue(
        issue_key: str,
        transition_id: str = "",
        transition_name: str = "",
    ) -> str:
        args: dict[str, Any] = {"issue_key": issue_key}
        if transition_id:
            args["transition_id"] = transition_id
        if transition_name:
            args["transition_name"] = transition_name
        return run_tool_json(ctx.cfg, "jira.transition_issue", args)

    return jira_transition_issue


def _tool_jira_create_issue(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(safe_name, description="Create a Jira issue in an allowlisted project.")
    def jira_create_issue(
        project_key: str,
        summary: str,
        issue_type: str,
        description: str = "",
    ) -> str:
        args: dict[str, Any] = {
            "project_key": project_key,
            "summary": summary,
            "issue_type": issue_type,
        }
        if description:
            args["description"] = description
        return run_tool_json(ctx.cfg, "jira.create_issue", args)

    return jira_create_issue


def _tool_jira_update_issue(safe_name: str, ctx: TriggerContext) -> Any:
    @tool(
        safe_name,
        description=(
            "Update Jira issue fields (REST PUT). "
            "`fields` maps Jira field ids to values (same shape as invoke_tool)."
        ),
    )
    def jira_update_issue(
        issue_key: str,
        fields: dict[str, Any],
    ) -> str:
        return run_tool_json(
            ctx.cfg,
            "jira.update_issue",
            {"issue_key": issue_key, "fields": fields},
        )

    return jira_update_issue


_TOOL_BUILDERS: dict[str, Callable[[str, TriggerContext], Any]] = {
    "sample.echo": _tool_sample_echo,
    "slack.post_message": _tool_slack_post_message,
    "slack.reactions_add": _tool_slack_reactions_add,
    "slack.reactions_remove": _tool_slack_reactions_remove,
    "slack.chat_update": _tool_slack_chat_update,
    "slack.conversations_history": _tool_slack_conversations_history,
    "slack.conversations_replies": _tool_slack_conversations_replies,
    "jira.search_issues": _tool_jira_search_issues,
    "jira.get_issue": _tool_jira_get_issue,
    "jira.add_comment": _tool_jira_add_comment,
    "jira.transition_issue": _tool_jira_transition_issue,
    "jira.create_issue": _tool_jira_create_issue,
    "jira.update_issue": _tool_jira_update_issue,
}

MCP_LANGCHAIN_TYPED_TOOL_IDS: frozenset[str] = frozenset(_TOOL_BUILDERS.keys())


def make_mcp_langchain_tool(tool_id: str, safe_name: str, ctx: TriggerContext) -> Any:
    """Return a LangChain tool for ``tool_id`` using typed parameters when registered."""
    builder = _TOOL_BUILDERS.get(tool_id)
    if builder is not None:
        return builder(safe_name, ctx)
    return _json_fail(tool_id, safe_name, ctx)


# [DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-003] Every registered id is typed; generic JSON wrapper only via _json_fail for unknown ids.
assert REGISTERED_MCP_TOOL_IDS == MCP_LANGCHAIN_TYPED_TOOL_IDS, (
    "REGISTERED_MCP_TOOL_IDS must match typed LangChain builders; update mcp_langchain_tools."
)
