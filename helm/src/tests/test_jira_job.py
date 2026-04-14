"""Tests for ``hosted_agents.scrapers.jira_job``."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from hosted_agents.scrapers import jira_job
from hosted_agents.scrapers.jira_job import search_issues


def test_search_issues_single_page() -> None:
    body = {
        "issues": [
            {
                "key": "DEMO-1",
                "fields": {"updated": "2024-01-01T00:00:00.000+0000"},
            },
        ],
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/rest/api/3/search/jql" in str(request.url)
        payload = json.loads(request.content.decode("utf-8"))
        assert "nextPageToken" not in payload
        assert payload["jql"] == 'project = "DEMO"'
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    issues = search_issues(client, "https://x.example.net", 'project = "DEMO"', ["summary"], 10)
    assert len(issues) == 1
    assert issues[0]["key"] == "DEMO-1"


def test_search_issues_next_page_token() -> None:
    """Second request includes ``nextPageToken`` from the first response."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/rest/api/3/search/jql" in str(request.url)
        payload = json.loads(request.content.decode("utf-8"))
        if payload.get("nextPageToken") == "t2":
            return httpx.Response(
                200,
                json={
                    "issues": [
                        {
                            "key": "DEMO-2",
                            "fields": {"updated": "2024-01-02T00:00:00.000+0000"},
                        },
                    ],
                },
            )
        return httpx.Response(
            200,
            json={
                "issues": [
                    {
                        "key": "DEMO-1",
                        "fields": {"updated": "2024-01-01T00:00:00.000+0000"},
                    },
                ],
                "nextPageToken": "t2",
            },
        )

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    issues = search_issues(client, "https://x.example.net", "project = DEMO", ["summary"], 10)
    assert [i["key"] for i in issues] == ["DEMO-1", "DEMO-2"]


def test_build_jql_with_watermark() -> None:
    q = jira_job._build_jql('project = DEMO ORDER BY updated ASC', "2024-01-01 00:00")
    assert "project = DEMO" in q
    assert "updated >=" in q


def test_watermark_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_WATERMARK_DIR", str(tmp_path))
    p = jira_job._watermark_path("scope", 'project = "DEMO"')
    jira_job._write_watermark(p, "2024-02-01T12:00:00.000+0000")
    wm = jira_job._read_watermark(p, overlap_minutes=5)
    assert wm is not None
    data = json.loads(p.read_text(encoding="utf-8"))
    assert "2024-02-01" in data["last_updated"]


def test_fetch_comments_empty() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert "/comment" in str(request.url)
        return httpx.Response(200, json={"comments": [], "total": 0})

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport, auth=("a", "b"))
    out = jira_job._fetch_comments(client, "https://h.example", "DEMO-1", 10)
    assert out == []


def test_run_jira_end_to_end_mocked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Exercise ``jira_job.run()`` with mocked HTTP (search, comments, RAG embed)."""
    job = {"source": "jira", "query": 'project = DEMO ORDER BY updated ASC', "maxIssuesPerRun": 2}
    cfg = tmp_path / "job.json"
    cfg.write_text(json.dumps(job), encoding="utf-8")
    monkeypatch.setenv("SCRAPER_JOB_CONFIG", str(cfg))
    monkeypatch.setenv("JIRA_SITE_URL", "https://jira.example.net")
    monkeypatch.setenv("JIRA_EMAIL", "u@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "secret")
    monkeypatch.setenv("JIRA_WATERMARK_DIR", str(tmp_path / "wm"))
    monkeypatch.setenv("RAG_SERVICE_URL", "http://rag.local")
    monkeypatch.setenv("SCRAPER_METRICS_ADDR", "")

    def handler(request: httpx.Request) -> httpx.Response:
        u = str(request.url)
        if "/rest/api/3/search/jql" in u:
            return httpx.Response(
                200,
                json={
                    "issues": [
                        {
                            "key": "DEMO-9",
                            "fields": {"updated": "2024-03-01T00:00:00.000+0000"},
                        },
                    ],
                    "total": 1,
                },
            )
        if "/rest/api/3/issue/DEMO-9/comment" in u:
            return httpx.Response(200, json={"comments": [], "total": 0})
        if u.rstrip("/").endswith("/v1/embed"):
            return httpx.Response(200, json={"ok": True})
        return httpx.Response(404, json={"err": u})

    transport = httpx.MockTransport(handler)
    real_client_cls = jira_job.httpx.Client

    def client_factory(**kwargs: object) -> httpx.Client:
        return real_client_cls(transport=transport, **kwargs)

    monkeypatch.setattr(jira_job.httpx, "Client", client_factory)
    jira_job.run()


def test_issue_text_builds() -> None:
    issue = {
        "key": "DEMO-2",
        "fields": {
            "summary": "S",
            "description": "D",
            "status": {"name": "Open"},
            "assignee": {"displayName": "A"},
            "issuelinks": [],
            "updated": "2024-01-02T00:00:00.000+0000",
        },
    }
    text = jira_job._issue_text(issue, [], 10, False)
    assert "DEMO-2" in text
    assert "Summary: S" in text


