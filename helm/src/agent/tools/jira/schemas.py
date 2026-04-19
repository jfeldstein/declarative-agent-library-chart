"""Pydantic argument models for Jira MCP tools (no LangChain imports)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class JiraSearchIssuesArgs(BaseModel):
    jql: str
    max_results: int | None = None


class JiraGetIssueArgs(BaseModel):
    issue_key: str
    fields: list[str] | None = None


class JiraAddCommentArgs(BaseModel):
    issue_key: str
    body: str


class JiraTransitionIssueArgs(BaseModel):
    issue_key: str
    transition_id: str = ""
    transition_name: str = ""


class JiraCreateIssueArgs(BaseModel):
    project_key: str
    summary: str
    issue_type: str
    description: str = ""


class JiraUpdateIssueArgs(BaseModel):
    issue_key: str
    fields: dict[str, Any]
