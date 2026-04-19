"""Tests for LLM-time Slack tools (see per-test docstrings for [DALC-REQ-SLACK-TOOLS-*])."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest
from slack_sdk.errors import SlackApiError

from hosted_agents.tools.dispatch import invoke_tool
from hosted_agents.tools.slack.support import _slack_req_id_from_headers


@pytest.fixture(autouse=True)
def _clear_slack_tools_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN", raising=False)


def test_slack_post_simulated_without_token() -> None:
    """[DALC-REQ-SLACK-TOOLS-001] Simulated path does not perform HTTP."""
    out = invoke_tool(
        "slack.post_message",
        {"channel_id": "C123", "text": "hi"},
    )
    assert out["ok"] is True
    assert out.get("simulated") is True
    assert "ts" in out


def test_slack_post_real_calls_chat_post_message(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-SLACK-TOOLS-003]"""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN", "xoxb-test-token")

    mock_resp = MagicMock()
    mock_resp.data = {"ok": True, "ts": "1234.5678", "channel": "C123"}

    with patch("hosted_agents.tools.slack.support.WebClient") as wc:
        inst = wc.return_value
        inst.chat_postMessage.return_value = mock_resp
        out = invoke_tool(
            "slack.post_message",
            {"channel_id": "C123", "text": "hello"},
        )

    inst.chat_postMessage.assert_called_once()
    kwargs = inst.chat_postMessage.call_args.kwargs
    assert kwargs["channel"] == "C123"
    assert kwargs["text"] == "hello"
    assert out["ok"] is True
    assert out.get("simulated") is False
    assert out["ts"] == "1234.5678"


def test_slack_api_error_has_no_token_in_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-SLACK-TOOLS-006]"""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN", "xoxb-secret")

    resp = MagicMock()
    resp.data = {"ok": False, "error": "channel_not_found"}
    resp.headers = {}
    err = SlackApiError(message="slack failed", response=resp)

    with patch("hosted_agents.tools.slack.support.WebClient") as wc:
        inst = wc.return_value
        inst.chat_postMessage.side_effect = err
        out = invoke_tool(
            "slack.post_message",
            {"channel_id": "C999", "text": "nope"},
        )

    assert out["ok"] is False
    assert out.get("error") == "channel_not_found"
    dumped = json.dumps(out)
    assert "xoxb" not in dumped


def test_history_tools_simulated_without_token() -> None:
    """[DALC-REQ-SLACK-TOOLS-004]"""
    h = invoke_tool(
        "slack.conversations_history",
        {"channel_id": "C1"},
    )
    assert h["ok"] is True
    assert h.get("simulated") is True
    assert h["messages"] == []

    r = invoke_tool(
        "slack.conversations_replies",
        {"channel_id": "C1", "thread_ts": "1.0"},
    )
    assert r["ok"] is True
    assert r.get("simulated") is True


def test_reactions_real_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-SLACK-TOOLS-003]"""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN", "xoxb-test")

    mock_add = MagicMock()
    mock_add.data = {"ok": True}
    mock_rm = MagicMock()
    mock_rm.data = {"ok": True}

    with patch("hosted_agents.tools.slack.support.WebClient") as wc:
        inst = wc.return_value
        inst.reactions_add.return_value = mock_add
        inst.reactions_remove.return_value = mock_rm

        a = invoke_tool(
            "slack.reactions_add",
            {"channel_id": "C1", "timestamp": "1.0", "name": "thumbsup"},
        )
        assert a["ok"] is True
        inst.reactions_add.assert_called_once()

        b = invoke_tool(
            "slack.reactions_remove",
            {"channel_id": "C1", "ts": "1.0", "emoji": "thumbsup"},
        )
        assert b["ok"] is True
        inst.reactions_remove.assert_called_once()


def test_chat_update_and_history_real_path(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-SLACK-TOOLS-003] [DALC-REQ-SLACK-TOOLS-004]"""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN", "xoxb-test")

    upd = MagicMock()
    upd.data = {"ok": True, "ts": "9.9"}
    hist = MagicMock()
    hist.data = {
        "ok": True,
        "messages": [{"ts": "1", "user": "U1", "text": "a", "type": "message"}],
    }
    rep = MagicMock()
    rep.data = {
        "ok": True,
        "messages": [{"ts": "2", "user": "U2", "text": "b", "type": "message"}],
    }

    with patch("hosted_agents.tools.slack.support.WebClient") as wc:
        inst = wc.return_value
        inst.chat_update.return_value = upd
        inst.conversations_history.return_value = hist
        inst.conversations_replies.return_value = rep

        u = invoke_tool(
            "slack.chat_update",
            {"channel_id": "C1", "ts": "1.0", "text": "edited"},
        )
        assert u["ok"] is True

        h = invoke_tool(
            "slack.conversations_history",
            {"channel_id": "C1", "limit": 10},
        )
        assert h["messages"][0]["text"] == "a"

        r = invoke_tool(
            "slack.conversations_replies",
            {"channel_id": "C1", "thread_ts": "1.0"},
        )
        assert r["messages"][0]["text"] == "b"


def test_slack_req_id_from_headers_never_raises() -> None:
    """[DALC-REQ-SLACK-TOOLS-006] Headers may be non-mapping; extraction must stay safe."""
    assert _slack_req_id_from_headers(None) == ""

    class NoGet:
        pass

    assert _slack_req_id_from_headers(NoGet()) == ""

    class WithGet:
        def get(self, key: str, default: object = None) -> object:
            if key == "x-slack-req-id":
                return "abc"
            return default

    assert _slack_req_id_from_headers(WithGet()) == "abc"


def test_tools_impl_has_no_embed_client_import() -> None:
    """[DALC-REQ-SLACK-TOOLS-001] Guard: Slack tools modules must not pull RAG embed client."""
    import hosted_agents.tools.slack.history as sch
    import hosted_agents.tools.slack.post as sp
    import hosted_agents.tools.slack.reactions as sr

    for mod in (sp, sr, sch):
        src = open(mod.__file__, encoding="utf-8").read()
        assert "/v1/embed" not in src
