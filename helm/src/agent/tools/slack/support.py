"""Shared helpers for LLM-time Slack tools (distinct from scraper ``SLACK_*`` env)."""

from __future__ import annotations

import os
import time
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from agent.o11y_logging import get_logger

_SLACK_TOOLS_TOKEN = "HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN"
_HISTORY_LIMIT = "HOSTED_AGENT_SLACK_TOOLS_HISTORY_LIMIT"
_TIMEOUT = "HOSTED_AGENT_SLACK_TOOLS_TIMEOUT_SECONDS"


def optional_tools_client() -> WebClient | None:
    """Return a ``WebClient`` when ``HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN`` is set."""
    token = os.environ.get(_SLACK_TOOLS_TOKEN, "").strip()
    if not token:
        return None
    timeout = timeout_seconds()
    return WebClient(token=token, timeout=timeout)


def timeout_seconds() -> int:
    raw = os.environ.get(_TIMEOUT, "30").strip()
    try:
        sec = int(raw)
    except ValueError:
        return 30
    return max(5, min(sec, 120))


def history_limit(requested: int | None) -> int:
    """Clamp history/replies limit using env default and a hard ceiling."""
    cap = default_history_limit()
    if requested is None:
        return cap
    try:
        n = int(requested)
    except (TypeError, ValueError):
        return cap
    return max(1, min(n, 200, cap))


def default_history_limit() -> int:
    raw = os.environ.get(_HISTORY_LIMIT, "50").strip()
    try:
        n = int(raw)
    except ValueError:
        return 50
    return max(1, min(n, 200))


def normalize_channel_id(arguments: dict[str, Any]) -> str:
    return str(arguments.get("channel_id") or arguments.get("channel") or "").strip()


def slack_response_data(resp: object) -> dict[str, Any]:
    """Normalize Slack SDK ``SlackResponse`` or bare dict to a payload dict."""
    if isinstance(resp, dict):
        return resp
    raw = getattr(resp, "data", None)
    return raw if isinstance(raw, dict) else {}


def slack_response_ok(resp: object) -> bool:
    return bool(slack_response_data(resp).get("ok", True))


def _slack_req_id_from_headers(headers: object | None) -> str:
    """Best-effort Slack request id for logs (never raises)."""
    if headers is None:
        return ""
    getter = getattr(headers, "get", None)
    if not callable(getter):
        return ""
    for key in ("x-slack-req-id", "X-Slack-Req-Id"):
        val = getter(key, None)
        if val:
            return str(val)
    return ""


def slack_api_error_payload(exc: SlackApiError, *, method: str) -> dict[str, Any]:
    """Structured error for the model; never includes tokens."""
    err = "slack_api_error"
    req_id = ""
    resp = getattr(exc, "response", None)
    if resp is not None:
        raw = getattr(resp, "data", None)
        if isinstance(raw, dict):
            err = str(raw.get("error") or err)
        req_id = _slack_req_id_from_headers(getattr(resp, "headers", None))
    get_logger().warning(
        "slack_tools_api_error",
        method=method,
        slack_error=err,
        slack_req_id=req_id or None,
    )
    out: dict[str, Any] = {"ok": False, "error": err}
    if req_id:
        out["slack_req_id"] = req_id
    return out


def finish_ok(_method: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Return tool JSON; Prometheus metrics are emitted in :mod:`agent.trigger_steps`."""
    return payload


def api_start() -> float:
    return time.perf_counter()
