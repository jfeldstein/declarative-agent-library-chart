"""Subagent roles: metrics (Prometheus text) vs rag (proxy to RAG /v1/query)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from agent.app import create_app
from tests.conftest import patch_supervisor_fake_model, tool_then_text_responses


def test_metrics_role_returns_prometheus_text(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [
                {
                    "name": "metrics",
                    "role": "metrics",
                    "exposeAsTool": True,
                    "description": "Return this process Prometheus metrics snapshot",
                },
            ],
        ),
    )
    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses("subagent_metrics", {}, final_text="skip"),
    )
    client = TestClient(create_app(system_prompt='Respond, "M"'))
    r = client.post("/api/v1/trigger", json={"message": "scrape metrics"})
    assert r.status_code == 200
    # HTTP body is the supervisor's final turn; Prometheus text is produced inside the tool.
    prom = client.get("/metrics").text
    assert "dalc_http_trigger" in prom
    assert "dalc_subagent_invocations_total" in prom


def test_rag_role_proxies_to_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_RAG_BASE_URL", "http://rag:8090")
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [
                {
                    "name": "rag",
                    "role": "rag",
                    "systemPrompt": "",
                    "description": "Query the configured RAG HTTP API",
                },
            ],
        ),
    )
    mock_resp = MagicMock()
    mock_resp.text = '{"hits":[]}'
    mock_resp.raise_for_status = MagicMock()
    client_kw: dict = {}
    post_mocks: list[MagicMock] = []

    def capture_httpx_client(**kw: object) -> MagicMock:
        client_kw.update(kw)
        mock_cm = MagicMock()
        post = mock_cm.__enter__.return_value.post
        post.return_value = mock_resp
        post_mocks.append(post)
        mock_cm.__exit__.return_value = None
        return mock_cm

    monkeypatch.setattr("agent.subagent_exec.httpx.Client", capture_httpx_client)

    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses(
            "subagent_rag",
            {"query": "find docs", "scope": "s1"},
            final_text="done",
        ),
    )

    client = TestClient(create_app(system_prompt='Respond, "M"'))
    r = client.post("/api/v1/trigger", json={"message": "search rag"})
    assert r.status_code == 200
    assert r.text == "done"
    assert client_kw["headers"].get("X-Request-Id")
    args, kwargs = post_mocks[0].call_args
    assert args[0] == "http://rag:8090/v1/query"
    assert kwargs["json"]["query"] == "find docs"
    assert kwargs["json"]["scope"] == "s1"


def test_rag_role_requires_query(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_RAG_BASE_URL", "http://rag:8090")
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps([{"name": "rag", "role": "rag", "description": "RAG"}]),
    )
    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses(
            "subagent_rag",
            {"query": "", "scope": "default"},
            final_text="x",
        ),
    )
    client = TestClient(create_app(system_prompt='Respond, "M"'))
    r = client.post("/api/v1/trigger", json={"message": "bad rag"})
    assert r.status_code == 400
