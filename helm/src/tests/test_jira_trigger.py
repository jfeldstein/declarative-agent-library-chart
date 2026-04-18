"""Tests for Jira trigger bridge (HTTP webhook → ``run_trigger_graph``)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from hosted_agents.app import create_app


@pytest.fixture()
def webhook_secret() -> str:
    return "test-jira-webhook-secret-not-real"


def test_jira_trigger_http_bad_secret_does_not_run_graph(
    monkeypatch: pytest.MonkeyPatch,
    webhook_secret: str,
) -> None:
    """[DALC-REQ-JIRA-TRIGGER-003] Invalid shared secret rejects before ``run_trigger_graph``."""
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET", webhook_secret)
    calls: list[int] = []

    def _boom(_ctx):
        calls.append(1)
        return "no"

    app = create_app(system_prompt="system")
    body = json.dumps({"webhookEvent": "jira:issue_updated"}).encode()
    with patch("hosted_agents.jira_trigger.dispatch.run_trigger_graph", _boom):
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/integrations/jira/webhook",
                content=body,
                params={"secret": "wrong"},
            )
    assert r.status_code == 401
    assert calls == []


def test_jira_trigger_http_invalid_json_does_not_run_graph(
    monkeypatch: pytest.MonkeyPatch,
    webhook_secret: str,
) -> None:
    """[DALC-REQ-JIRA-TRIGGER-003] Bad JSON rejects without invoking ``run_trigger_graph``."""
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET", webhook_secret)
    calls: list[int] = []

    def _boom(_ctx):
        calls.append(1)
        return "no"

    app = create_app(system_prompt="system")
    with patch("hosted_agents.jira_trigger.dispatch.run_trigger_graph", _boom):
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/integrations/jira/webhook?secret=" + webhook_secret,
                content=b"not-json",
            )
    assert r.status_code == 400
    assert calls == []


def test_jira_trigger_issue_updated_invokes_run_trigger_graph(
    monkeypatch: pytest.MonkeyPatch,
    webhook_secret: str,
) -> None:
    """[DALC-REQ-JIRA-TRIGGER-001] Happy-path webhook schedules trigger pipeline."""
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET", webhook_secret)
    captured: list[object] = []

    def _capture(ctx):
        captured.append(ctx)
        return "ok"

    payload = {
        "webhookEvent": "jira:issue_updated",
        "issue": {
            "key": "PROJ-42",
            "fields": {
                "summary": "Hello world",
                "project": {"key": "PROJ"},
            },
        },
    }
    body = json.dumps(payload).encode()

    app = create_app(system_prompt="system")
    with patch("hosted_agents.jira_trigger.dispatch.run_trigger_graph", _capture):
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/integrations/jira/webhook",
                content=body,
                params={"secret": webhook_secret},
                headers={"X-Atlassian-Webhook-Identifier": "wh-001"},
            )
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert len(captured) == 1
    ctx = captured[0]
    assert ctx.body.message is not None
    assert "PROJ-42" in ctx.body.message
    assert ctx.body.thread_id is not None
    assert ctx.body.thread_id.startswith("jira:PROJ-42:")
    assert ctx.jira_issue_key == "PROJ-42"
    assert ctx.jira_project_key == "PROJ"
    assert ctx.jira_webhook_event == "jira:issue_updated"


def test_jira_trigger_sources_do_not_reference_embed_route() -> None:
    """[DALC-REQ-JIRA-TRIGGER-002] Trigger bridge must not call managed RAG embed path."""
    root = Path(__file__).resolve().parents[1] / "hosted_agents" / "jira_trigger"
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "/v1/embed" not in text, path


def test_jira_trigger_metrics_counter_has_no_secret_labels() -> None:
    """[DALC-REQ-JIRA-TRIGGER-005] Prometheus labels are fixed strings (transport/result)."""
    from hosted_agents.metrics import JIRA_TRIGGER_INBOUND

    assert list(JIRA_TRIGGER_INBOUND._labelnames) == ["transport", "result"]  # noqa: SLF001


def test_jira_trigger_event_dedupe_skips_second_delivery(
    monkeypatch: pytest.MonkeyPatch,
    webhook_secret: str,
) -> None:
    """[DALC-REQ-JIRA-TRIGGER-001] Duplicate webhook identifier does not schedule twice."""
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET", webhook_secret)
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_EVENT_DEDUPE", "true")
    calls: list[int] = []

    def _count(_ctx):
        calls.append(1)
        return "ok"

    def _payload() -> bytes:
        return json.dumps(
            {
                "webhookEvent": "jira:issue_updated",
                "issue": {
                    "key": "PROJ-9",
                    "fields": {"summary": "x", "project": {"key": "PROJ"}},
                },
            }
        ).encode()

    app = create_app(system_prompt="system")
    with patch("hosted_agents.jira_trigger.dispatch.run_trigger_graph", _count):
        with TestClient(app) as client:
            hdrs = {"X-Atlassian-Webhook-Identifier": "wh-dedupe"}
            r1 = client.post(
                "/api/v1/integrations/jira/webhook",
                content=_payload(),
                params={"secret": webhook_secret},
                headers=hdrs,
            )
            r2 = client.post(
                "/api/v1/integrations/jira/webhook",
                content=_payload(),
                params={"secret": webhook_secret},
                headers=hdrs,
            )
    assert r1.status_code == 200
    assert r2.status_code == 200
    assert len(calls) == 1


def test_jira_tools_can_coexist_with_trigger_runtime_paths(
    monkeypatch: pytest.MonkeyPatch,
    webhook_secret: str,
) -> None:
    """[DALC-REQ-JIRA-TRIGGER-002] Smoke: trigger uses graph entrypoint; tools are separate."""
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TRIGGER_WEBHOOK_SECRET", webhook_secret)
    seen: list[str] = []

    def _capture(ctx):
        seen.append(ctx.jira_issue_key or "")
        return "ok"

    body = json.dumps(
        {
            "webhookEvent": "jira:issue_updated",
            "issue": {
                "key": "ABC-1",
                "fields": {"summary": "t", "project": {"key": "ABC"}},
            },
        }
    ).encode()
    app = create_app(system_prompt="system")
    with patch("hosted_agents.jira_trigger.dispatch.run_trigger_graph", _capture):
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/integrations/jira/webhook",
                content=body,
                params={"secret": webhook_secret},
            )
    assert r.status_code == 200
    assert seen == ["ABC-1"]
