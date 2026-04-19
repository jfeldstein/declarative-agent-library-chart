"""Shape tests for bundled toolsets (``TOOLS`` tuples)."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from agent.tools.contract import ToolSpec
from agent.tools.jira import TOOL_IDS as JIRA_TOOL_IDS
from agent.tools.jira import TOOLS as JIRA_TOOLS_TUPLE
from agent.tools.sample_echo import TOOLS as SAMPLE_TOOLS
from agent.tools.slack import TOOLS as SLACK_TOOLS


def test_slack_tools_tuple_ids() -> None:
    ids = {spec.id for spec in SLACK_TOOLS}
    assert ids == {
        "slack.post_message",
        "slack.reactions_add",
        "slack.reactions_remove",
        "slack.chat_update",
        "slack.conversations_history",
        "slack.conversations_replies",
    }
    assert all(isinstance(s, ToolSpec) for s in SLACK_TOOLS)


def test_jira_tools_tuple_ids() -> None:
    ids = {spec.id for spec in JIRA_TOOLS_TUPLE}
    assert ids == {
        "jira.search_issues",
        "jira.get_issue",
        "jira.add_comment",
        "jira.transition_issue",
        "jira.create_issue",
        "jira.update_issue",
    }
    assert JIRA_TOOL_IDS == ids


def test_sample_echo_tools_tuple() -> None:
    assert len(SAMPLE_TOOLS) == 1
    assert SAMPLE_TOOLS[0].id == "sample.echo"


def test_jira_handler_raises_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from agent.tools.jira import TOOLS as JIRA_TOOLS

    monkeypatch.setattr(
        "agent.tools.jira.config.load_settings",
        lambda: None,
    )
    with pytest.raises(ValueError, match="Jira tools are not enabled"):
        JIRA_TOOLS[0].handler({"jql": "x"})


def test_toolset_modules_have_no_langchain_imports() -> None:
    root = Path(__file__).resolve().parents[1] / "agent" / "tools"
    banned_roots = {"langchain", "langchain_core"}
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    head = alias.name.split(".")[0]
                    assert head not in banned_roots, f"{path}: {alias.name}"
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    head = node.module.split(".")[0]
                    assert head not in banned_roots, f"{path}: {node.module}"


def test_slack_init_preserves_legacy_reexports() -> None:
    from agent.tools.slack import (
        api_start,
        finish_ok,
        normalize_channel_id,
        send_message,
    )

    assert callable(api_start)
    assert callable(send_message)
    assert callable(finish_ok)
    assert callable(normalize_channel_id)
