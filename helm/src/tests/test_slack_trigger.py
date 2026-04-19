"""Tests for Slack trigger bridge (HTTP Events API → ``run_trigger_graph``)."""

from __future__ import annotations

import hashlib
import hmac
import json
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from slack_sdk.signature import SignatureVerifier

from agent.app import create_app


def _sign_slack_body(signing_secret: str, body: bytes) -> dict[str, str]:
    ts = str(int(time.time()))
    basestring = f"v0:{ts}:{body.decode('utf-8')}"
    sig = hmac.new(
        signing_secret.encode("utf-8"),
        basestring.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return {
        "X-Slack-Request-Timestamp": ts,
        "X-Slack-Signature": f"v0={sig}",
    }


def _assert_sig_well_formed(
    signing_secret: str, body: bytes, hdrs: dict[str, str]
) -> None:
    v = SignatureVerifier(signing_secret)
    assert v.is_valid(
        body,
        hdrs["X-Slack-Request-Timestamp"],
        hdrs["X-Slack-Signature"],
    )


@pytest.fixture()
def signing_secret() -> str:
    return "test-signing-secret-not-real"


def test_slack_trigger_http_bad_signature_does_not_run_graph(
    monkeypatch: pytest.MonkeyPatch,
    signing_secret: str,
) -> None:
    """[DALC-REQ-SLACK-TRIGGER-003] Invalid signature rejects before ``run_trigger_graph``."""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_SIGNING_SECRET", signing_secret)
    calls: list[int] = []

    def _boom(_ctx):
        calls.append(1)
        return "no"

    app = create_app(system_prompt="system")
    body = json.dumps({"type": "event_callback"}).encode()
    with patch("agent.triggers.slack.dispatch.run_trigger_graph", _boom):
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/integrations/slack/events",
                content=body,
                headers={
                    "X-Slack-Request-Timestamp": "1",
                    "X-Slack-Signature": "v0=deadbeef",
                },
            )
    assert r.status_code == 401
    assert calls == []


def test_slack_trigger_url_challenge_does_not_run_graph(
    monkeypatch: pytest.MonkeyPatch,
    signing_secret: str,
) -> None:
    """[DALC-REQ-SLACK-TRIGGER-003] URL verification returns challenge without trigger."""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_SIGNING_SECRET", signing_secret)
    calls: list[int] = []

    def _boom(_ctx):
        calls.append(1)
        return "no"

    payload = {"type": "url_verification", "challenge": "abc123challenge"}
    body = json.dumps(payload).encode()
    hdrs = _sign_slack_body(signing_secret, body)
    _assert_sig_well_formed(signing_secret, body, hdrs)

    app = create_app(system_prompt="system")
    with patch("agent.triggers.slack.dispatch.run_trigger_graph", _boom):
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/integrations/slack/events",
                content=body,
                headers=hdrs,
            )
    assert r.status_code == 200
    assert r.json() == {"challenge": "abc123challenge"}
    assert calls == []


def test_slack_trigger_app_mention_invokes_run_trigger_graph(
    monkeypatch: pytest.MonkeyPatch,
    signing_secret: str,
) -> None:
    """[DALC-REQ-SLACK-TRIGGER-001] Happy-path ``app_mention`` schedules trigger pipeline."""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_SIGNING_SECRET", signing_secret)
    captured: list[object] = []

    def _capture(ctx):
        captured.append(ctx)
        return "ok"

    event = {
        "type": "app_mention",
        "channel": "C01234567",
        "user": "U01",
        "ts": "1234.5678",
        "text": "<@U012> hello there",
    }
    envelope = {
        "type": "event_callback",
        "event_id": "EvTESTONE",
        "event": event,
    }
    body = json.dumps(envelope).encode()
    hdrs = _sign_slack_body(signing_secret, body)

    app = create_app(system_prompt="system")
    with patch("agent.triggers.slack.dispatch.run_trigger_graph", _capture):
        with TestClient(app) as client:
            r = client.post(
                "/api/v1/integrations/slack/events",
                content=body,
                headers=hdrs,
            )
    assert r.status_code == 200
    assert r.json() == {"ok": True}
    assert len(captured) == 1
    ctx = captured[0]
    assert ctx.body.message == "hello there"
    assert ctx.body.thread_id == "slack:C01234567:1234.5678"
    assert ctx.slack_channel_id == "C01234567"


def test_slack_trigger_sources_do_not_reference_embed_route() -> None:
    """[DALC-REQ-SLACK-TRIGGER-002] Trigger bridge must not call managed RAG embed path."""
    root = Path(__file__).resolve().parents[1] / "agent" / "triggers" / "slack"
    for path in sorted(root.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "/v1/embed" not in text, path


def test_slack_trigger_metrics_counter_has_no_secret_labels() -> None:
    """[DALC-REQ-SLACK-TRIGGER-005] Prometheus labels are fixed strings (transport/result)."""
    from agent.metrics import SLACK_TRIGGER_INBOUND

    assert list(SLACK_TRIGGER_INBOUND._labelnames) == ["transport", "result"]  # noqa: SLF001


def test_slack_trigger_event_dedupe_skips_second_delivery(
    monkeypatch: pytest.MonkeyPatch,
    signing_secret: str,
) -> None:
    """[DALC-REQ-SLACK-TRIGGER-001] Duplicate Slack ``event_id`` does not schedule twice."""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_SIGNING_SECRET", signing_secret)
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_EVENT_DEDUPE", "true")
    calls: list[int] = []

    def _count(_ctx):
        calls.append(1)
        return "ok"

    def _envelope() -> bytes:
        event = {
            "type": "app_mention",
            "channel": "C09",
            "user": "U02",
            "ts": "99.01",
            "text": "<@U9> twice",
        }
        return json.dumps(
            {
                "type": "event_callback",
                "event_id": "EvDEDUPE",
                "event": event,
            }
        ).encode()

    app = create_app(system_prompt="system")
    with patch("agent.triggers.slack.dispatch.run_trigger_graph", _count):
        with TestClient(app) as client:
            for _ in range(2):
                b = _envelope()
                h = _sign_slack_body(signing_secret, b)
                r = client.post(
                    "/api/v1/integrations/slack/events",
                    content=b,
                    headers=h,
                )
                assert r.status_code == 200
    assert len(calls) == 1


def test_slack_trigger_posts_graph_output_to_slack_when_client_available(
    monkeypatch: pytest.MonkeyPatch,
    signing_secret: str,
) -> None:
    """Trigger output is posted back to the Slack thread when a Web API client can be built."""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TRIGGER_SIGNING_SECRET", signing_secret)
    mock_client = MagicMock()

    event = {
        "type": "app_mention",
        "channel": "C01234567",
        "user": "U01",
        "ts": "1234.5678",
        "text": "<@U012> hello there",
    }
    envelope = {
        "type": "event_callback",
        "event_id": "EvPOST",
        "event": event,
    }
    body = json.dumps(envelope).encode()
    hdrs = _sign_slack_body(signing_secret, body)

    app = create_app(system_prompt='Respond, "Hello :wave:"')
    with patch(
        "agent.triggers.slack.dispatch.run_trigger_graph",
        return_value="Hello :wave:",
    ):
        with patch(
            "agent.triggers.slack.dispatch._slack_client_for_trigger_reply",
            return_value=mock_client,
        ):
            with TestClient(app) as client:
                r = client.post(
                    "/api/v1/integrations/slack/events",
                    content=body,
                    headers=hdrs,
                )
    assert r.status_code == 200
    mock_client.chat_postMessage.assert_called_once_with(
        channel="C01234567",
        text="Hello :wave:",
        thread_ts="1234.5678",
    )
