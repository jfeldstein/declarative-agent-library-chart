"""Normalize Slack ``app_mention`` events into trigger identifiers."""

from __future__ import annotations

import re
from typing import Any

_MENTION_RE = re.compile(r"<@[^>]+>\s*")


def strip_leading_mentions(text: str) -> str:
    """Remove leading ``<@U…>`` segments; keep remainder as supervisor message."""
    s = (text or "").strip()
    while True:
        next_s = _MENTION_RE.sub("", s, count=1).strip()
        if next_s == s:
            break
        s = next_s
    return s.strip()


def slack_thread_id_for_event(event: dict[str, Any]) -> str:
    """Stable thread id: ``slack:<channel>:<conversation_root_ts>``."""
    channel = str(event.get("channel") or "").strip()
    root_ts = str(event.get("thread_ts") or event.get("ts") or "").strip()
    if not channel or not root_ts:
        return ""
    return f"slack:{channel}:{root_ts}"


def extract_app_mention(event: dict[str, Any]) -> tuple[str, str, str, str] | None:
    """Return ``message, channel_id, thread_ts, message_ts`` or None if unusable."""
    if str(event.get("type") or "") != "app_mention":
        return None
    channel_id = str(event.get("channel") or "").strip()
    message_ts = str(event.get("ts") or "").strip()
    thread_ts = str(event.get("thread_ts") or event.get("ts") or "").strip()
    text = strip_leading_mentions(str(event.get("text") or ""))
    if not channel_id or not message_ts:
        return None
    return text, channel_id, thread_ts, message_ts
