"""Jira Cloud pull scraper: job JSON (JQL) → comments → RAG ``/v1/embed``.

Config is mounted at ``SCRAPER_JOB_CONFIG`` (default ``/config/job.json``) with
``source: jira`` and ``query`` (JQL). Secrets: ``JIRA_SITE_URL``, ``JIRA_EMAIL``,
``JIRA_API_TOKEN``, ``JIRA_WATERMARK_DIR`` from env. Unknown ``source`` exits non-zero.

Search uses **``POST /rest/api/3/search/jql``** with ``nextPageToken`` pagination.
See ``openspec/changes/jira-scraper/``.
"""

from __future__ import annotations

import hashlib
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
from hosted_agents.scrapers.cursor_store import cursor_store_from_env


def _integration_label() -> str:
    v = os.environ.get("SCRAPER_INTEGRATION", "jira").strip()
    return v or "jira"


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


def _site_base(url: str) -> str:
    u = url.strip().rstrip("/")
    if not u.startswith("https://"):
        print("JIRA_SITE_URL must be an https URL", file=sys.stderr)  # noqa: T201
        sys.exit(1)
    return u


def _watermark_path(scope: str, query: str) -> Path:
    root = Path(os.environ.get("JIRA_WATERMARK_DIR", "/tmp/jira-scraper-watermark").strip())
    safe_scope = re.sub(r"[^a-zA-Z0-9._-]+", "_", scope)[:80]
    qhash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:24]
    root.mkdir(parents=True, exist_ok=True)
    return root / f"watermark-{safe_scope}-{qhash}.json"


def _jql_watermark_after_overlap(last_updated_iso: str | None, overlap_minutes: int) -> str | None:
    """Turn stored Jira ``last_updated`` ISO into the JQL ``updated >=`` string (with overlap)."""
    if not last_updated_iso:
        return None
    try:
        raw = str(last_updated_iso).replace("Z", "+00:00")
        if raw.endswith("+0000"):
            raw = raw[:-5] + "+00:00"
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt - timedelta(minutes=max(overlap_minutes, 0))
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return None


def _read_watermark(path: Path, overlap_minutes: int) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        iso = str(data.get("last_updated", "")).strip()
    except (OSError, json.JSONDecodeError):
        return None
    return _jql_watermark_after_overlap(iso or None, overlap_minutes)


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
    """POST /rest/api/3/search/jql — JQL enhanced search with ``nextPageToken`` pagination."""
    url = f"{base.rstrip('/')}/rest/api/3/search/jql"
    issues: list[dict[str, Any]] = []
    next_page_token: str | None = None
    while len(issues) < max_results:
        page_size = min(50, max_results - len(issues))
        body: dict[str, Any] = {
            "jql": jql,
            "fields": fields,
            "maxResults": page_size,
        }
        if next_page_token:
            body["nextPageToken"] = next_page_token
        r = client.post(url, json=body)
        r.raise_for_status()
        data = r.json()
        batch = data.get("issues", []) or []
        if not batch:
            break
        issues.extend(batch)
        raw_token = data.get("nextPageToken")
        if raw_token is None or raw_token == "":
            break
        token = str(raw_token).strip()
        if not token or token == next_page_token:
            break
        next_page_token = token
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


def _build_jql(base_query: str, watermark_iso: str | None) -> str:
    q = base_query.strip()
    if not q:
        return q
    if watermark_iso:
        return f'({q}) AND updated >= "{watermark_iso}" ORDER BY updated ASC'
    return q


def run() -> None:
    t0 = time.perf_counter()
    integration = _integration_label()
    httpd = maybe_start_scraper_metrics_http()
    run_ok = False
    try:
        cfg = _load_job_config()
        if str(cfg.get("source", "")).strip().lower() != "jira":
            print("Job config source must be jira", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        base_query = str(cfg.get("query", "")).strip()
        if not base_query:
            print("Job config query (JQL) is required", file=sys.stderr)  # noqa: T201
            sys.exit(1)

        site = _site_base(os.environ.get("JIRA_SITE_URL", ""))
        email = os.environ.get("JIRA_EMAIL", "").strip()
        token = os.environ.get("JIRA_API_TOKEN", "").strip()
        if not email or not token:
            print("JIRA_EMAIL and JIRA_API_TOKEN are required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        rag_base = os.environ.get("RAG_SERVICE_URL", "").strip().rstrip("/")
        if not rag_base:
            print("RAG_SERVICE_URL is required", file=sys.stderr)  # noqa: T201
            sys.exit(1)
        scope = os.environ.get("SCRAPER_SCOPE", "jira").strip() or "jira"
        max_issues = int(cfg.get("maxIssuesPerRun", 50))
        max_comments = int(cfg.get("maxCommentsPerIssue", 100))
        overlap = int(cfg.get("overlapMinutes", 5))
        fields = _default_fields()
        extra = cfg.get("extraFields")
        if isinstance(extra, list):
            fields = list(dict.fromkeys(fields + [str(x) for x in extra]))

        store = cursor_store_from_env()
        wm = _jql_watermark_after_overlap(store.get_state("jira", scope, base_query), overlap)
        jql = _build_jql(base_query, wm)

        all_payloads: list[dict[str, Any]] = []
        with httpx.Client(
            timeout=120.0,
            auth=(email, token),
            headers={"Accept": "application/json"},
        ) as client:
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
                store.set_state("jira", scope, base_query, max_upd)

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
