"""Observability: Prometheus metrics and request correlation.

Traceability: [DALC-VER-002] (see matrix for per-requirement pytest nodes).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from hosted_agents.app import create_app
from hosted_agents.skills_state import reset_skill_unlocked_tools
from tests.conftest import patch_supervisor_fake_model, tool_then_text_responses


def _metrics_text(client: TestClient) -> str:
    r = client.get("/metrics")
    assert r.status_code == 200
    return r.text


def test_metrics_endpoint_exposes_registry() -> None:
    """[DALC-REQ-O11Y-SCRAPE-001]"""
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    text = _metrics_text(client)
    assert "# TYPE " in text
    assert "agent_runtime_http_trigger" in text


def test_trigger_success_increments_counter() -> None:
    """[DALC-REQ-O11Y-SCRAPE-002]"""
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    before = _metrics_text(client)
    client.post("/api/v1/trigger")
    after = _metrics_text(client)
    assert 'agent_runtime_http_trigger_requests_total{result="success"}' in after
    # Counter should have increased vs initial scrape (may be same line with higher value)
    assert after.count("agent_runtime_http_trigger_requests_total") >= before.count(
        "agent_runtime_http_trigger_requests_total",
    )


def test_trigger_client_error_increments_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-O11Y-SCRAPE-002]"""
    from hosted_agents.env import SYSTEM_PROMPT_ENV_KEY

    monkeypatch.setenv(SYSTEM_PROMPT_ENV_KEY, "   ")
    app = create_app()
    client = TestClient(app)
    r = client.post("/api/v1/trigger")
    assert r.status_code == 400

    text = _metrics_text(client)
    assert 'agent_runtime_http_trigger_requests_total{result="client_error"}' in text


def test_x_request_id_echo_and_generation() -> None:
    """[DALC-REQ-O11Y-LOGS-002]"""
    app = create_app(system_prompt='Respond, "x"')
    client = TestClient(app)
    r = client.post("/api/v1/trigger", headers={"X-Request-Id": "fixed-id"})
    assert r.headers.get("x-request-id") == "fixed-id"
    r2 = client.post("/api/v1/trigger")
    assert r2.headers.get("x-request-id")
    assert r2.headers.get("x-request-id") != "fixed-id"


def test_trigger_forwards_x_request_id_to_rag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_RAG_BASE_URL", "http://rag:8090")
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps([{"name": "rag", "role": "rag", "description": "RAG"}]),
    )
    mock_resp = MagicMock()
    mock_resp.text = "{}"
    mock_resp.raise_for_status = MagicMock()
    client_kw: dict = {}

    def capture_httpx_client(**kw: object) -> MagicMock:
        client_kw.update(kw)
        mock_cm = MagicMock()
        mock_cm.__enter__.return_value.post.return_value = mock_resp
        mock_cm.__exit__.return_value = None
        return mock_cm

    monkeypatch.setattr(
        "hosted_agents.subagent_exec.httpx.Client", capture_httpx_client
    )
    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses("subagent_rag", {"query": "q"}, final_text="ok"),
    )
    client = TestClient(create_app(system_prompt='Respond, "M"'))
    client.post(
        "/api/v1/trigger",
        headers={"X-Request-Id": "upstream-abc"},
        json={"message": "rag please"},
    )
    assert client_kw["headers"]["X-Request-Id"] == "upstream-abc"


def test_subagent_and_skill_and_mcp_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-O11Y-SCRAPE-003]"""
    reset_skill_unlocked_tools()
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [
                {"name": "s1", "systemPrompt": 'Respond, "S"', "description": "s1"},
                {"name": "missing", "systemPrompt": "", "description": "broken"},
            ],
        ),
    )
    monkeypatch.setenv(
        "HOSTED_AGENT_SKILLS_JSON",
        json.dumps([{"name": "sk", "prompt": "p", "extra_tools": ["sample.echo"]}]),
    )
    monkeypatch.setenv("HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps([]))
    client = TestClient(create_app(system_prompt='Respond, "M"'))

    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses("subagent_s1", {"task": "t"}, final_text="a"),
    )
    client.post("/api/v1/trigger", json={"message": "call s1"})

    def _missing_factory() -> object:
        from hosted_agents.chat_model import FakeToolChatModel
        from langchain_core.messages import AIMessage

        return FakeToolChatModel(
            responses=[
                AIMessage(
                    content="",
                    tool_calls=[
                        {
                            "name": "subagent_missing",
                            "args": {"task": ""},
                            "id": "m1",
                            "type": "tool_call",
                        },
                    ],
                ),
                AIMessage(content="b"),
            ],
        )

    monkeypatch.setattr(
        "hosted_agents.supervisor.resolve_chat_model",
        _missing_factory,
    )
    client.post("/api/v1/trigger", json={"message": "call missing"})

    client.post("/api/v1/trigger", json={"load_skill": "sk"})
    client.post("/api/v1/trigger", json={"load_skill": "nope"})
    client.post("/api/v1/trigger", json={"tool": "sample.echo", "tool_arguments": {}})

    text = _metrics_text(client)
    assert (
        'agent_runtime_subagent_invocations_total{result="success",subagent="s1"}'
        in text
    )
    assert (
        'agent_runtime_subagent_invocations_total{result="error",subagent="missing"}'
        in text
    )
    assert 'agent_runtime_skill_loads_total{result="success",skill="sk"}' in text
    assert 'agent_runtime_skill_loads_total{result="error",skill="nope"}' in text
    assert (
        'agent_runtime_mcp_tool_calls_total{result="success",tool="sample.echo"}'
        in text
    )


def test_json_log_format_emits_message_key() -> None:
    """[DALC-REQ-O11Y-LOGS-001]"""
    runtime = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["HOSTED_AGENT_LOG_FORMAT"] = "json"
    env["PYTHONPATH"] = str(runtime)
    code = """
from hosted_agents.o11y_logging import configure_request_logging, get_logger
configure_request_logging()
get_logger().info("hello_probe", request_id="abc")
"""
    proc = subprocess.run(
        [sys.executable, "-c", code],
        cwd=str(runtime),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    line = proc.stdout.strip().splitlines()[-1]
    data = json.loads(line)
    assert data["message"] == "hello_probe"
    assert data["request_id"] == "abc"
