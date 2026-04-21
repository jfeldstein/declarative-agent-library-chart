"""Jira Cloud pull scraper: job JSON (JQL) → comments → RAG ``/v1/embed``.

Config is mounted at ``SCRAPER_JOB_CONFIG`` (default ``/config/job.json``) with
``source: jira`` and ``query`` (JQL). Secrets: ``JIRA_SITE_URL``, ``JIRA_EMAIL``,
``JIRA_API_TOKEN``, ``JIRA_WATERMARK_DIR`` from env. Unknown ``source`` exits non-zero.

Search uses **``POST /rest/api/3/search/jql``** with ``nextPageToken`` pagination.
See ``openspec/changes/jira-scraper/``.

Traceability: [DALC-REQ-SCRAPER-BASE-002]
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any

import httpx

from agent.scrapers.base import (
    ScrapedEmbeds,
    ingest_from_integration,
    integration_label,
    run_scraper_main,
)
from agent.scrapers.cursor_store import cursor_store_from_env


def _eprint(msg: str) -> None:
    """Print to stderr with secrets from env redacted (Jira email + API token)."""
    t = str(msg)
    tok = os.environ.get("JIRA_API_TOKEN", "").strip()
    if tok:
        t = t.replace(tok, "<redacted>")
    em = os.environ.get("JIRA_EMAIL", "").strip()
    if em:
        t = t.replace(em, "<redacted>")
    print(t, file=sys.stderr)  # noqa: T201


def _retry_after_sleep_s(headers: httpx.Headers) -> float:
    raw = (headers.get("retry-after") or "").strip()
    if not raw:
        return 1.0
    try:
        sec = float(raw)
        return min(max(sec, 0.0), 600.0)
    except ValueError:
        try:
            dt = parsedate_to_datetime(raw)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = (dt - datetime.now(timezone.utc)).total_seconds()
            return min(max(delta, 0.0), 600.0)
        except (TypeError, ValueError, OverflowError):
            return 1.0


def jira_request(
    client: httpx.Client,
    method: str,
    url: str,
    *,
    max_rate_limit_retries: int = 10,
    **kwargs: Any,
) -> httpx.Response:
    """Perform a Jira REST request with **429** handling via ``Retry-After`` backoff."""
    attempt = 0
    while True:
        r = client.request(method, url, **kwargs)
        if r.status_code != 429:
            r.raise_for_status()
            return r
        attempt += 1
        if attempt > max_rate_limit_retries:
            r.raise_for_status()
            return r
        time.sleep(_retry_after_sleep_s(r.headers))


def _http_timeout_seconds() -> float:
    raw = os.environ.get("JIRA_HTTP_TIMEOUT_SECONDS", "").strip()
    if not raw:
        return 120.0
    try:
        return max(float(raw), 1.0)
    except ValueError:
        return 120.0


def _load_job_config() -> dict[str, Any]:
    raw_path = os.environ.get("SCRAPER_JOB_CONFIG", "/config/job.json").strip()
    p = Path(raw_path)
    if not p.is_file():
        _eprint(f"SCRAPER_JOB_CONFIG file not found: {p}")
        sys.exit(1)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        _eprint(f"Invalid job config JSON: {exc}")
        sys.exit(1)
    if not isinstance(data, dict):
        _eprint("Job config must be a JSON object")
        sys.exit(1)
    return data


def _site_base(url: str) -> str:
    u = url.strip().rstrip("/")
    if not u.startswith("https://"):
        _eprint("JIRA_SITE_URL must be an https URL")
        sys.exit(1)
    return u


def _watermark_path(scope: str, query: str) -> Path:
    root = Path(
        os.environ.get("JIRA_WATERMARK_DIR", "/tmp/jira-scraper-watermark").strip()
    )
    safe_scope = re.sub(r"[^a-zA-Z0-9._-]+", "_", scope)[:80]
    qhash = hashlib.sha256(query.encode("utf-8")).hexdigest()[:24]
    root.mkdir(parents=True, exist_ok=True)
    return root / f"watermark-{safe_scope}-{qhash}.json"


def _jql_watermark_after_overlap(
    last_updated_iso: str | None, overlap_minutes: int
) -> str | None:
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
        r = jira_request(client, "POST", url, json=body)
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
        r = jira_request(
            client,
            "GET",
            f"{root}/rest/api/3/issue/{issue_key}/comment",
            params={"startAt": start, "maxResults": min(100, cap - len(out))},
        )
        data = r.json()
        comments = data.get("comments", []) or []
        if not comments:
            break
        out.extend(comments)
        start += len(comments)
        if int(data.get("total", 0)) <= start:
            break
    return out[:cap]


def _issue_field_lines(fields: dict[str, Any], key: str) -> list[str]:
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
    return lines


def _as_issue_dict(val: Any) -> dict[str, Any]:
    return val if isinstance(val, dict) else {}


def _issue_link_endpoint_keys(ln: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    typ = _as_issue_dict(ln.get("type"))
    inward = _as_issue_dict(ln.get("inwardIssue"))
    outward = _as_issue_dict(ln.get("outwardIssue"))
    ik = inward.get("key")
    ok = outward.get("key")
    ik_s = str(ik) if ik else ""
    ok_s = str(ok) if ok else ""
    return ik_s, ok_s, typ


def _append_issue_link_edges(
    out: list[dict[str, str]],
    seen: set[tuple[str, str, str]],
    issue_key: str,
    ik_s: str,
    ok_s: str,
    typ: dict[str, Any],
    default_name: str,
) -> None:
    cur = f"jira:{issue_key}"
    if ik_s == issue_key and ok_s:
        rt = str(typ.get("outward") or default_name)[:256]
        key_t = (cur, f"jira:{ok_s}", rt)
        if key_t not in seen:
            seen.add(key_t)
            out.append(
                {"source": cur, "target": f"jira:{ok_s}", "relationship_type": rt}
            )
        return
    if ok_s == issue_key and ik_s:
        rt = str(typ.get("inward") or default_name)[:256]
        key_t = (f"jira:{ik_s}", cur, rt)
        if key_t not in seen:
            seen.add(key_t)
            out.append(
                {"source": f"jira:{ik_s}", "target": cur, "relationship_type": rt},
            )


def _relationships_from_issue_links(
    issue_key: str,
    links: Any,
    *,
    max_links: int = 200,
) -> list[dict[str, str]]:
    """Structured RAG edges from ``fields.issuelinks`` (distinct from flattened link text)."""
    out: list[dict[str, str]] = []
    if not isinstance(links, list):
        return out
    seen: set[tuple[str, str, str]] = set()
    for ln in links[:max_links]:
        if not isinstance(ln, dict):
            continue
        ik_s, ok_s, typ = _issue_link_endpoint_keys(ln)
        default_name = str(typ.get("name") or "related")
        _append_issue_link_edges(out, seen, issue_key, ik_s, ok_s, typ, default_name)
    return out


def _issue_comment_lines(
    comments: list[dict[str, Any]], max_comments: int
) -> list[str]:
    lines: list[str] = ["Comments:"]
    for c in comments[:max_comments]:
        body = c.get("body")
        if isinstance(body, dict):
            body_s = json.dumps(body)[:2000]
        else:
            body_s = str(body or "")[:2000]
        author = (c.get("author") or {}).get("displayName", "")
        created = c.get("created", "")
        lines.append(f"- {created} {author}: {body_s}")
    return lines


def _issue_text(
    issue: dict[str, Any],
    comments: list[dict[str, Any]],
    max_comments: int,
    truncated: bool,
) -> str:
    fields = issue.get("fields", {}) or {}
    key = issue.get("key", "")
    lines = _issue_field_lines(fields, str(key))
    lines.extend(_issue_comment_lines(comments, max_comments))
    if truncated:
        lines.append("(comments truncated by maxCommentsPerIssue cap)")
    return "\n".join(lines)


def _embed_for_issue(
    scope: str,
    issue: dict[str, Any],
    text: str,
    site_base: str,
) -> dict[str, Any]:
    fields = issue.get("fields") or {}
    key = str(issue.get("key") or "unknown")
    proj = fields.get("project") if isinstance(fields.get("project"), dict) else {}
    proj_key = str(proj.get("key") or "")
    root = site_base.rstrip("/")
    issue_url = f"{root}/browse/{key}" if key != "unknown" else ""
    links = fields.get("issuelinks")
    rels = _relationships_from_issue_links(key, links)
    return {
        "scope": scope,
        "entities": [],
        "relationships": rels,
        "items": [
            {
                "text": text,
                "metadata": {
                    "source": "jira-scraper",
                    "jira_issue_key": key,
                    "jira_project_key": proj_key,
                    "jira_issue_url": issue_url,
                    "jira_updated": fields.get("updated", ""),
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


def _jira_issue_fields(cfg: dict[str, Any]) -> list[str]:
    fields = _default_fields()
    extra = cfg.get("extraFields")
    if isinstance(extra, list):
        fields = list(dict.fromkeys(fields + [str(x) for x in extra]))
    return fields


def _jira_build_embed_payloads(
    client: httpx.Client,
    site: str,
    jql: str,
    fields: list[str],
    scope: str,
    max_issues: int,
    max_comments: int,
) -> tuple[list[dict[str, Any]], str | None]:
    issues = search_issues(client, site, jql, fields, max_issues)
    max_upd: str | None = None
    all_payloads: list[dict[str, Any]] = []
    for issue in issues:
        issue_key = str(issue.get("key", ""))
        raw_comments = _fetch_comments(client, site, issue_key, max_comments + 1)
        truncated = len(raw_comments) > max_comments
        comments = raw_comments[:max_comments]
        text = _issue_text(issue, comments, max_comments, truncated)
        all_payloads.append(_embed_for_issue(scope, issue, text, site))
        upd = (issue.get("fields") or {}).get("updated")
        if isinstance(upd, str):
            max_upd = max(max_upd, upd) if max_upd else upd
    return all_payloads, max_upd


def _jira_validate_config_and_env(
    cfg: dict[str, Any],
) -> tuple[str, str, str, str, str, str]:
    if str(cfg.get("source", "")).strip().lower() != "jira":
        _eprint("Job config source must be jira")
        sys.exit(1)
    base_query = str(cfg.get("query", "")).strip()
    if not base_query:
        _eprint("Job config query (JQL) is required")
        sys.exit(1)

    site = _site_base(os.environ.get("JIRA_SITE_URL", ""))
    email = os.environ.get("JIRA_EMAIL", "").strip()
    token = os.environ.get("JIRA_API_TOKEN", "").strip()
    if not email or not token:
        _eprint("JIRA_EMAIL and JIRA_API_TOKEN are required")
        sys.exit(1)
    rag_base = os.environ.get("RAG_SERVICE_URL", "").strip().rstrip("/")
    if not rag_base:
        _eprint("RAG_SERVICE_URL is required")
        sys.exit(1)
    scope = os.environ.get("SCRAPER_SCOPE", "jira").strip() or "jira"
    return site, email, token, rag_base, scope, base_query


class _JiraIntegration:
    """Fetch Jira REST + comment pages; emit ``ScrapedEmbeds`` only (no RAG HTTP here)."""

    __slots__ = ("_cfg", "_site", "_email", "_token", "_scope", "_base_query")

    def __init__(
        self,
        cfg: dict[str, Any],
        *,
        site: str,
        email: str,
        token: str,
        scope: str,
        base_query: str,
    ) -> None:
        self._cfg = cfg
        self._site = site
        self._email = email
        self._token = token
        self._scope = scope
        self._base_query = base_query

    def build_batch(self) -> ScrapedEmbeds:
        max_issues = int(self._cfg.get("maxIssuesPerRun", 50))
        max_comments = int(self._cfg.get("maxCommentsPerIssue", 100))
        overlap = int(self._cfg.get("overlapMinutes", 5))
        fields = _jira_issue_fields(self._cfg)

        store = cursor_store_from_env()
        wm = _jql_watermark_after_overlap(
            store.get_state("jira", self._scope, self._base_query), overlap
        )
        jql = _build_jql(self._base_query, wm)

        tout = _http_timeout_seconds()
        with httpx.Client(
            timeout=httpx.Timeout(tout),
            auth=(self._email, self._token),
            headers={"Accept": "application/json"},
        ) as client:
            all_payloads, max_upd = _jira_build_embed_payloads(
                client,
                self._site,
                jql,
                fields,
                self._scope,
                max_issues,
                max_comments,
            )

        def commit_watermark() -> None:
            if max_upd:
                store.set_state("jira", self._scope, self._base_query, max_upd)

        return ScrapedEmbeds(all_payloads, commit_watermark if max_upd else None)


def run() -> None:
    integration = integration_label(
        os.environ.get("SCRAPER_INTEGRATION", ""),
        fallback="jira",
    )

    def main() -> None:
        cfg = _load_job_config()
        site, email, token, rag_base, scope, base_query = _jira_validate_config_and_env(
            cfg
        )
        scraper = _JiraIntegration(
            cfg, site=site, email=email, token=token, scope=scope, base_query=base_query
        )
        ingest_from_integration(
            rag_base=rag_base,
            integration=integration,
            scraper=scraper,
            timeout=_http_timeout_seconds(),
        )

    run_scraper_main(integration, main)


if __name__ == "__main__":
    run()
