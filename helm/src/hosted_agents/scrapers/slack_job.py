"""Slack pull scraper — job JSON at ``SCRAPER_JOB_CONFIG`` (mounted ConfigMap).

* ``slack_search`` — `assistant.search.context` (Real-time Search API), then for each
  hit: `conversations.replies` on the thread root and `conversations.history` in a
  configurable time window (`contextBeforeMinutes` / `contextAfterMinutes`).
  Requires ``SLACK_USER_TOKEN`` (``xoxp-``). See
  https://docs.slack.dev/apis/web-api/real-time-search-api and
  https://docs.slack.dev/reference/methods/conversations.history

* ``slack_channel`` — `conversations.history` for ``conversationId`` with cursor
  draining and incremental ``watermark_ts`` (via ``CursorStore`` / ``SLACK_STATE_DIR``).
  Requires ``SLACK_BOT_TOKEN``.

Per-run limits (defaults in parentheses):

- ``rtsLimit`` — Real-time Search ``assistant.search.context`` max hits (``20``, capped at ``50``).
- ``historyLimit`` — ``conversations.history`` / ``conversations.replies`` page size (``200``, max ``200``).
- ``maxMessagesPerRun`` — stop collecting after this many messages for the job (``10000``).

Unknown ``source`` or invalid job JSON fields → exit code 1 with actionable stderr.
"""

from __future__ import annotations

import json
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from hosted_agents.scrapers.base import (
    ScrapedEmbeds,
    ingest_scraped_embeds,
    integration_label,
    run_scraper_main,
)
from hosted_agents.scrapers.cursor_store import CursorStore, cursor_store_from_env


_TOKEN_LIKE = re.compile(r"xox[bpa]-[A-Za-z0-9+/=-]+")


def _redact_token_like(text: str) -> str:
    """Avoid echoing Slack tokens if an API error message ever contains one."""
    return _TOKEN_LIKE.sub("<redacted>", text)


def _die(msg: str) -> None:
    print(_redact_token_like(msg), file=sys.stderr)  # noqa: T201
    sys.exit(1)


_DEFAULT_RTS_LIMIT = 20
_MAX_RTS_LIMIT = 50
_DEFAULT_HISTORY_LIMIT = 200
_MAX_HISTORY_LIMIT = 200
_DEFAULT_MAX_MESSAGES_PER_RUN = 10_000
_MAX_CONTEXT_MINUTES = 24 * 60


def _load_job_config() -> dict[str, Any]:
    raw_path = os.environ.get("SCRAPER_JOB_CONFIG", "/config/job.json").strip()
    p = Path(raw_path)
    if not p.is_file():
        _die(f"SCRAPER_JOB_CONFIG file not found: {p}")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _die(f"Invalid job config JSON: {exc}")
    if not isinstance(data, dict):
        _die("Job config must be a JSON object at the top level.")
    return data


def _parse_int_field(
    cfg: dict[str, Any],
    key: str,
    *,
    default: int,
    min_v: int,
    max_v: int,
) -> int:
    raw = cfg.get(key)
    if raw is None:
        return default
    try:
        v = int(raw)
    except (TypeError, ValueError):
        _die(f"Job config field {key!r} must be an integer (got {raw!r}).")
    if v < min_v or v > max_v:
        _die(f"Job config field {key!r} must be between {min_v} and {max_v} (got {v}).")
    return v


def _parse_float_minutes(cfg: dict[str, Any], key: str, *, default: float) -> float:
    raw = cfg.get(key)
    if raw is None:
        return default
    try:
        v = float(raw)
    except (TypeError, ValueError):
        _die(f"Job config field {key!r} must be a number (got {raw!r}).")
    if v < 0 or v > _MAX_CONTEXT_MINUTES:
        _die(
            "Job config field "
            f"{key!r} must be between 0 and {_MAX_CONTEXT_MINUTES} minutes (got {v})."
        )
    return v


def _normalize_slack_job(cfg: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Validate ``job.json`` fields and return ``(source, normalized)`` for runners."""
    src = str(cfg.get("source", "")).strip().lower()
    if src not in ("slack_search", "slack_channel"):
        _die(
            "Job config field 'source' must be 'slack_search' or 'slack_channel' "
            f"(got {cfg.get('source')!r})."
        )

    hist_limit = _parse_int_field(
        cfg,
        "historyLimit",
        default=_DEFAULT_HISTORY_LIMIT,
        min_v=1,
        max_v=_MAX_HISTORY_LIMIT,
    )
    max_msgs = _parse_int_field(
        cfg,
        "maxMessagesPerRun",
        default=_DEFAULT_MAX_MESSAGES_PER_RUN,
        min_v=1,
        max_v=1_000_000,
    )

    if src == "slack_search":
        query = str(cfg.get("query", "")).strip()
        if not query:
            _die("slack_search jobs require non-empty job config field 'query'.")
        norm: dict[str, Any] = {
            "query": query,
            "contextBeforeMinutes": _parse_float_minutes(
                cfg,
                "contextBeforeMinutes",
                default=0.0,
            ),
            "contextAfterMinutes": _parse_float_minutes(
                cfg,
                "contextAfterMinutes",
                default=0.0,
            ),
            "rtsLimit": _parse_int_field(
                cfg,
                "rtsLimit",
                default=_DEFAULT_RTS_LIMIT,
                min_v=1,
                max_v=_MAX_RTS_LIMIT,
            ),
            "historyLimit": hist_limit,
            "maxMessagesPerRun": max_msgs,
        }
        return src, norm

    cid = str(cfg.get("conversationId", "")).strip()
    if not cid:
        _die("slack_channel jobs require non-empty job config field 'conversationId'.")
    return src, {
        "conversationId": cid,
        "historyLimit": hist_limit,
        "maxMessagesPerRun": max_msgs,
    }


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


def _messages_page_from_slack_response(
    raw: object,
) -> tuple[list[dict[str, Any]], str | None]:
    """Parse ``conversations.*`` responses: messages list + pagination cursor."""
    page = _response_dict(raw)
    if not page.get("ok", True):
        err = page.get("error", "unknown")
        raise SlackApiError(err, raw)
    msgs = page.get("messages", []) or []
    meta = page.get("response_metadata") or {}
    slack_cursor = meta.get("next_cursor") if isinstance(meta, dict) else None
    return list(msgs), slack_cursor


def _message_channel_id(m: dict[str, Any]) -> str | None:
    raw = m.get("channel") or m.get("channel_id")
    if isinstance(raw, dict):
        raw = raw.get("id")
    if raw is None or raw == "":
        return None
    return str(raw)


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


def _conversations_history_page(
    client: WebClient,
    kwargs: dict[str, Any],
) -> tuple[list[dict[str, Any]], str | None]:
    raw = client.conversations_history(**kwargs)
    return _messages_page_from_slack_response(raw)


def _history_page_kwargs(
    channel: str,
    cap: int,
    inclusive: bool,
    oldest: str | None,
    latest: str | None,
    slack_cursor: str | None,
) -> dict[str, Any]:
    kwargs: dict[str, Any] = {
        "channel": channel,
        "limit": cap,
        "inclusive": inclusive,
    }
    if oldest is not None:
        kwargs["oldest"] = oldest
    if latest is not None:
        kwargs["latest"] = latest
    if slack_cursor:
        kwargs["cursor"] = slack_cursor
    return kwargs


def _trim_page_to_remaining_budget(
    msgs: list[dict[str, Any]],
    max_messages: int | None,
    already_collected: int,
) -> tuple[list[dict[str, Any]], bool]:
    """Return messages to append and whether ``max_messages`` is now reached."""
    if max_messages is None:
        return msgs, False
    room = max_messages - already_collected
    if room <= 0:
        return [], True
    trimmed = msgs[:room]
    budget_full = already_collected + len(trimmed) >= max_messages
    return trimmed, budget_full


def _collect_history_pages(
    client: WebClient,
    channel: str,
    *,
    oldest: str | None,
    latest: str | None,
    inclusive: bool,
    limit: int,
    max_messages: int | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    slack_cursor: str | None = None
    cap = max(1, min(limit, _MAX_HISTORY_LIMIT))
    while True:
        if max_messages is not None and len(out) >= max_messages:
            break
        kwargs = _history_page_kwargs(
            channel, cap, inclusive, oldest, latest, slack_cursor
        )
        msgs, slack_cursor = _conversations_history_page(client, kwargs)
        msgs, budget_done = _trim_page_to_remaining_budget(msgs, max_messages, len(out))
        out.extend(msgs)
        if budget_done:
            break
        if not slack_cursor or not msgs:
            break
    return out


def _conversations_replies_page(
    client: WebClient,
    kwargs: dict[str, Any],
) -> tuple[list[dict[str, Any]], str | None]:
    raw = client.conversations_replies(**kwargs)
    return _messages_page_from_slack_response(raw)


def _collect_replies_pages(
    client: WebClient,
    channel: str,
    thread_ts: str,
    *,
    limit: int,
    max_messages: int | None = None,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    slack_cursor: str | None = None
    cap = max(1, min(limit, _MAX_HISTORY_LIMIT))
    while True:
        if max_messages is not None and len(out) >= max_messages:
            break
        kwargs: dict[str, Any] = {
            "channel": channel,
            "ts": thread_ts,
            "limit": cap,
        }
        if slack_cursor:
            kwargs["cursor"] = slack_cursor
        msgs, slack_cursor = _conversations_replies_page(client, kwargs)
        msgs, budget_done = _trim_page_to_remaining_budget(msgs, max_messages, len(out))
        out.extend(msgs)
        if budget_done:
            break
        if not slack_cursor or not msgs:
            break
    return out


def _slack_rag_item(ch: str, ts_s: str, m: dict[str, Any]) -> dict[str, Any]:
    team = m.get("team")
    if isinstance(team, dict):
        team = team.get("id")
    team_s = str(team) if team else None
    entity_id = _entity_id(ch, ts_s, team_s)
    thr = m.get("thread_ts")
    thr_s = str(thr).strip() if thr not in (None, "") else ""
    meta: dict[str, Any] = {
        "source": "slack-scraper",
        "slack_channel": ch,
        "slack_ts": ts_s,
    }
    if team_s:
        meta["slack_team_id"] = team_s
    if thr_s and thr_s != ts_s:
        meta["slack_thread_ts"] = thr_s
    compact = ts_s.replace(".", "")
    if compact:
        meta["slack_ts_compact"] = compact
    return {
        "text": _message_text(m),
        "metadata": meta,
        "entity_id": entity_id,
    }


def _build_items_from_messages(
    messages: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    for m in messages:
        ch = _message_channel_id(m)
        ts = m.get("ts")
        if not ch or not ts:
            continue
        ts_s = str(ts)
        key = (ch, ts_s)
        if key in seen:
            continue
        seen.add(key)
        items.append(_slack_rag_item(ch, ts_s, m))
    return items


def _embed_payload(scope: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scope": scope,
        "entities": [],
        "relationships": [],
        "items": items,
    }


def _rts_messages(page: dict[str, Any]) -> list[dict[str, Any]]:
    results = page.get("results") or {}
    if isinstance(results, dict):
        raw = results.get("messages") or []
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]
    return []


def _slack_search_add_message(
    m: dict[str, Any],
    seen: set[tuple[str, str]],
    collected: list[dict[str, Any]],
) -> None:
    ch = _message_channel_id(m)
    ts = m.get("ts") or m.get("message_ts")
    if not ch or not ts:
        return
    key = (ch, str(ts))
    if key in seen:
        return
    seen.add(key)
    collected.append(m)


def _slack_search_expand_hit(
    hist_client: WebClient,
    hit: dict[str, Any],
    before_m: float,
    after_m: float,
    add_msg: Callable[[dict[str, Any]], None],
    *,
    history_limit: int,
    rem: list[int],
) -> None:
    if rem[0] <= 0:
        return
    pair = _norm_channel_ts(hit)
    if not pair:
        return
    channel_id, message_ts = pair
    thread_root = str(hit.get("thread_ts") or message_ts)

    try:
        thread_msgs = _collect_replies_pages(
            hist_client,
            channel_id,
            thread_root,
            limit=history_limit,
            max_messages=rem[0],
        )
        for m in thread_msgs:
            add_msg(m)
    except SlackApiError as exc:
        _die(f"conversations.replies failed: {_redact_token_like(str(exc))}")

    try:
        lo, hi = _ts_window(message_ts, before_m, after_m)
        win_msgs = _collect_history_pages(
            hist_client,
            channel_id,
            oldest=lo,
            latest=hi,
            inclusive=True,
            limit=history_limit,
            max_messages=rem[0],
        )
        for m in win_msgs:
            add_msg(m)
    except SlackApiError as exc:
        _die(f"conversations.history failed: {_redact_token_like(str(exc))}")


def _run_slack_search(
    user_client: WebClient,
    bot_client: WebClient | None,
    norm: dict[str, Any],
    scope: str,
) -> dict[str, Any] | None:
    query = str(norm["query"])
    before_m = float(norm["contextBeforeMinutes"])
    after_m = float(norm["contextAfterMinutes"])
    hist_limit = int(norm["historyLimit"])

    body: dict[str, Any] = {
        "query": query,
        "content_types": ["messages"],
        "channel_types": ["public_channel", "private_channel", "im", "mpim"],
        "limit": int(norm["rtsLimit"]),
    }
    raw = user_client.api_call("assistant.search.context", json=body)
    page = _response_dict(raw)
    if not page.get("ok", True):
        err = page.get("error", "unknown")
        _die(f"assistant.search.context failed: {_redact_token_like(str(err))}")

    hits = _rts_messages(page)
    collected: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    hist_client = bot_client or user_client
    rem = [int(norm["maxMessagesPerRun"])]

    def add_msg(m: dict[str, Any]) -> None:
        if rem[0] <= 0:
            return
        before_n = len(collected)
        _slack_search_add_message(m, seen, collected)
        if len(collected) > before_n:
            rem[0] -= 1

    for hit in hits:
        if rem[0] <= 0:
            break
        _slack_search_expand_hit(
            hist_client,
            hit,
            before_m,
            after_m,
            add_msg,
            history_limit=hist_limit,
            rem=rem,
        )

    items = _build_items_from_messages(collected)
    if not items:
        return None
    return _embed_payload(scope, items)


def _merge_max_slack_ts(
    msgs: list[dict[str, Any]],
    max_seen: float | None,
) -> float | None:
    for m in msgs:
        ts = m.get("ts")
        if not ts:
            continue
        tf = _slack_ts_to_float(str(ts))
        max_seen = tf if max_seen is None else max(max_seen, tf)
    return max_seen


def _channel_history_page(
    bot: WebClient,
    cid: str,
    watermark: str | None,
    slack_cursor: str | None,
    *,
    limit: int,
) -> tuple[list[dict[str, Any]], str | None]:
    cap = max(1, min(int(limit), _MAX_HISTORY_LIMIT))
    kwargs: dict[str, Any] = {"channel": cid, "limit": cap}
    if watermark:
        kwargs["oldest"] = str(watermark)
        kwargs["inclusive"] = False
    if slack_cursor:
        kwargs["cursor"] = slack_cursor
    raw = bot.conversations_history(**kwargs)
    return _messages_page_from_slack_response(raw)


def _channel_history_drain(
    bot: WebClient,
    cid: str,
    watermark: str | None,
    *,
    hist_limit: int,
    max_messages: int,
) -> tuple[list[dict[str, Any]], float | None]:
    collected: list[dict[str, Any]] = []
    slack_cursor: str | None = None
    max_seen: float | None = None
    while True:
        if len(collected) >= max_messages:
            break
        msgs, slack_cursor = _channel_history_page(
            bot,
            cid,
            watermark,
            slack_cursor,
            limit=hist_limit,
        )
        room = max_messages - len(collected)
        if room <= 0:
            break
        msgs = msgs[:room]
        max_seen = _merge_max_slack_ts(msgs, max_seen)
        collected.extend(msgs)
        if not slack_cursor or not msgs:
            break
    return collected, max_seen


def _run_slack_channel(
    bot: WebClient,
    norm: dict[str, Any],
    scope: str,
    store: CursorStore,
) -> ScrapedEmbeds:
    cid = str(norm["conversationId"])
    hist_limit = int(norm["historyLimit"])
    max_msgs = int(norm["maxMessagesPerRun"])
    watermark = store.get_state("slack", scope, cid)
    collected, max_seen = _channel_history_drain(
        bot,
        cid,
        watermark,
        hist_limit=hist_limit,
        max_messages=max_msgs,
    )

    items = _build_items_from_messages(collected)
    if not items:
        return ScrapedEmbeds([], None)
    payload = _embed_payload(scope, items)

    def commit_cursor() -> None:
        if max_seen is not None:
            store.set_state("slack", scope, cid, _float_to_slack_ts(max_seen))

    return ScrapedEmbeds(
        [payload],
        commit_cursor if max_seen is not None else None,
    )


def _slack_run_job_body(
    source: str,
    norm: dict[str, Any],
    store: CursorStore,
    scope: str,
    rag_base: str,
    integration: str,
) -> None:
    user_token = os.environ.get("SLACK_USER_TOKEN", "").strip()
    bot_token = os.environ.get("SLACK_BOT_TOKEN", "").strip()

    if source == "slack_search":
        if not user_token:
            _die(
                "SLACK_USER_TOKEN is required for slack_search (assistant.search.context / RTS)."
            )
        user_client = WebClient(token=user_token)
        bot_client = WebClient(token=bot_token) if bot_token else None
        try:
            payload = _run_slack_search(user_client, bot_client, norm, scope)
        except SlackApiError as exc:
            _die(f"Slack API error: {_redact_token_like(str(exc))}")
        if payload:
            ingest_scraped_embeds(
                rag_base,
                integration,
                ScrapedEmbeds([payload], None),
            )
        return

    if not bot_token:
        _die("SLACK_BOT_TOKEN is required for slack_channel (conversations.history).")
    bot = WebClient(token=bot_token)
    try:
        batch = _run_slack_channel(bot, norm, scope, store)
    except SlackApiError as exc:
        _die(f"Slack API error: {_redact_token_like(str(exc))}")
    ingest_scraped_embeds(rag_base, integration, batch)


def run() -> None:
    integration = integration_label(
        os.environ.get("SCRAPER_INTEGRATION", ""),
        fallback="slack",
    )

    def main() -> None:
        cfg = _load_job_config()
        source, norm = _normalize_slack_job(cfg)
        rag_base = os.environ.get("RAG_SERVICE_URL", "").strip().rstrip("/")
        if not rag_base:
            _die("RAG_SERVICE_URL is required.")
        scope = os.environ.get("SCRAPER_SCOPE", "slack").strip() or "slack"
        store = cursor_store_from_env()
        _slack_run_job_body(source, norm, store, scope, rag_base, integration)

    run_scraper_main(integration, main)


if __name__ == "__main__":
    run()
