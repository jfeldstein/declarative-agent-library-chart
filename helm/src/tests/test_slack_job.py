"""Tests for ``hosted_agents.scrapers.slack_job``."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

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
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
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
    monkeypatch.setenv("SLACK_USER_TOKEN", "xoxp-test")
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
    hx_inst.post.assert_called_once()
