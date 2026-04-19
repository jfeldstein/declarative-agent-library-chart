"""Tests for agent HTTP routes (RAG proxy, trigger-orchestrated subagents/skills/tools)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from agent.app import create_app
from agent.skills_state import reset_skill_unlocked_tools
from tests.conftest import patch_supervisor_fake_model, tool_then_text_responses


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    reset_skill_unlocked_tools()
    monkeypatch.setenv("HOSTED_AGENT_SYSTEM_PROMPT", 'Respond, "Main"')
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [
                {
                    "name": "s1",
                    "systemPrompt": 'Respond, "Sub1"',
                    "description": "Test specialist s1",
                },
            ],
        ),
    )
    monkeypatch.setenv(
        "HOSTED_AGENT_SKILLS_JSON",
        json.dumps(
            [{"name": "bonus", "prompt": "Skill text", "extra_tools": ["sample.echo"]}],
        ),
    )
    monkeypatch.setenv("HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps([]))
    return TestClient(create_app())


def test_runtime_summary(client: TestClient) -> None:
    r = client.get("/api/v1/runtime/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["subagents"] == ["s1"]
    assert body["skills"] == ["bonus"]
    assert body["enabled_mcp_tools"] == []
    assert body["launch_path"] == "POST /api/v1/trigger"
    assert body["orchestration"] == "langgraph"
    obs = body["observability"]
    assert obs["checkpoint_store"] == "memory"
    assert obs["feature_flags"]["checkpoints_enabled"] is True
    assert obs["wandb"]["tracing_enabled_intent"] is False
    assert obs["wandb"]["tracing_ready"] is False
    assert obs["wandb"]["mandatory_run_tag_keys"]


def test_subagent_tool_via_supervisor(
    monkeypatch: pytest.MonkeyPatch,
    client: TestClient,
) -> None:
    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses("subagent_s1", {"task": "go"}, final_text="ok"),
    )
    r = client.post("/api/v1/trigger", json={"message": "call s1"})
    assert r.status_code == 200
    assert r.text == "ok"
    metrics = client.get("/metrics").text
    assert (
        'dalc_subagent_invocations_total{result="success",subagent="s1"}'
        in metrics
    )


def test_legacy_subagent_field_rejected(client: TestClient) -> None:
    r = client.post("/api/v1/trigger", json={"subagent": "nope"})
    assert r.status_code == 400
    assert "subagent" in r.json()["detail"].lower()


def test_rag_query_requires_config(client: TestClient) -> None:
    r = client.post("/api/v1/rag/query", json={"query": "x"})
    assert r.status_code == 503


def test_rag_query_proxies(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("HOSTED_AGENT_RAG_BASE_URL", "http://rag.local")

    mock_resp = MagicMock()
    mock_resp.json.return_value = {"hits": [], "related": []}
    mock_resp.raise_for_status = MagicMock()

    client_kwargs: list[dict] = []
    post_mocks: list[MagicMock] = []

    def capture_httpx_client(**kw: object) -> MagicMock:
        client_kwargs.append(kw)
        mock_cm = MagicMock()
        post = mock_cm.__enter__.return_value.post
        post.return_value = mock_resp
        post_mocks.append(post)
        mock_cm.__exit__.return_value = None
        return mock_cm

    with monkeypatch.context() as m:
        m.setattr("agent.app.httpx.Client", capture_httpx_client)
        r = client.post(
            "/api/v1/rag/query",
            json={"query": "hello", "expand_relationships": True},
        )
    assert r.status_code == 200
    assert r.json() == {"hits": [], "related": []}
    assert client_kwargs[0]["headers"].get("X-Request-Id")
    post_mocks[0].assert_called_once()
    args, pkw = post_mocks[0].call_args
    assert args[0] == "http://rag.local/v1/query"
    assert pkw["json"]["query"] == "hello"
    assert pkw["json"]["expand_relationships"] is True


def test_skill_load_unlocks_tool(client: TestClient) -> None:
    r = client.post("/api/v1/trigger", json={"load_skill": "bonus"})
    assert r.status_code == 200
    data = json.loads(r.text)
    assert data["activated_tools"] == ["sample.echo"]
    inv = client.post(
        "/api/v1/trigger",
        json={"tool": "sample.echo", "tool_arguments": {"message": "x"}},
    )
    assert inv.status_code == 200
    assert json.loads(inv.text)["result"]["echo"] == "x"


def test_tool_forbidden_without_skill_or_allowlist(client: TestClient) -> None:
    reset_skill_unlocked_tools()
    r = client.post(
        "/api/v1/trigger",
        json={"tool": "sample.echo", "tool_arguments": {}},
    )
    assert r.status_code == 403
