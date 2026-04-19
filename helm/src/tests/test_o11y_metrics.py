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

from agent.app import create_app
from agent.skills_state import reset_skill_unlocked_tools
from agent.trigger_errors import TriggerHttpError
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
    assert "dalc_trigger_requests_total" in text


def test_trigger_success_increments_counter() -> None:
    """[DALC-REQ-O11Y-SCRAPE-002] success classification."""
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    before = _metrics_text(client)
    client.post("/api/v1/trigger")
    after = _metrics_text(client)
    assert (
        'dalc_trigger_requests_total{result="success",transport="http",trigger="http"}'
        in after
    )
    # Counter should have increased vs initial scrape (may be same line with higher value)
    assert after.count("dalc_trigger_requests_total") >= before.count(
        "dalc_trigger_requests_total",
    )


def test_trigger_client_error_increments_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-O11Y-SCRAPE-002] client_error classification."""
    from agent.env import SYSTEM_PROMPT_ENV_KEY

    monkeypatch.setenv(SYSTEM_PROMPT_ENV_KEY, "   ")
    app = create_app()
    client = TestClient(app)
    r = client.post("/api/v1/trigger")
    assert r.status_code == 400

    text = _metrics_text(client)
    assert (
        'dalc_trigger_requests_total{result="client_error",transport="http",trigger="http"}'
        in text
    )


def test_x_request_id_echo_and_generation() -> None:
    """[DALC-REQ-O11Y-LOGS-002] HTTP header echo/generation."""
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

    monkeypatch.setattr("agent.subagent_exec.httpx.Client", capture_httpx_client)
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
        from agent.chat_model import FakeToolChatModel
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
        "agent.supervisor.resolve_chat_model",
        _missing_factory,
    )
    client.post("/api/v1/trigger", json={"message": "call missing"})

    client.post("/api/v1/trigger", json={"load_skill": "sk"})
    client.post("/api/v1/trigger", json={"load_skill": "nope"})
    client.post("/api/v1/trigger", json={"tool": "sample.echo", "tool_arguments": {}})

    text = _metrics_text(client)
    assert (
        'dalc_subagent_invocations_total{result="success",subagent="s1"}'
        in text
    )
    assert (
        'dalc_subagent_invocations_total{result="error",subagent="missing"}'
        in text
    )
    assert 'dalc_skill_loads_total{result="success",skill="sk"}' in text
    assert 'dalc_skill_loads_total{result="error",skill="nope"}' in text
    assert (
        'dalc_tool_calls_total{result="success",tool="sample.echo"}'
        in text
    )


def test_json_logs_emit_structured_correlation_for_trigger_route() -> None:
    """[DALC-REQ-O11Y-LOGS-002] Structured JSON logs include ``request_id`` on the trigger path."""
    runtime = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["HOSTED_AGENT_LOG_FORMAT"] = "json"
    env["PYTHONPATH"] = str(runtime)
    script = """
from agent.o11y_logging import reset_logging_for_tests

reset_logging_for_tests()
from agent.app import create_app
from fastapi.testclient import TestClient

app = create_app(system_prompt='Respond, "Probe"')
client = TestClient(app)
res = client.post(
    "/api/v1/trigger",
    headers={"X-Request-Id": "structured-log-parity-id"},
)
assert res.status_code == 200
"""
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(runtime),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    records: list[dict] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    matched = [
        row
        for row in records
        if row.get("request_id") == "structured-log-parity-id"
        and row.get("message") in ("http_request_start", "http_request_end")
    ]
    assert matched, proc.stdout


def test_trigger_unhandled_exception_increments_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-O11Y-SCRAPE-002] Unhandled ``Exception`` maps to ``server_error``."""

    def _boom(_ctx: object) -> str:
        raise RuntimeError("simulated handler failure")

    monkeypatch.setattr("agent.app.run_trigger_graph", _boom)
    client = TestClient(
        create_app(system_prompt='Respond, "Hi"'), raise_server_exceptions=False
    )
    before = _metrics_text(client)
    r = client.post("/api/v1/trigger", json={"message": "hi"})
    assert r.status_code == 500
    after = _metrics_text(client)
    assert (
        'dalc_trigger_requests_total{result="server_error",transport="http",trigger="http"}'
        in after
    )
    assert after.count("dalc_trigger_requests_total") >= before.count(
        "dalc_trigger_requests_total",
    )


def test_trigger_http_error_5xx_increments_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-O11Y-SCRAPE-002] ``TriggerHttpError`` with status ≥500 maps to ``server_error``."""

    def _raise(_ctx: object) -> str:
        raise TriggerHttpError(503, "upstream unavailable")

    monkeypatch.setattr("agent.app.run_trigger_graph", _raise)
    client = TestClient(create_app(system_prompt='Respond, "Hi"'))
    before = _metrics_text(client)
    r = client.post("/api/v1/trigger", json={"message": "hi"})
    assert r.status_code == 503
    after = _metrics_text(client)
    assert (
        'dalc_trigger_requests_total{result="server_error",transport="http",trigger="http"}'
        in after
    )
    assert after.count("dalc_trigger_requests_total") >= before.count(
        "dalc_trigger_requests_total",
    )


def test_trigger_http_error_4xx_stays_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-O11Y-SCRAPE-002] ``TriggerHttpError`` with status <500 maps to ``client_error``."""

    def _raise(_ctx: object) -> str:
        raise TriggerHttpError(404, "missing")

    monkeypatch.setattr("agent.app.run_trigger_graph", _raise)
    client = TestClient(create_app(system_prompt='Respond, "Hi"'))
    before = _metrics_text(client)
    r = client.post("/api/v1/trigger", json={"message": "hi"})
    assert r.status_code == 404
    after = _metrics_text(client)
    assert (
        'dalc_trigger_requests_total{result="client_error",transport="http",trigger="http"}'
        in after
    )
    assert after.count("dalc_trigger_requests_total") >= before.count(
        "dalc_trigger_requests_total",
    )


def test_json_log_format_emits_message_key() -> None:
    """[DALC-REQ-O11Y-LOGS-001]"""
    runtime = Path(__file__).resolve().parent.parent
    env = os.environ.copy()
    env["HOSTED_AGENT_LOG_FORMAT"] = "json"
    env["PYTHONPATH"] = str(runtime)
    code = """
from agent.o11y_logging import configure_request_logging, get_logger
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
    assert data["service"] == "declarative-agent-library-chart"
