"""Normalize Jira Cloud-style webhook JSON into trigger-oriented text and ids."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def _as_str(v: object | None) -> str:
    if v is None:
        return ""
    if isinstance(v, str):
        return v.strip()
    return str(v).strip()


def _issue_obj(payload: dict[str, Any]) -> dict[str, Any] | None:
    raw = payload.get("issue")
    return raw if isinstance(raw, dict) else None


def _project_key(issue: dict[str, Any]) -> str | None:
    fields = issue.get("fields")
    if not isinstance(fields, dict):
        return None
    proj = fields.get("project")
    if isinstance(proj, dict):
        key = _as_str(proj.get("key"))
        return key or None
    return None


def _changelog_text(payload: dict[str, Any]) -> str:
    changelog = payload.get("changelog")
    if not isinstance(changelog, dict):
        return ""
    items = changelog.get("items")
    if not isinstance(items, list):
        return ""
    lines: list[str] = []
    for it in items:
        if not isinstance(it, dict):
            continue
        field = _as_str(it.get("field"))
        frm = _as_str(it.get("fromString"))
        to = _as_str(it.get("toString"))
        if field:
            lines.append(f"{field}: {frm!s} → {to!s}")
    return "\n".join(lines)


def _issue_summary_line(issue: dict[str, Any]) -> str | None:
    key = _as_str(issue.get("key"))
    fields = issue.get("fields")
    summary = ""
    if isinstance(fields, dict):
        summary = _as_str(fields.get("summary"))
    head = f"[{key}]" if key else "[issue]"
    if summary:
        return f"{head} {summary}"
    if key:
        return head
    return None


def _comment_section(payload: dict[str, Any]) -> str | None:
    comment = payload.get("comment")
    if not isinstance(comment, dict):
        return None
    body = _as_str(comment.get("body"))
    if not body:
        return None
    return f"Comment:\n{body}"


def build_jira_trigger_message(payload: dict[str, Any]) -> str:
    """Human-readable message for ``TriggerBody.message`` (no secrets)."""
    parts: list[str] = []
    webhook_event = _as_str(payload.get("webhookEvent"))
    if webhook_event:
        parts.append(f"Event: {webhook_event}")

    issue = _issue_obj(payload)
    if issue:
        summary_line = _issue_summary_line(issue)
        if summary_line:
            parts.append(summary_line)

    comment_line = _comment_section(payload)
    if comment_line:
        parts.append(comment_line)

    clog = _changelog_text(payload)
    if clog:
        parts.append(f"Changelog:\n{clog}")

    if not parts:
        return ""
    return "\n\n".join(parts)


def extract_issue_context(
    payload: dict[str, Any],
) -> tuple[str | None, str | None, str]:
    """Return ``issue_key``, ``project_key``, ``webhook_event`` (may be empty)."""
    issue = _issue_obj(payload)
    issue_key = _as_str(issue.get("key")) if issue else None
    project_key = _project_key(issue) if issue else None
    webhook_event = _as_str(payload.get("webhookEvent"))
    return (
        issue_key or None,
        project_key or None,
        webhook_event,
    )


def stable_thread_suffix(
    *, header_delivery_id: str, payload: dict[str, Any], raw_body: bytes
) -> str:
    """Bounded id for ``thread_id`` segment (never secrets)."""
    hid = header_delivery_id.strip()
    if hid:
        return hid[:200]
    basis = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    digest = hashlib.sha256(basis + raw_body).hexdigest()[:24]
    return f"h_{digest}"
