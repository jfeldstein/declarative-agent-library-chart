"""Tests for reference scraper job."""

from __future__ import annotations

from unittest.mock import MagicMock

import httpx
import pytest
from prometheus_client import REGISTRY, generate_latest

from hosted_agents.scrapers import reference_job


def test_reference_job_requires_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAG_SERVICE_URL", raising=False)
    monkeypatch.delenv("SCRAPER_METRICS_ADDR", raising=False)
    with pytest.raises(SystemExit):
        reference_job.run()


def test_reference_job_posts_embed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag:8090")
    monkeypatch.delenv("SCRAPER_METRICS_ADDR", raising=False)
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


def test_reference_job_metrics_on_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag:8090")
    monkeypatch.delenv("SCRAPER_METRICS_ADDR", raising=False)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_post = MagicMock(return_value=mock_resp)
    mock_client = MagicMock()
    mock_client.__enter__.return_value.post = mock_post
    mock_client.__exit__.return_value = None
    monkeypatch.setattr("hosted_agents.scrapers.reference_job.httpx.Client", lambda **kw: mock_client)
    reference_job.run()
    text = generate_latest(REGISTRY).decode()
    assert 'agent_runtime_scraper_runs_total{integration="reference",result="success"}' in text
    assert 'agent_runtime_scraper_rag_submissions_total{integration="reference",result="success"}' in text


def test_reference_job_metrics_on_embed_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag:8090")
    monkeypatch.delenv("SCRAPER_METRICS_ADDR", raising=False)
    req = httpx.Request("POST", "http://rag:8090/v1/embed")
    err_resp = httpx.Response(500, request=req)
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError("fail", request=req, response=err_resp),
    )
    mock_post = MagicMock(return_value=mock_resp)
    mock_client = MagicMock()
    mock_client.__enter__.return_value.post = mock_post
    mock_client.__exit__.return_value = None
    monkeypatch.setattr("hosted_agents.scrapers.reference_job.httpx.Client", lambda **kw: mock_client)
    with pytest.raises(httpx.HTTPStatusError):
        reference_job.run()
    text = generate_latest(REGISTRY).decode()
    assert 'agent_runtime_scraper_runs_total{integration="reference",result="error"}' in text
    assert 'agent_runtime_scraper_rag_submissions_total{integration="reference",result="server_error"}' in text
