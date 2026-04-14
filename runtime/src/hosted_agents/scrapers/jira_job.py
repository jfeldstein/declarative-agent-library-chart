"""Jira Cloud pull scraper: incremental JQL → comments → RAG ``/v1/embed``.

Uses ``httpx`` against Jira REST v3. Env includes ``JIRA_SITE_URL``, ``JIRA_EMAIL``,
``JIRA_API_TOKEN``, ``JIRA_PROJECT_KEYS`` (comma-separated), ``JIRA_WATERMARK_DIR``,
``SCRAPER_SCOPE``. See ``openspec/changes/jira-scraper/``.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import httpx

from hosted_agents.scrapers.metrics import (
    classify_rag_submission_result,
    maybe_start_scraper_metrics_http,
    observe_rag_embed_attempt,
    observe_scraper_run,
    stop_scraper_metrics_http,
)


def _integration_label() -> str:
    v = os.environ.get("SCRAPER_INTEGRATION", "jira").strip()
    return v or "jira"


def _site_base(url: str) -> str:
    u = url.strip().rstrip("/")
    if not u.startswith("https://"):
        print("JIRA_SITE_URL must be an https URL", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    return u


def _watermark_path(scope: str, project: str) -> Path:
    root = Path(os.environ.get("JIRA_WATERMARK_DIR", "/tmp/jira-scraper-watermark").strip())
    safe_scope = re.sub(r"[^a-zA-Z0-9._-]+", "_", scope)[:80]
    safe_proj = re.sub(r"[^a-zA-Z0-9._-]+", "_", project)[:32]
    root.mkdir(parents=True, exist_ok=True)
    return root / f"watermark-{safe_scope}-{safe_proj}.json"


def _read_watermark(path: Path, overlap_minutes: int) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        iso = str(data.get("last_updated", "")).strip()
        if not iso:
            return None
        raw = iso.replace("Z", "+00:00")
        if raw.endswith("+0000"):
            raw = raw[:-5] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt - timedelta(minutes=max(overlap_minutes, 0))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def _write_watermark(path: Path, iso: str) -> None:
    path.write_text(
        json.dumps({"last_updated": iso}, indent=2) + "\n",
        encoding="utf-8",
    )


def _default_fields() -> list[str]:
    return [
        "summary",
        "description",
        "status",
        "assignee",
        "issuelinks",
        "updated",
        "project",
        "issuetype",
    ]


def search_issues(
    client: httpx.Client,
    base: str,
    jql: str,
    fields: list[str],
    max_results: int,
) -> list[dict[str, Any]]:
    """POST /rest/api/3/search — used by tests and ``run()``."""
    url = f"{base.rstrip('/')}/rest/api/3/search"
    issues: list[dict[str, Any]] = []
    start_at = 0
    while len(issues) < max_results:
        body = {
            "jql": jql,
            "startAt": start_at,
            "maxResults": min(50, max_results - len(issues)),
            "fields": fields,
        }
        r = client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
        batch = data.get("issues", []) or []
        if not batch:
            break
        issues.extend(batch)
        start_at += len(batch)
        total = int(data.get("total", 0))
        if start_at >= total or len(batch) < body["maxResults"]:
            break
    return issues[:max_results]


def _fetch_comments(
    client: httpx.Client,
    base: str,
    issue_key: str,
    cap: int,
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    start = 0
    root = base.rstrip("/")
    while len(out) < cap:
        r = client.get(
            f"{root}/rest/api/3/issue/{issue_key}/comment",
            params={"startAt": start, "maxResults": min(100, cap - len(out))},
        )
        r.raise_for_status()
        data = r.json()
        comments = data.get("comments", []) or []
        if not comments:
            break
        out.extend(comments)
        start += len(comments)
        if int(data.get("total", 0)) <= start:
            break
    return out[:cap]


def _issue_text(
    issue: dict[str, Any],
    comments: list[dict[str, Any]],
    max_comments: int,
    truncated: bool,
) -> str:
    fields = issue.get("fields", {}) or {}
    key = issue.get("key", "")
    lines = [f"Issue {key}", f"Summary: {fields.get('summary', '')}"]
    desc = fields.get("description")
    if isinstance(desc, dict):
        lines.append(f"Description: {json.dumps(desc)[:8000]}")
    elif desc:
        lines.append(f"Description: {str(desc)[:8000]}")
    st = fields.get("status") or {}
    if isinstance(st, dict):
        lines.append(f"Status: {st.get('name', '')}")
    assignee = fields.get("assignee") or {}
    if isinstance(assignee, dict):
        lines.append(
            f"Assignee: {assignee.get('displayName', assignee.get('accountId', ''))}"
        )
    links = fields.get("issuelinks") or []
    if isinstance(links, list) and links:
        lines.append("Links:")
        for ln in links[:50]:
            lines.append(json.dumps(ln)[:500])
    lines.append("Comments:")
    for c in comments[:max_comments]:
        body = c.get("body")
        if isinstance(body, dict):
            body_s = json.dumps(body)[:2000]
        else:
            body_s = str(body or "")[:2000]
        author = (c.get("author") or {}).get("displayName", "")
        created = c.get("created", "")
        lines.append(f"- {created} {author}: {body_s}")
    if truncated:
        lines.append("(comments truncated by maxCommentsPerIssue cap)")
    return "\n".join(lines)


def _embed_for_issue(
    scope: str,
    issue: dict[str, Any],
    text: str,
) -> dict[str, Any]:
    key = issue.get("key", "unknown")
    return {
        "scope": scope,
        "entities": [],
        "relationships": [],
        "items": [
            {
                "text": text,
                "metadata": {
                    "source": "jira-scraper",
                    "jira_issue_key": key,
                    "jira_updated": (issue.get("fields") or {}).get("updated", ""),
                },
                "entity_id": f"jira:{key}",
            },
        ],
    }


def run() -> None:
    t0 = time.perf_counter()
    integration = _integration_label()
    httpd = maybe_start_scraper_metrics_http()
    run_ok = False
    try:
        site = _site_base(os.environ.get("JIRA_SITE_URL", ""))
        email = os.environ.get("JIRA_EMAIL", "").strip()
        token = os.environ.get("JIRA_API_TOKEN", "").strip()
        if not email or not token:
            print("JIRA_EMAIL and JIRA_API_TOKEN are required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        projects_raw = os.environ.get("JIRA_PROJECT_KEYS", "").strip()
        if not projects_raw:
            print("JIRA_PROJECT_KEYS is required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        projects = [p.strip() for p in projects_raw.split(",") if p.strip()]
        rag_base = os.environ.get("RAG_SERVICE_URL", "").strip().rstrip("/")
        if not rag_base:
            print("RAG_SERVICE_URL is required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        scope = os.environ.get("SCRAPER_SCOPE", "jira").strip() or "jira"
        max_issues = int(os.environ.get("JIRA_MAX_ISSUES_PER_RUN", "50"))
        max_comments = int(os.environ.get("JIRA_MAX_COMMENTS_PER_ISSUE", "100"))
        overlap = int(os.environ.get("JIRA_OVERLAP_MINUTES", "5"))
        fields = _default_fields()
        extra = os.environ.get("JIRA_EXTRA_FIELDS_JSON", "").strip()
        if extra:
            try:
                parsed = json.loads(extra)
                if isinstance(parsed, list):
                    fields = list(dict.fromkeys(fields + [str(x) for x in parsed]))
            except json.JSONDecodeError:
                pass

        all_payloads: list[dict[str, Any]] = []
        with httpx.Client(
            timeout=120.0,
            auth=(email, token),
            headers={"Accept": "application/json"},
        ) as client:
            for proj in projects:
                wm_path = _watermark_path(scope, proj)
                wm = _read_watermark(wm_path, overlap)
                if wm:
                    jql = f'project = "{proj}" AND updated >= "{wm}" ORDER BY updated ASC'
                else:
                    jql = f'project = "{proj}" ORDER BY updated DESC'
                issues = search_issues(client, site, jql, fields, max_issues)
                max_upd: str | None = None
                for issue in issues:
                    key = issue.get("key", "")
                    raw_comments = _fetch_comments(client, site, key, max_comments + 1)
                    truncated = len(raw_comments) > max_comments
                    comments = raw_comments[:max_comments]
                    text = _issue_text(issue, comments, max_comments, truncated)
                    all_payloads.append(_embed_for_issue(scope, issue, text))
                    upd = (issue.get("fields") or {}).get("updated")
                    if isinstance(upd, str):
                        max_upd = max(max_upd, upd) if max_upd else upd
                if max_upd:
                    _write_watermark(wm_path, max_upd)

        if not all_payloads:
            run_ok = True
        else:
            with httpx.Client(timeout=120.0) as hx:
                for payload in all_payloads:
                    try:
                        r = hx.post(f"{rag_base}/v1/embed", json=payload)
                        r.raise_for_status()
                    except httpx.HTTPError as exc:
                        observe_rag_embed_attempt(
                            integration, classify_rag_submission_result(exc)
                        )
                        raise
                    observe_rag_embed_attempt(integration, "success")
            run_ok = True
    finally:
        elapsed = time.perf_counter() - t0
        observe_scraper_run(integration, run_ok, elapsed)
        stop_scraper_metrics_http(httpd)


if __name__ == "__main__":
    run()
