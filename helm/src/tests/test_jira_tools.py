"""Tests for Jira REST tools (`agent.tools.jira`)."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from agent.tools.dispatch import invoke_tool
from agent.tools.jira.config import load_settings
from agent.tools.jira.rest import normalize_jira_error
from agent.tools.jira import TOOL_IDS


def _enable_jira_tools(
    monkeypatch: pytest.MonkeyPatch, *, simulated: bool = True
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_ENABLED", "true")
    monkeypatch.setenv(
        "HOSTED_AGENT_JIRA_TOOLS_SIMULATED", "true" if simulated else "false"
    )
    monkeypatch.setenv(
        "HOSTED_AGENT_JIRA_TOOLS_SITE_URL", "https://example.atlassian.net"
    )
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_EMAIL", "bot@example.com")
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_API_TOKEN", "secret-token-not-for-logs")
    monkeypatch.setenv(
        "HOSTED_AGENT_JIRA_TOOLS_SCOPES_JSON",
        json.dumps(
            {
                "search": True,
                "read": True,
                "comment": True,
                "transition": True,
                "create": True,
                "update": True,
            },
        ),
    )
    monkeypatch.setenv(
        "HOSTED_AGENT_JIRA_TOOLS_ALLOWED_PROJECT_KEYS_JSON", json.dumps(["DEMO"])
    )
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_MAX_SEARCH_RESULTS", "50")
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_MAX_JQL_LENGTH", "500")


def test_jira_tools_python_sources_avoid_embed_route():
    """[DALC-REQ-JIRA-TOOLS-001]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_jira_tools_python_sources_avoid_embed_route``
    """

    root = Path(__file__).resolve().parents[1] / "agent" / "tools" / "jira"
    for path in sorted(root.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        assert "/v1/embed" not in text, path.name


def test_invoke_search_simulated(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-003] [DALC-REQ-JIRA-TOOLS-004]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_invoke_search_simulated``
    """

    _enable_jira_tools(monkeypatch, simulated=True)
    out = invoke_tool("jira.search_issues", {"jql": "project = DEMO", "max_results": 5})
    assert out["ok"] is True
    assert out["simulated"] is True
    assert len(out["issues"]) >= 1


def test_search_requires_jql(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-004]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_search_requires_jql``
    """

    _enable_jira_tools(monkeypatch)
    with pytest.raises(ValueError, match="jql"):
        invoke_tool("jira.search_issues", {})


def test_search_jql_length_cap(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-004]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_search_jql_length_cap``
    """

    _enable_jira_tools(monkeypatch)
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_MAX_JQL_LENGTH", "10")
    long_jql = "x" * 20
    with pytest.raises(ValueError, match="max length"):
        invoke_tool("jira.search_issues", {"jql": long_jql})


def test_scope_denied(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-003]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_scope_denied``
    """

    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_SIMULATED", "true")
    monkeypatch.setenv(
        "HOSTED_AGENT_JIRA_TOOLS_SCOPES_JSON",
        json.dumps({"search": False, "read": False}),
    )
    monkeypatch.setenv("HOSTED_AGENT_JIRA_TOOLS_ALLOWED_PROJECT_KEYS_JSON", "[]")
    with pytest.raises(ValueError, match="scope"):
        invoke_tool("jira.search_issues", {"jql": "project = X"})


def test_tools_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-002]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_tools_disabled``
    """

    monkeypatch.delenv("HOSTED_AGENT_JIRA_TOOLS_ENABLED", raising=False)
    assert load_settings() is None
    with pytest.raises(ValueError, match="not enabled"):
        invoke_tool("jira.search_issues", {"jql": "project = X"})


def test_http_error_mapping_redacts() -> None:
    """[DALC-REQ-JIRA-TOOLS-006]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_http_error_mapping_redacts``
    """

    req = httpx.Request("GET", "https://example.atlassian.net/rest/api/3/issue/X-1")
    resp = httpx.Response(
        401,
        request=req,
        headers={"atl-traceid": "trace-abc"},
        json={"errorMessages": ["nice try"]},
    )
    body = normalize_jira_error(resp)
    dumped = json.dumps(body)
    assert "TOPSECRET" not in dumped
    assert "Authorization" not in dumped
    assert "trace-abc" in dumped or body.get("trace_id") == "trace-abc"


def test_real_search_uses_httpx(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-005]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_real_search_uses_httpx``
    """

    _enable_jira_tools(monkeypatch, simulated=False)

    mock_resp = httpx.Response(
        200,
        json={
            "issues": [{"key": "DEMO-1", "fields": {"summary": "Hi"}}],
            "total": 1,
        },
    )

    class FakeClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> FakeClient:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def request(self, method: str, url: str, **kwargs: object) -> httpx.Response:
            return mock_resp

    monkeypatch.setattr(
        "agent.tools.jira.handlers.build_client", lambda _s: FakeClient()
    )

    out = invoke_tool("jira.search_issues", {"jql": "project = DEMO"})
    assert out["ok"] is True
    assert out["simulated"] is False
    assert out["issues"][0]["key"] == "DEMO-1"


def test_token_not_in_tool_error_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-006]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_token_not_in_tool_error_payload``
    """

    _enable_jira_tools(monkeypatch, simulated=False)

    bad_req = httpx.Request("GET", "https://example.atlassian.net/rest/api/3/search")
    bad = httpx.Response(
        403,
        request=bad_req,
        json={"errorMessages": ["forbidden"]},
    )

    class BoomClient:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pass

        def __enter__(self) -> BoomClient:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def request(self, *args: object, **kwargs: object) -> httpx.Response:
            return bad

    monkeypatch.setattr(
        "agent.tools.jira.handlers.build_client", lambda _s: BoomClient()
    )

    out = invoke_tool("jira.search_issues", {"jql": "project = DEMO"})
    dumped = json.dumps(out)
    assert "secret-token-not-for-logs" not in dumped


@pytest.mark.parametrize(
    ("tool", "args"),
    [
        ("jira.get_issue", {"issue_key": "DEMO-1"}),
        ("jira.add_comment", {"issue_key": "DEMO-1", "body": "hello"}),
        ("jira.transition_issue", {"issue_key": "DEMO-1"}),
        (
            "jira.create_issue",
            {"project_key": "DEMO", "summary": "x", "issue_type": "Task"},
        ),
        ("jira.update_issue", {"issue_key": "DEMO-1", "fields": {"summary": "y"}}),
    ],
)
def test_simulated_mutations_return_ok(
    monkeypatch: pytest.MonkeyPatch,
    tool: str,
    args: dict[str, object],
) -> None:
    """[DALC-REQ-JIRA-TOOLS-003]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_simulated_mutations_return_ok``
    """

    _enable_jira_tools(monkeypatch, simulated=True)
    out = invoke_tool(tool, args)
    assert out["ok"] is True


def test_router_rejects_unknown_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    """Exercise guard branches on the Jira router."""

    _enable_jira_tools(monkeypatch)
    from agent.tools.jira.router import invoke as jinvoke

    with pytest.raises(ValueError, match="unknown Jira tool"):
        jinvoke("jira.typo_tool", {})


class _QueuedHttpxClient:
    """Minimal httpx.Client stand-in returning a queue of ``httpx.Response`` objects."""

    def __init__(self, responses: list[httpx.Response]) -> None:
        self._responses = responses
        self._i = 0

    def __enter__(self) -> _QueuedHttpxClient:
        return self

    def __exit__(self, *exc: object) -> None:
        return None

    def request(self, *args: object, **kwargs: object) -> httpx.Response:
        r = self._responses[self._i]
        self._i += 1
        return r


def test_real_get_issue(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-003]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_real_get_issue``
    """

    _enable_jira_tools(monkeypatch, simulated=False)
    req = httpx.Request("GET", "https://example.atlassian.net/rest/api/3/issue/DEMO-1")
    body = httpx.Response(
        200,
        request=req,
        json={"key": "DEMO-1", "fields": {"summary": "s"}},
    )
    monkeypatch.setattr(
        "agent.tools.jira.handlers.build_client",
        lambda _s: _QueuedHttpxClient([body]),
    )
    out = invoke_tool("jira.get_issue", {"issue_key": "DEMO-1"})
    assert out["key"] == "DEMO-1"
    assert out["simulated"] is False


def test_real_transition_with_name(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-003]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_real_transition_with_name``
    """

    _enable_jira_tools(monkeypatch, simulated=False)
    req = httpx.Request(
        "GET",
        "https://example.atlassian.net/rest/api/3/issue/DEMO-1/transitions",
    )
    tr_get = httpx.Response(
        200,
        request=req,
        json={"transitions": [{"id": "5", "name": "Done"}]},
    )
    req2 = httpx.Request(
        "POST",
        "https://example.atlassian.net/rest/api/3/issue/DEMO-1/transitions",
    )
    tr_post = httpx.Response(204, request=req2)
    monkeypatch.setattr(
        "agent.tools.jira.handlers.build_client",
        lambda _s: _QueuedHttpxClient([tr_get, tr_post]),
    )
    out = invoke_tool(
        "jira.transition_issue",
        {"issue_key": "DEMO-1", "transition_name": "Done"},
    )
    assert out["ok"] is True


def test_real_create_issue(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-003]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_real_create_issue``
    """

    _enable_jira_tools(monkeypatch, simulated=False)
    req = httpx.Request("POST", "https://example.atlassian.net/rest/api/3/issue")
    created = httpx.Response(
        201,
        request=req,
        json={
            "key": "DEMO-9",
            "id": "12345",
            "self": "https://x/rest/api/3/issue/12345",
        },
    )
    monkeypatch.setattr(
        "agent.tools.jira.handlers.build_client",
        lambda _s: _QueuedHttpxClient([created]),
    )
    out = invoke_tool(
        "jira.create_issue",
        {
            "project_key": "DEMO",
            "summary": "hi",
            "issue_type": "Task",
            "description": "d",
        },
    )
    assert out["key"] == "DEMO-9"


def test_real_add_comment(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-003]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_real_add_comment``
    """

    _enable_jira_tools(monkeypatch, simulated=False)
    req = httpx.Request(
        "POST",
        "https://example.atlassian.net/rest/api/3/issue/DEMO-1/comment",
    )
    ok = httpx.Response(201, request=req, json={"id": "c1"})
    monkeypatch.setattr(
        "agent.tools.jira.handlers.build_client",
        lambda _s: _QueuedHttpxClient([ok]),
    )
    out = invoke_tool(
        "jira.add_comment",
        {"issue_key": "DEMO-1", "body": "note"},
    )
    assert out["id"] == "c1"


def test_real_update_issue(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-003]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_real_update_issue``
    """

    _enable_jira_tools(monkeypatch, simulated=False)
    req = httpx.Request(
        "PUT",
        "https://example.atlassian.net/rest/api/3/issue/DEMO-1",
    )
    ok = httpx.Response(204, request=req)
    monkeypatch.setattr(
        "agent.tools.jira.handlers.build_client",
        lambda _s: _QueuedHttpxClient([ok]),
    )
    out = invoke_tool(
        "jira.update_issue",
        {"issue_key": "DEMO-1", "fields": {"summary": "z"}},
    )
    assert out["ok"] is True


def test_transport_error_mapping(monkeypatch: pytest.MonkeyPatch) -> None:
    """[DALC-REQ-JIRA-TOOLS-005]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_transport_error_mapping``
    """

    _enable_jira_tools(monkeypatch, simulated=False)

    class BadClient:
        def __init__(self, *a: object, **kw: object) -> None:
            pass

        def __enter__(self) -> BadClient:
            return self

        def __exit__(self, *exc: object) -> None:
            return None

        def request(self, *a: object, **kw: object) -> httpx.Response:
            raise httpx.ConnectError("boom")

    monkeypatch.setattr(
        "agent.tools.jira.handlers.build_client",
        lambda _s: BadClient(),
    )
    out = invoke_tool("jira.search_issues", {"jql": "project = DEMO"})
    assert out.get("error") == "jira_transport_error"


def test_allowlisted_tool_ids_cover_runtime_surface() -> None:
    """[DALC-REQ-JIRA-TOOLS-001]

    Evidence: ``helm/src/tests/test_jira_tools.py::test_allowlisted_tool_ids_cover_runtime_surface``
    """

    expected = (
        "jira.search_issues",
        "jira.get_issue",
        "jira.add_comment",
        "jira.transition_issue",
        "jira.create_issue",
        "jira.update_issue",
    )
    for tool_id in expected:
        assert tool_id in TOOL_IDS
