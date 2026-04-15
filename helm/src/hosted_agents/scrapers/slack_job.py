"""Slack pull scraper — job JSON at ``SCRAPER_JOB_CONFIG`` (mounted ConfigMap).

* ``slack_search`` — `assistant.search.context` (Real-time Search API), then for each
  hit: `conversations.replies` on the thread root and `conversations.history` in a
  configurable time window (`contextBeforeMinutes` / `contextAfterMinutes`).
  Requires ``SLACK_USER_TOKEN`` (``xoxp-``). See
  https://docs.slack.dev/apis/web-api/real-time-search-api and
  https://docs.slack.dev/reference/methods/conversations.history

* ``slack_channel`` — `conversations.history` for ``conversationId`` with cursor
  draining and incremental ``watermark_ts`` under ``SLACK_STATE_DIR``.
  Requires ``SLACK_BOT_TOKEN``.

Unknown ``source`` → exit code 1.
"""

from __future__ import annotations

import json
import os
import re
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
from hosted_agents.scrapers.cursor_store import CursorStore, cursor_store_from_env


def _integration_label() -> str:
    v = os.environ.get("SCRAPER_INTEGRATION", "slack").strip()
    return v or "slack"


def _load_job_config() -> dict[str, Any]:
    raw_path = os.environ.get("SCRAPER_JOB_CONFIG", "/config/job.json").strip()
    p = Path(raw_path)
    if not p.is_file():
        print(f"SCRAPER_JOB_CONFIG file not found: {p}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Invalid job config JSON: {exc}", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    if not isinstance(data, dict):
        print("Job config must be a JSON object", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    return data


def _response_dict(resp: object) -> dict[str, Any]:
    if isinstance(resp, dict):
        return resp
    data = getattr(resp, "data", None)
    if isinstance(data, dict):
        return data
    try:
        return dict(resp)
    except Exception:
        return {}


def _slack_ts_to_float(ts: str) -> float:
    return float(str(ts).strip())


def _float_to_slack_ts(x: float) -> str:
    s = f"{x:.6f}"
    if "." in s:
        head, _, tail = s.partition(".")
        tail = tail.rstrip("0")
        if not tail:
            return head
        return f"{head}.{tail}"
    return s


def _ts_window(center: str, before_min: float, after_min: float) -> tuple[str, str]:
    c = _slack_ts_to_float(center)
    lo = _float_to_slack_ts(c - max(before_min, 0.0) * 60.0)
    hi = _float_to_slack_ts(c + max(after_min, 0.0) * 60.0)
    return lo, hi


def _entity_id(channel: str, ts: str, team: str | None) -> str:
    tid = (team or "unknown").replace(":", "_")
    return f"slack:{tid}:{channel}:{ts}"


def _message_text(m: dict[str, Any]) -> str:
    t = m.get("text")
    if t:
        return str(t)
    if m.get("blocks"):
        return json.dumps(m.get("blocks"))[:8000]
    return "(no text)"


def _norm_channel_ts(m: dict[str, Any]) -> tuple[str, str] | None:
    ch = m.get("channel_id") or m.get("channel")
    if isinstance(ch, dict):
        ch = ch.get("id")
    ts = m.get("message_ts") or m.get("ts")
    if not ch or not ts:
        return None
    return str(ch), str(ts)


def _collect_history_pages(
    client: WebClient,
    channel: str,
    *,
    oldest: str | None,
    latest: str | None,
    inclusive: bool,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    slack_cursor: str | None = None
    while True:
        kwargs: dict[str, Any] = {
            "channel": channel,
            "limit": 200,
            "inclusive": inclusive,
        }
        if oldest is not None:
            kwargs["oldest"] = oldest
        if latest is not None:
            kwargs["latest"] = latest
        if slack_cursor:
            kwargs["cursor"] = slack_cursor
        raw = client.conversations_history(**kwargs)
        page = _response_dict(raw)
        if not page.get("ok", True):
            err = page.get("error", "unknown")
            raise SlackApiError(err, raw)
        msgs = page.get("messages", []) or []
        out.extend(msgs)
        meta = page.get("response_metadata") or {}
        slack_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None
        if not slack_cursor or not msgs:
            break
    return out


def _collect_replies_pages(
    client: WebClient,
    channel: str,
    thread_ts: str,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    slack_cursor: str | None = None
    while True:
        kwargs: dict[str, Any] = {
            "channel": channel,
            "ts": thread_ts,
            "limit": 200,
        }
        if slack_cursor:
            kwargs["cursor"] = slack_cursor
        raw = client.conversations_replies(**kwargs)
        page = _response_dict(raw)
        if not page.get("ok", True):
            err = page.get("error", "unknown")
            raise SlackApiError(err, raw)
        msgs = page.get("messages", []) or []
        out.extend(msgs)
        meta = page.get("response_metadata") or {}
        slack_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None
        if not slack_cursor or not msgs:
            break
    return out


def _build_items_from_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for m in messages:
        ch_raw = m.get("channel") or m.get("channel_id")
        if isinstance(ch_raw, dict):
            channel = ch_raw.get("id")
        else:
            channel = ch_raw
        ts = m.get("ts")
        if not channel or not ts:
            continue
        ch = str(channel)
        ts_s = str(ts)
        key = (ch, ts_s)
        if key in seen:
            continue
        seen.add(key)
        team = m.get("team")
        if isinstance(team, dict):
            team = team.get("id")
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


def _rts_messages(page: dict[str, Any]) -> list[dict[str, Any]]:
    results = page.get("results") or {}
    if isinstance(results, dict):
        raw = results.get("messages") or []
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]
    return []


def _run_slack_search(
    user_client: WebClient,
    bot_client: WebClient | None,
    job: dict[str, Any],
    scope: str,
    rag_base: str,
    integration: str,
) -> None:
    query = str(job.get("query", "")).strip()
    if not query:
        print("slack_search job requires query", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    before_m = float(job.get("contextBeforeMinutes", 0))
    after_m = float(job.get("contextAfterMinutes", 0))

    body: dict[str, Any] = {
        "query": query,
        "content_types": ["messages"],
        "channel_types": ["public_channel", "private_channel", "im", "mpim"],
        "limit": min(int(job.get("rtsLimit", 20)), 50),
    }
    raw = user_client.api_call("assistant.search.context", json=body)
    page = _response_dict(raw)
    if not page.get("ok", True):
        print(
            f"assistant.search.context failed: {page.get('error', page)}",
            file=sys.stderr,
        )  # noqa: T201
        sys.exit(1)

    hits = _rts_messages(page)
    collected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()

    def _add_msg(m: dict[str, Any]) -> None:
        ch = m.get("channel") or m.get("channel_id")
        if isinstance(ch, dict):
            ch = ch.get("id")
        ts = m.get("ts") or m.get("message_ts")
        if not ch or not ts:
            return
        key = (str(ch), str(ts))
        if key in seen:
            return
        seen.add(key)
        collected.append(m)

    hist_client = bot_client or user_client

    for hit in hits:
        pair = _norm_channel_ts(hit)
        if not pair:
            continue
        channel_id, message_ts = pair
        thread_root = str(hit.get("thread_ts") or message_ts)

        try:
            thread_msgs = _collect_replies_pages(
                hist_client, channel_id, thread_root
            )
            for m in thread_msgs:
                _add_msg(m)
        except SlackApiError as exc:
            print(f"conversations.replies: {exc}", file=sys.stderr)  # noqa: T201
            sys.exit(1)

        try:
            lo, hi = _ts_window(message_ts, before_m, after_m)
            win_msgs = _collect_history_pages(
                hist_client,
                channel_id,
                oldest=lo,
                latest=hi,
                inclusive=True,
            )
            for m in win_msgs:
                _add_msg(m)
        except SlackApiError as exc:
            print(f"conversations.history: {exc}", file=sys.stderr)  # noqa: T201
            sys.exit(1)

    items = _build_items_from_messages(collected)
    if not items:
        return
    payload = _embed_payload(scope, items)
    with httpx.Client(timeout=120.0) as hx:
        _post_embed(hx, rag_base, payload, integration)


def _state_dir() -> Path:
    root = Path(os.environ.get("SLACK_STATE_DIR", "/tmp/slack-scraper-state").strip())
    root.mkdir(parents=True, exist_ok=True)
    return root


def _safe_scope(scope: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", scope)[:80]


def _run_slack_channel(
    bot: WebClient,
    job: dict[str, Any],
    scope: str,
    rag_base: str,
    integration: str,
    store: CursorStore,
) -> None:
    cid = str(job.get("conversationId", "")).strip()
    if not cid:
        print("slack_channel job requires conversationId", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    watermark = store.get_state("slack", scope, cid)

    collected: list[dict[str, Any]] = []
    slack_cursor: str | None = None
    max_seen: float | None = None
    while True:
        kwargs: dict[str, Any] = {"channel": cid, "limit": 200}
        if watermark:
            kwargs["oldest"] = str(watermark)
            kwargs["inclusive"] = False
        if slack_cursor:
            kwargs["cursor"] = slack_cursor
        raw = bot.conversations_history(**kwargs)
        page = _response_dict(raw)
        if not page.get("ok", True):
            err = page.get("error", "unknown")
            raise SlackApiError(err, raw)
        msgs = page.get("messages", []) or []
        for m in msgs:
            ts = m.get("ts")
            if ts:
                tf = _slack_ts_to_float(str(ts))
                max_seen = tf if max_seen is None else max(max_seen, tf)
        collected.extend(msgs)
        meta = page.get("response_metadata") or {}
        slack_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None
        if not slack_cursor or not msgs:
            break

    if max_seen is not None:
        store.set_state("slack", scope, cid, _float_to_slack_ts(max_seen))

    items = _build_items_from_messages(collected)
    if not items:
        return
    payload = _embed_payload(scope, items)
    with httpx.Client(timeout=120.0) as hx:
        _post_embed(hx, rag_base, payload, integration)


def run() -> None:
    t0 = time.perf_counter()
    integration = _integration_label()
    httpd = maybe_start_scraper_metrics_http()
    run_ok = False
    try:
        cfg = _load_job_config()
        source = str(cfg.get("source", "")).strip().lower()
        if source not in ("slack_search", "slack_channel"):
            print(
                f"Unknown slack job source {source!r}; expected slack_search or slack_channel",
                file=sys.stderr,
            )  # noqa: T201
            sys.exit(1)

        rag_base = os.environ.get("RAG_SERVICE_URL", "").strip().rstrip("/")
        if not rag_base:
            print("RAG_SERVICE_URL is required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        scope = os.environ.get("SCRAPER_SCOPE", "slack").strip() or "slack"
        store = cursor_store_from_env()

        user_token = os.environ.get("SLACK_USER_TOKEN", "").strip()
        bot_token = os.environ.get("SLACK_BOT_TOKEN", "").strip()

        if source == "slack_search":
            if not user_token:
                print(
                    "SLACK_USER_TOKEN is required for slack_search (Real-time Search API)",
                    file=sys.stderr,
                )  # noqa: T201
                sys.exit(1)
            user_client = WebClient(token=user_token)
            bot_client = WebClient(token=bot_token) if bot_token else None
            try:
                _run_slack_search(user_client, bot_client, cfg, scope, rag_base, integration)
            except SlackApiError as exc:
                print(f"Slack API error: {exc}", file=sys.stderr)  # noqa: T201
                sys.exit(1)
            run_ok = True
        else:
            if not bot_token:
                print("SLACK_BOT_TOKEN is required for slack_channel", file=sys.stderr)  # noqa: T201
                sys.exit(1)
            bot = WebClient(token=bot_token)
            try:
                _run_slack_channel(bot, cfg, scope, rag_base, integration, store)
            except SlackApiError as exc:
                print(f"Slack API error: {exc}", file=sys.stderr)  # noqa: T201
                sys.exit(1)
            run_ok = True
    finally:
        elapsed = time.perf_counter() - t0
        observe_scraper_run(integration, run_ok, elapsed)
        stop_scraper_metrics_http(httpd)


if __name__ == "__main__":
    run()
