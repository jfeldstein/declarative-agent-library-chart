"""Boot-time validation of configured MCP tool ids."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from agent.app import create_app, validate_enabled_tools
from agent.runtime_config import RuntimeConfig


def test_validate_enabled_tools_passes_on_known_ids() -> None:
    cfg = RuntimeConfig(
        rag_base_url="",
        subagents=[],
        skills=[],
        enabled_mcp_tools=["sample.echo", "slack.post_message"],
    )
    validate_enabled_tools(cfg)


def test_validate_enabled_tools_raises_on_unknown_id() -> None:
    cfg = RuntimeConfig(
        rag_base_url="",
        subagents=[],
        skills=[],
        enabled_mcp_tools=["slack.typo"],
    )
    with pytest.raises(RuntimeError) as exc:
        validate_enabled_tools(cfg)
    msg = str(exc.value)
    assert "slack.typo" in msg
    assert "Registered ids:" in msg


def test_validate_accepts_jira_ids_even_when_jira_disabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "agent.tools.jira.config.load_settings",
        lambda: None,
    )
    cfg = RuntimeConfig(
        rag_base_url="",
        subagents=[],
        skills=[],
        enabled_mcp_tools=["jira.get_issue"],
    )
    validate_enabled_tools(cfg)


def test_lifespan_calls_validate_enabled_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[RuntimeConfig] = []

    def capture(cfg: RuntimeConfig) -> None:
        calls.append(cfg)

    monkeypatch.setattr("agent.app.validate_enabled_tools", capture)
    client = TestClient(create_app(system_prompt="hi"))
    with client:
        pass
    assert len(calls) == 1
    assert isinstance(calls[0], RuntimeConfig)
