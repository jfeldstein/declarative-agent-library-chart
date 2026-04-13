"""Tests for :mod:`hosted_agents.runtime_config`."""

from __future__ import annotations

import json

import pytest

from hosted_agents.runtime_config import RuntimeConfig, subagent_system_prompt


def test_from_env_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """[CFHA-REQ-RAG-SCRAPERS-004]"""
    monkeypatch.delenv("HOSTED_AGENT_RAG_BASE_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_SUBAGENTS_JSON", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_SKILLS_JSON", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", raising=False)
    cfg = RuntimeConfig.from_env()
    assert cfg.rag_base_url == ""
    assert cfg.subagents == []
    assert cfg.skills == []
    assert cfg.enabled_mcp_tools == []


def test_from_env_lists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_RAG_BASE_URL", "http://rag:8090")
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps([{"name": "a", "systemPrompt": 'Respond, "Hi"'}]),
    )
    monkeypatch.setenv(
        "HOSTED_AGENT_SKILLS_JSON",
        json.dumps([{"name": "sk", "prompt": "x", "extra_tools": ["sample.echo"]}]),
    )
    monkeypatch.setenv("HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps(["sample.echo"]))
    cfg = RuntimeConfig.from_env()
    assert cfg.rag_base_url == "http://rag:8090"
    assert cfg.subagents[0]["name"] == "a"
    assert cfg.skills[0]["name"] == "sk"
    assert cfg.enabled_mcp_tools == ["sample.echo"]


def test_subagent_system_prompt_variants() -> None:
    assert subagent_system_prompt({"systemPrompt": "A"}) == "A"
    assert subagent_system_prompt({"system_prompt": "B"}) == "B"
    assert subagent_system_prompt({"systemPrompt": "", "system_prompt": "C"}) == "C"


def test_invalid_json_list(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SUBAGENTS_JSON", json.dumps({"not": "list"}))
    with pytest.raises(ValueError, match="JSON array"):
        RuntimeConfig.from_env()
