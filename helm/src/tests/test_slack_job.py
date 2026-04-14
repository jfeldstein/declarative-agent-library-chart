"""Tests for ``hosted_agents.scrapers.slack_job``."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from hosted_agents.scrapers import slack_job


def test_load_searches_valid(tmp_path, monkeypatch) -> None:
    p = tmp_path / "s.json"
    p.write_text(
        json.dumps(
            [{"id": "a", "type": "search_messages", "query": "x", "limit": 2}],
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("SLACK_SCRAPER_SEARCHES_FILE", str(p))
    monkeypatch.delenv("SLACK_SCRAPER_SEARCHES_JSON", raising=False)
    s = slack_job._load_searches()
    assert len(s) == 1
    assert s[0]["id"] == "a"


def test_build_items_deterministic_entity_id() -> None:
    msgs = [
        {
            "text": "hi",
            "channel": "C1",
            "ts": "1.0",
            "team": "T9",
        },
    ]
    items = slack_job._build_items(msgs)
    assert items[0]["entity_id"] == "slack:T9:C1:1.0"


@patch("hosted_agents.scrapers.slack_job.httpx.Client")
@patch("hosted_agents.scrapers.slack_job.WebClient")
def test_run_conversations_history(mock_wc_class, mock_hx_cls, monkeypatch) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv(
        "SLACK_SCRAPER_SEARCHES_JSON",
        json.dumps(
            [{"id": "c1", "type": "conversations_history", "channel": "C1", "limit": 3}],
        ),
    )
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag.local")
    monkeypatch.setenv("SCRAPER_METRICS_ADDR", "")
    mock_client = MagicMock()
    mock_wc_class.return_value = mock_client
    mock_client.conversations_history.return_value = {
        "messages": [{"text": "m", "channel": "C1", "ts": "1.0", "team": "T1"}],
        "response_metadata": {},
    }
    hx_inst = MagicMock()
    mock_hx_cls.return_value.__enter__.return_value = hx_inst
    resp = MagicMock()
    hx_inst.post.return_value = resp
    resp.raise_for_status = MagicMock()
    slack_job.run()
    mock_client.conversations_history.assert_called_once()


@patch("hosted_agents.scrapers.slack_job.httpx.Client")
@patch("hosted_agents.scrapers.slack_job.WebClient")
def test_run_posts_embed(mock_wc_class, mock_hx_cls, monkeypatch) -> None:
    monkeypatch.setenv("SLACK_BOT_TOKEN", "xoxb-test")
    monkeypatch.setenv(
        "SLACK_SCRAPER_SEARCHES_JSON",
        json.dumps(
            [{"id": "s1", "type": "search_messages", "query": "foo", "limit": 5}],
        ),
    )
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag.local")
    monkeypatch.setenv("SCRAPER_METRICS_ADDR", "")
    mock_client = MagicMock()
    mock_wc_class.return_value = mock_client
    mock_client.search_messages.return_value = {
        "messages": {
            "matches": [
                {
                    "text": "hello",
                    "channel": "CZ",
                    "ts": "2.0",
                    "team": "TX",
                },
            ],
            "pagination": {},
        },
    }
    hx_inst = MagicMock()
    mock_hx_cls.return_value.__enter__.return_value = hx_inst
    resp = MagicMock()
    hx_inst.post.return_value = resp
    resp.raise_for_status = MagicMock()
    slack_job.run()
    mock_client.search_messages.assert_called_once()
    hx_inst.post.assert_called_once()
    args, kwargs = hx_inst.post.call_args
    assert args[0] == "http://rag.local/v1/embed"
