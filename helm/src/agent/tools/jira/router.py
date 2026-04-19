"""Map allowlisted ``jira.*`` tool ids to handlers."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agent.tools.jira.config import JiraToolsSettings, load_settings
from agent.tools.jira.handlers import (
    run_add_comment,
    run_create_issue,
    run_get_issue,
    run_search_issues,
    run_transition_issue,
    run_update_issue,
)

_HANDLER: dict[str, Callable[[JiraToolsSettings, dict[str, Any]], dict[str, Any]]] = {
    "jira.search_issues": run_search_issues,
    "jira.get_issue": run_get_issue,
    "jira.add_comment": run_add_comment,
    "jira.transition_issue": run_transition_issue,
    "jira.create_issue": run_create_issue,
    "jira.update_issue": run_update_issue,
}


def invoke(tool: str, arguments: dict[str, Any]) -> dict[str, Any]:
    cfg = load_settings()
    if cfg is None:
        msg = (
            "Jira tools are not enabled (set HOSTED_AGENT_JIRA_TOOLS_ENABLED=true "
            "and chart jiraTools.enabled)"
        )
        raise ValueError(msg)
    fn = _HANDLER.get(tool)
    if fn is None:
        msg = f"unknown Jira tool: {tool}"
        raise ValueError(msg)
    return fn(cfg, arguments)
