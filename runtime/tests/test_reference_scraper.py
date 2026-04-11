"""Tests for reference scraper job."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from hosted_agents.scrapers import reference_job


def test_reference_job_requires_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAG_SERVICE_URL", raising=False)
    with pytest.raises(SystemExit):
        reference_job.run()


def test_reference_job_posts_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag:8090")
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_post = MagicMock(return_value=mock_resp)
    mock_client = MagicMock()
    mock_client.__enter__.return_value.post = mock_post
    mock_client.__exit__.return_value = None
    monkeypatch.setattr("hosted_agents.scrapers.reference_job.httpx.Client", lambda **kw: mock_client)
    reference_job.run()
    mock_post.assert_called_once()
    args, kwargs = mock_post.call_args
    assert args[0] == "http://rag:8090/v1/embed"
    assert kwargs["json"]["scope"] == "reference"
    assert kwargs["json"]["relationships"]
