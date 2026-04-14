"""Slack pull scraper: declarative searches → RAG ``/v1/embed``.

Env: ``RAG_SERVICE_URL``, ``SCRAPER_SCOPE``, ``SLACK_BOT_TOKEN``,
``SLACK_SCRAPER_SEARCHES_JSON`` (or ``SLACK_SCRAPER_SEARCHES_FILE``),
``SCRAPER_INTEGRATION`` (default ``slack``). See ``openspec/changes/slack-scraper/``.
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import Any

import httpx
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from hosted_agents.scrapers.metrics import (
    classify_rag_submission_result,
    maybe_start_scraper_metrics_http,
    observe_rag_embed_attempt,
    observe_scraper_run,
    stop_scraper_metrics_http,
)


def _integration_label() -> str:
    v = os.environ.get("SCRAPER_INTEGRATION", "slack").strip()
    return v or "slack"


def _load_searches() -> list[dict[str, Any]]:
    raw_path = os.environ.get("SLACK_SCRAPER_SEARCHES_FILE", "").strip()
    raw_json = os.environ.get("SLACK_SCRAPER_SEARCHES_JSON", "").strip()
    if raw_path:
        p = Path(raw_path)
        if not p.is_file():
            print(f"SLACK_SCRAPER_SEARCHES_FILE not found: {p}", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        raw_json = p.read_text(encoding="utf-8")
    if not raw_json:
        print(
            "SLACK_SCRAPER_SEARCHES_JSON or SLACK_SCRAPER_SEARCHES_FILE is required",
            file=sys.stderr,
        )  # noqa: T201
        sys.exit(1)
    try:
        data = json.loads(raw_json)
    except json.JSONDecodeError as exc:
        print(f"Invalid SLACK_SCRAPER_SEARCHES_JSON: {exc}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    if not isinstance(data, list) or not data:
        print("Searches JSON must be a non-empty list", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    for i, step in enumerate(data):
        if not isinstance(step, dict):
            print(f"Search step {i} must be an object", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        if "id" not in step or "type" not in step:
            print(f"Search step {i} requires id and type", file=sys.stderr)  # noqa: T201
            sys.exit(1)
    return data


def _entity_id(channel: str, ts: str, team: str | None) -> str:
    tid = (team or "unknown").replace(":", "_")
    return f"slack:{tid}:{channel}:{ts}"


def _response_dict(resp: object) -> dict[str, Any]:
    if isinstance(resp, dict):
        return resp
    data = getattr(resp, "data", None)
    if isinstance(data, dict):
        return data
    try:
        return dict(resp)  # SlackResponse is Mapping-like
    except Exception:
        return {}


def _collect_messages(client: WebClient, step: dict[str, Any]) -> list[dict[str, Any]]:
    stype = str(step["type"]).strip()
    limit = min(int(step.get("limit", 50)), 200)
    out: list[dict[str, Any]] = []
    if stype == "search_messages":
        query = str(step.get("query", "")).strip()
        if not query:
            return out
        cursor = None
        while len(out) < limit:
            raw = client.search_messages(
                query=query, count=min(100, limit - len(out)), cursor=cursor
            )
            page = _response_dict(raw)
            msg_obj = page.get("messages") or {}
            if isinstance(msg_obj, dict):
                msgs = msg_obj.get("matches", []) or []
                pag = msg_obj.get("pagination") or {}
            else:
                msgs = []
                pag = {}
            if not msgs:
                break
            out.extend(msgs)
            cursor = pag.get("next_cursor") if isinstance(pag, dict) else None
            if not cursor:
                break
    elif stype == "conversations_history":
        channel = str(step.get("channel", "")).strip()
        if not channel:
            return out
        slack_cursor = None
        while len(out) < limit:
            raw = client.conversations_history(
                channel=channel, limit=min(200, limit - len(out)), cursor=slack_cursor
            )
            page = _response_dict(raw)
            msgs = page.get("messages", []) or []
            if not msgs:
                break
            out.extend(msgs)
            meta = page.get("response_metadata") or {}
            slack_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None
            if not slack_cursor:
                break
    else:
        print(f"Unknown search type: {stype}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    return out[:limit]


def _message_text(m: dict[str, Any]) -> str:
    t = m.get("text")
    if t:
        return str(t)
    if m.get("blocks"):
        return json.dumps(m.get("blocks"))[:8000]
    return "(no text)"


def _build_items(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for m in messages:
        ch_raw = m.get("channel")
        if isinstance(ch_raw, dict):
            channel = ch_raw.get("id")
        else:
            channel = ch_raw
        ts = m.get("ts") or m.get("permalink", "unknown")
        team = m.get("team")
        if isinstance(team, dict):
            team = team.get("id")
        ch = str(channel or "unknown")
        ts_s = str(ts)
        entity_id = _entity_id(ch, ts_s, str(team) if team else None)
        items.append(
            {
                "text": _message_text(m),
                "metadata": {
                    "source": "slack-scraper",
                    "slack_channel": ch,
                    "slack_ts": ts_s,
                },
                "entity_id": entity_id,
            },
        )
    return items


def _embed_payload(scope: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scope": scope,
        "entities": [],
        "relationships": [],
        "items": items,
    }


def _post_embed(
    client: httpx.Client, base: str, payload: dict[str, Any], integration: str
) -> None:
    try:
        r = client.post(f"{base}/v1/embed", json=payload)
        r.raise_for_status()
    except httpx.HTTPError as exc:
        observe_rag_embed_attempt(integration, classify_rag_submission_result(exc))
        raise
    observe_rag_embed_attempt(integration, "success")


def run() -> None:
    t0 = time.perf_counter()
    integration = _integration_label()
    httpd = maybe_start_scraper_metrics_http()
    run_ok = False
    try:
        token = os.environ.get("SLACK_BOT_TOKEN", "").strip()
        if not token:
            print("SLACK_BOT_TOKEN is required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        base = os.environ.get("RAG_SERVICE_URL", "").strip().rstrip("/")
        if not base:
            print("RAG_SERVICE_URL is required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        scope = os.environ.get("SCRAPER_SCOPE", "slack").strip() or "slack"
        searches = _load_searches()
        client = WebClient(token=token)
        all_items: list[dict[str, Any]] = []
        for step in searches:
            try:
                msgs = _collect_messages(client, step)
            except SlackApiError as exc:
                print(f"Slack API error on step {step.get('id')}: {exc}", file=sys.stderr)  # noqa: T201
                sys.exit(1)
            all_items.extend(_build_items(msgs))
        if not all_items:
            run_ok = True
        else:
            payload = _embed_payload(scope, all_items)
            with httpx.Client(timeout=120.0) as hx:
                _post_embed(hx, base, payload, integration)
            run_ok = True
    finally:
        elapsed = time.perf_counter() - t0
        observe_scraper_run(integration, run_ok, elapsed)
        stop_scraper_metrics_http(httpd)


if __name__ == "__main__":
    run()
