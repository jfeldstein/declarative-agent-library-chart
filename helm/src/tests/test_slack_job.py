"""Tests for ``hosted_agents.scrapers.slack_job``.

Traceability: exercises slack scraper job JSON validation, normalization, and RAG embed wiring.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from hosted_agents.scrapers import slack_job


def test_ts_window() -> None:
    lo, hi = slack_job._ts_window("1000.0", 1.0, 2.0)
    assert slack_job._slack_ts_to_float(lo) < 1000.0
    assert slack_job._slack_ts_to_float(hi) > 1000.0


def test_build_items_from_messages_dedupes() -> None:
    msgs = [
        {"text": "a", "channel": "C1", "ts": "1.0", "team": "T1"},
        {"text": "b", "channel": "C1", "ts": "1.0", "team": "T1"},
    ]
    items = slack_job._build_items_from_messages(msgs)
    assert len(items) == 1


def test_build_items_metadata_team_thread_compact_ts() -> None:
    msgs = [
        {
            "text": "t",
            "channel": "C1",
            "ts": "1000.000002",
            "team": "T9",
            "thread_ts": "999.0",
        },
    ]
    items = slack_job._build_items_from_messages(msgs)
    meta = items[0]["metadata"]
    assert meta["slack_team_id"] == "T9"
    assert meta["slack_thread_ts"] == "999.0"
    assert meta["slack_ts_compact"] == "1000000002"


def test_redact_token_like_strips_slack_token_patterns() -> None:
    # Avoid embedding a contiguous Slack-token-shaped literal (GitHub push protection).
    frag = "".join(("xox", "b-", "1234567890-1234567890123-AbCdEfGhIjKlMnOpQrStUvWxYz"))
    raw = "boom " + frag
    red = slack_job._redact_token_like(raw)
    assert "".join(("xox", "b-")) not in red
    assert "<redacted>" in red


def test_normalize_slack_job_rejects_unknown_source() -> None:
    with pytest.raises(SystemExit) as excinfo:
        slack_job._normalize_slack_job({"source": "not_a_slack_job"})
    assert excinfo.value.code == 1


def test_normalize_slack_search_requires_query() -> None:
    with pytest.raises(SystemExit) as excinfo:
        slack_job._normalize_slack_job({"source": "slack_search", "query": "  "})
    assert excinfo.value.code == 1


def test_normalize_slack_channel_requires_conversation_id() -> None:
    with pytest.raises(SystemExit) as excinfo:
        slack_job._normalize_slack_job({"source": "slack_channel", "conversationId": ""})
    assert excinfo.value.code == 1


def test_rts_messages_parses_results() -> None:
    page = {
        "ok": True,
        "results": {"messages": [{"channel_id": "C1", "message_ts": "1.1"}]},
    }
    assert len(slack_job._rts_messages(page)) == 1


@patch("hosted_agents.scrapers.slack_job.httpx.Client")
@patch("hosted_agents.scrapers.slack_job.WebClient")
def test_run_slack_channel_posts_embed(
    mock_wc_class, mock_hx_cls, tmp_path, monkeypatch
) -> None:
    cfg = {
        "source": "slack_channel",
        "conversationId": "CXYZ",
    }
    cfg_path = tmp_path / "job.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setenv("SCRAPER_JOB_CONFIG", str(cfg_path))
    monkeypatch.setenv("SLACK_BOT_TOKEN", "test-bot-token-not-real")
    monkeypatch.setenv("SLACK_STATE_DIR", str(tmp_path / "st"))
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag.local")
    monkeypatch.setenv("SCRAPER_METRICS_ADDR", "")

    mock_bot = MagicMock()
    mock_wc_class.return_value = mock_bot
    mock_bot.conversations_history.return_value = {
        "ok": True,
        "messages": [{"text": "m", "channel": "CXYZ", "ts": "99.000001", "team": "T1"}],
        "response_metadata": {},
    }
    hx_inst = MagicMock()
    mock_hx_cls.return_value.__enter__.return_value = hx_inst
    resp = MagicMock()
    hx_inst.post.return_value = resp
    resp.raise_for_status = MagicMock()

    slack_job.run()
    mock_bot.conversations_history.assert_called()
    args, kwargs = mock_bot.conversations_history.call_args
    assert kwargs.get("limit") == 200
    hx_inst.post.assert_called_once()


@patch("hosted_agents.scrapers.slack_job.httpx.Client")
@patch("hosted_agents.scrapers.slack_job.WebClient")
def test_run_slack_search_posts_embed(
    mock_wc_class, mock_hx_cls, tmp_path, monkeypatch
) -> None:
    cfg = {
        "source": "slack_search",
        "query": "hello",
        "contextBeforeMinutes": 1,
        "contextAfterMinutes": 1,
    }
    cfg_path = tmp_path / "job.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    monkeypatch.setenv("SCRAPER_JOB_CONFIG", str(cfg_path))
    monkeypatch.setenv("SLACK_USER_TOKEN", "test-user-token-not-real")
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag.local")
    monkeypatch.setenv("SCRAPER_METRICS_ADDR", "")

    mock_user = MagicMock()
    mock_wc_class.return_value = mock_user
    mock_user.api_call.return_value = {
        "ok": True,
        "results": {
            "messages": [
                {
                    "channel_id": "C1",
                    "message_ts": "1000.0",
                    "thread_ts": "1000.0",
                },
            ],
        },
    }
    mock_user.conversations_replies.return_value = {
        "ok": True,
        "messages": [{"text": "t", "channel": "C1", "ts": "1000.0", "team": "T1"}],
        "response_metadata": {},
    }
    mock_user.conversations_history.return_value = {
        "ok": True,
        "messages": [],
        "response_metadata": {},
    }

    hx_inst = MagicMock()
    mock_hx_cls.return_value.__enter__.return_value = hx_inst
    resp = MagicMock()
    hx_inst.post.return_value = resp
    resp.raise_for_status = MagicMock()

    slack_job.run()
    mock_user.api_call.assert_called()
    assert mock_user.api_call.call_args[0][0] == "assistant.search.context"
    assert mock_user.api_call.call_args[1]["json"]["limit"] == 20
    hx_inst.post.assert_called_once()


def test_run_invalid_job_config_exits_before_slack_client(
    tmp_path, monkeypatch, capsys
) -> None:
    cfg_path = tmp_path / "job.json"
    cfg_path.write_text(json.dumps({"source": "slack_search"}), encoding="utf-8")
    monkeypatch.setenv("SCRAPER_JOB_CONFIG", str(cfg_path))
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag.local")
    monkeypatch.setenv("SCRAPER_METRICS_ADDR", "")
    monkeypatch.setenv("SLACK_USER_TOKEN", "test-user-token-not-real")

    with patch("hosted_agents.scrapers.slack_job.WebClient") as mock_wc:
        with pytest.raises(SystemExit) as ei:
            slack_job.run()
        assert ei.value.code == 1
        mock_wc.assert_not_called()
    err = capsys.readouterr().err
    assert "query" in err.lower()
