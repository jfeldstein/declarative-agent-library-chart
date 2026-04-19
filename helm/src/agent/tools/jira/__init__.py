"""Jira Cloud REST tools for LLM-time issue operations (distinct from scrapers / trigger keys)."""

from __future__ import annotations

from functools import partial

from agent.tools.contract import ToolSpec
from agent.tools.jira.router import invoke
from agent.tools.jira.schemas import (
    JiraAddCommentArgs,
    JiraCreateIssueArgs,
    JiraGetIssueArgs,
    JiraSearchIssuesArgs,
    JiraTransitionIssueArgs,
    JiraUpdateIssueArgs,
)

TOOLS: tuple[ToolSpec, ...] = (
    ToolSpec(
        id="jira.search_issues",
        description="Search Jira issues with JQL (bounded by deployment caps).",
        args_schema=JiraSearchIssuesArgs,
        handler=partial(invoke, "jira.search_issues"),
    ),
    ToolSpec(
        id="jira.get_issue",
        description="Fetch a Jira issue by key.",
        args_schema=JiraGetIssueArgs,
        handler=partial(invoke, "jira.get_issue"),
    ),
    ToolSpec(
        id="jira.add_comment",
        description="Add a plain-text comment to a Jira issue.",
        args_schema=JiraAddCommentArgs,
        handler=partial(invoke, "jira.add_comment"),
    ),
    ToolSpec(
        id="jira.transition_issue",
        description="Transition a Jira issue; use transition_id or transition_name.",
        args_schema=JiraTransitionIssueArgs,
        handler=partial(invoke, "jira.transition_issue"),
    ),
    ToolSpec(
        id="jira.create_issue",
        description="Create a Jira issue in an allowlisted project.",
        args_schema=JiraCreateIssueArgs,
        handler=partial(invoke, "jira.create_issue"),
    ),
    ToolSpec(
        id="jira.update_issue",
        description=(
            "Update Jira issue fields (REST PUT). "
            "`fields` maps Jira field ids to values (same shape as invoke_tool)."
        ),
        args_schema=JiraUpdateIssueArgs,
        handler=partial(invoke, "jira.update_issue"),
    ),
)

TOOL_IDS: frozenset[str] = frozenset(spec.id for spec in TOOLS)

__all__ = ["TOOL_IDS", "TOOLS", "invoke"]
