"""Tests for ``hosted_agents.scrapers.jira_job``."""

from __future__ import annotations

import json
import httpx

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
        "total": 1,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        assert "/rest/api/3/search" in str(request.url)
        return httpx.Response(200, json=body)

    transport = httpx.MockTransport(handler)
    client = httpx.Client(transport=transport)
    issues = search_issues(client, "https://x.example.net", 'project = "DEMO"', ["summary"], 10)
    assert len(issues) == 1
    assert issues[0]["key"] == "DEMO-1"


def test_watermark_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("JIRA_WATERMARK_DIR", str(tmp_path))
    p = jira_job._watermark_path("scope", "DEMO")
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


