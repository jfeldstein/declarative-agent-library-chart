"""httpx-backed Jira Cloud REST helpers with structured, redacted errors."""

from __future__ import annotations

import json
from typing import Any

import httpx

from agent.o11y_logging import get_logger
from agent.tools.jira.config import JiraToolsSettings


def _safe_detail_from_parsed(parsed: object) -> dict[str, Any] | list[Any] | str:
    if isinstance(parsed, dict):
        msgs = parsed.get("errorMessages")
        errs = parsed.get("errors")
        safe_body: dict[str, Any] = {}
        if isinstance(msgs, list):
            safe_body["errorMessages"] = [str(x) for x in msgs[:20]]
        if isinstance(errs, dict):
            safe_body["errors"] = {str(k): str(v) for k, v in list(errs.items())[:20]}
        return safe_body
    if isinstance(parsed, list):
        return parsed[:20]
    return str(parsed)[:500]


def build_client(settings: JiraToolsSettings) -> httpx.Client:
    base = settings.site_url.strip().rstrip("/")
    auth = (settings.email, settings.api_token)
    timeout = httpx.Timeout(settings.timeout_seconds)
    return httpx.Client(base_url=base, auth=auth, timeout=timeout)


def trace_id_from_response(resp: httpx.Response) -> str | None:
    for key in ("atl-traceid", "x-arequestid", "x-request-id"):
        val = resp.headers.get(key)
        if val:
            return val.strip()
    return None


def normalize_jira_error(resp: httpx.Response) -> dict[str, Any]:
    """Return a JSON-serializable error dict without secrets or raw auth headers."""

    trace = trace_id_from_response(resp)
    try:
        parsed = resp.json()
        safe_body = _safe_detail_from_parsed(parsed)
    except json.JSONDecodeError:
        safe_body = (resp.text or "")[:500]

    get_logger().warning(
        "jira_tools_http_error",
        status_code=resp.status_code,
        trace_id=trace,
        path=str(resp.request.url.path) if resp.request else "",
    )
    out: dict[str, Any] = {
        "ok": False,
        "status_code": resp.status_code,
        "error": "jira_http_error",
        "detail": safe_body,
    }
    if trace:
        out["trace_id"] = trace
    return out


def request_json(
    client: httpx.Client,
    settings: JiraToolsSettings,
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Perform a JSON request; return parsed body or a structured error dict."""

    try:
        resp = client.request(method, url, params=params, json=json_body)
    except httpx.HTTPError as exc:
        get_logger().warning(
            "jira_tools_transport_error",
            exc_type=type(exc).__name__,
        )
        return {
            "ok": False,
            "error": "jira_transport_error",
            "detail": type(exc).__name__,
        }

    if resp.status_code >= 400:
        return normalize_jira_error(resp)

    if resp.status_code == 204 or not (resp.content or b"").strip():
        return {}

    try:
        data = resp.json()
    except json.JSONDecodeError:
        return {"ok": False, "error": "invalid_json_response"}
    if isinstance(data, dict):
        return dict(data)
    return {"value": data}
