"""Guardrails for MCP LangChain tool registration vs Helm allowlist."""

from __future__ import annotations

import json
import re

import pytest

from hosted_agents.agent_models import TriggerBody
from hosted_agents.mcp_langchain_tools import MCP_LANGCHAIN_TYPED_TOOL_IDS, make_mcp_langchain_tool
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.tools_impl.dispatch import REGISTERED_MCP_TOOL_IDS
from hosted_agents.trigger_context import TriggerContext


def _sanitize_tool_name_fragment(raw: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", raw.strip()).strip("_")
    return s or "tool"


def _minimal_ctx(enabled: list[str]) -> TriggerContext:
    cfg = RuntimeConfig(
        rag_base_url="http://rag.invalid",
        subagents=[],
        skills=[],
        enabled_mcp_tools=enabled,
    )
    return TriggerContext(
        cfg=cfg,
        body=TriggerBody(message="hi"),
        system_prompt="test",
        request_id="req",
        run_id="run",
        thread_id="thr",
        observability=None,
    )


INVOCATION_PAYLOADS: dict[str, dict[str, object]] = {
    "sample.echo": {"message": "ping"},
    "slack.post_message": {
        "text": "hello",
        "channel_id": "C12345",
        "thread_ts": "",
        "reply_to_ts": "",
        "channel": "",
    },
    "slack.reactions_add": {
        "channel_id": "C12345",
        "name": "thumbsup",
        "timestamp": "1234.5678",
        "ts": "",
    },
    "slack.reactions_remove": {
        "channel_id": "C12345",
        "name": "thumbsup",
        "timestamp": "1234.5678",
        "ts": "",
    },
    "slack.chat_update": {"channel_id": "C12345", "ts": "1234.5678", "text": "updated"},
    "slack.conversations_history": {"channel_id": "C12345"},
    "slack.conversations_replies": {"channel_id": "C12345", "thread_ts": "1234.5678"},
    "jira.search_issues": {"jql": "project = DEMO"},
    "jira.get_issue": {"issue_key": "DEMO-1"},
    "jira.add_comment": {"issue_key": "DEMO-1", "body": "hello"},
    "jira.transition_issue": {"issue_key": "DEMO-1", "transition_id": "41", "transition_name": ""},
    "jira.create_issue": {
        "project_key": "DEMO",
        "summary": "task",
        "issue_type": "Task",
        "description": "",
    },
    "jira.update_issue": {"issue_key": "DEMO-1", "fields": {"summary": [{"set": "New"}]}},
}


def test_registered_mcp_tool_ids_match_langchain_builders() -> None:
    """Every Helm-contract tool id must have a typed LangChain factory (module import asserts too)."""
    assert REGISTERED_MCP_TOOL_IDS == MCP_LANGCHAIN_TYPED_TOOL_IDS


@pytest.mark.parametrize("tool_id", sorted(REGISTERED_MCP_TOOL_IDS))
def test_each_typed_tool_invokes_run_tool_json(tool_id: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Smoke: each `@tool` wrapper delegates to ``run_tool_json`` with structured args."""
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_run(cfg: RuntimeConfig, tid: str, args: dict[str, object]) -> str:
        calls.append((tid, args))
        return json.dumps({"tool": tid, "result": {"ok": True}})

    monkeypatch.setattr(
        "hosted_agents.mcp_langchain_tools.run_tool_json",
        fake_run,
    )

    payload = INVOCATION_PAYLOADS[tool_id]
    ctx = _minimal_ctx(enabled=list(REGISTERED_MCP_TOOL_IDS))
    safe = _sanitize_tool_name_fragment(tool_id)
    lc_tool = make_mcp_langchain_tool(tool_id, safe, ctx)

    lc_tool.invoke(payload)

    assert len(calls) == 1
    tid, captured = calls[0]
    assert tid == tool_id
    assert isinstance(captured, dict)


def test_unknown_tool_id_falls_back_to_generic_json(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple[str, dict[str, object]]] = []

    def fake_run(cfg: RuntimeConfig, tid: str, args: dict[str, object]) -> str:
        calls.append((tid, args))
        return json.dumps({"tool": tid, "result": {}})

    monkeypatch.setattr(
        "hosted_agents.mcp_langchain_tools.run_tool_json",
        fake_run,
    )

    ctx = _minimal_ctx(enabled=["future.tool"])
    t = make_mcp_langchain_tool("future.tool", "future_tool", ctx)
    t.invoke({"arguments_json": '{"x": 1}'})
    assert calls == [("future.tool", {"x": 1})]
