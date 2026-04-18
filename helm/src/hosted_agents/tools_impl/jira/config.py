"""Load Jira tools settings from ``HOSTED_AGENT_JIRA_TOOLS_*`` (disjoint from scraper env)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


def _truthy(raw: str) -> bool:
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _env_int(key: str, default: int) -> int:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def _load_json_object(key: str) -> dict[str, object]:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return {}
    data = json.loads(raw)
    if not isinstance(data, dict):
        msg = f"{key} must be a JSON object"
        raise ValueError(msg)
    return dict(data)


def _load_json_str_list(key: str) -> list[str]:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        msg = f"{key} must be a JSON array of strings"
        raise ValueError(msg)
    return [str(x) for x in data]


@dataclass(frozen=True)
class JiraToolsScopes:
    search: bool = False
    read: bool = False
    comment: bool = False
    transition: bool = False
    create: bool = False
    update: bool = False


@dataclass(frozen=True)
class JiraToolsSettings:
    """Effective settings for Jira REST tools."""

    enabled: bool
    simulated: bool
    site_url: str
    email: str
    api_token: str
    timeout_seconds: float
    scopes: JiraToolsScopes
    allowed_project_keys: frozenset[str]
    max_search_results: int
    max_jql_length: int


def load_settings() -> JiraToolsSettings | None:
    """Return settings when tools are enabled; otherwise ``None``."""

    raw_en = os.environ.get("HOSTED_AGENT_JIRA_TOOLS_ENABLED", "").strip()
    if not raw_en or not _truthy(raw_en):
        return None

    simulated = _truthy(os.environ.get("HOSTED_AGENT_JIRA_TOOLS_SIMULATED", "true"))
    site_url = (
        os.environ.get("HOSTED_AGENT_JIRA_TOOLS_SITE_URL", "").strip().rstrip("/")
    )
    email = os.environ.get("HOSTED_AGENT_JIRA_TOOLS_EMAIL", "").strip()
    api_token = os.environ.get("HOSTED_AGENT_JIRA_TOOLS_API_TOKEN", "").strip()

    if not simulated and (not site_url or not email or not api_token):
        simulated = True

    scopes_obj = _load_json_object("HOSTED_AGENT_JIRA_TOOLS_SCOPES_JSON")
    scopes = JiraToolsScopes(
        search=bool(scopes_obj.get("search")),
        read=bool(scopes_obj.get("read")),
        comment=bool(scopes_obj.get("comment")),
        transition=bool(scopes_obj.get("transition")),
        create=bool(scopes_obj.get("create")),
        update=bool(scopes_obj.get("update")),
    )
    allowed = frozenset(
        x.upper()
        for x in _load_json_str_list(
            "HOSTED_AGENT_JIRA_TOOLS_ALLOWED_PROJECT_KEYS_JSON"
        )
    )
    return JiraToolsSettings(
        enabled=True,
        simulated=simulated,
        site_url=site_url,
        email=email,
        api_token=api_token,
        timeout_seconds=float(_env_int("HOSTED_AGENT_JIRA_TOOLS_TIMEOUT_SECONDS", 30)),
        scopes=scopes,
        allowed_project_keys=allowed,
        max_search_results=max(
            1, _env_int("HOSTED_AGENT_JIRA_TOOLS_MAX_SEARCH_RESULTS", 50)
        ),
        max_jql_length=max(
            16, _env_int("HOSTED_AGENT_JIRA_TOOLS_MAX_JQL_LENGTH", 4000)
        ),
    )
