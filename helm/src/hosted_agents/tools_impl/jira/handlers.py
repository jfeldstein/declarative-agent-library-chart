"""Allowlisted Jira tool implementations."""

from __future__ import annotations

import re
from typing import Any

from hosted_agents.observability.side_effects import record_side_effect_checkpoint
from hosted_agents.tools_impl.jira.adf import plain_text_comment_body
from hosted_agents.tools_impl.jira.config import JiraToolsScopes, JiraToolsSettings
from hosted_agents.tools_impl.jira.rest import build_client, request_json

_ISSUE_KEY_RE = re.compile(r"^[A-Z][A-Z0-9_]*-\d+$")


def _require_issue_key(raw: object) -> str:
    key = str(raw or "").strip().upper()
    if not key or not _ISSUE_KEY_RE.match(key):
        msg = "issue_key must look like PROJ-123"
        raise ValueError(msg)
    return key


def _require_scope(scopes: JiraToolsScopes, name: str) -> None:
    if not getattr(scopes, name):
        msg = f"Jira tools scope '{name}' is not enabled for this deployment"
        raise ValueError(msg)


def _record_issue_checkpoint(
    *,
    tool_name: str,
    issue_key: str,
    extra: dict[str, str] | None = None,
) -> str:
    ref = {"issue_key": issue_key}
    if extra:
        ref.update(extra)
    se = record_side_effect_checkpoint(
        tool_name=tool_name,
        external_ref=ref,
    )
    return se.checkpoint_id


def _sim_return(
    tool_name: str,
    payload: dict[str, Any],
    *,
    issue_key: str | None,
    checkpoint: bool,
) -> dict[str, Any]:
    out = {"ok": True, "simulated": True, **payload}
    if checkpoint and issue_key:
        cid = _record_issue_checkpoint(tool_name=tool_name, issue_key=issue_key)
        out["checkpoint_id"] = cid
    return out


def run_search_issues(
    settings: JiraToolsSettings, arguments: dict[str, Any]
) -> dict[str, Any]:
    _require_scope(settings.scopes, "search")
    jql = str(arguments.get("jql") or "").strip()
    if not jql:
        msg = "jira.search_issues requires jql"
        raise ValueError(msg)
    if len(jql) > settings.max_jql_length:
        msg = "jql exceeds configured max length"
        raise ValueError(msg)
    raw_max = arguments.get("max_results")
    cap = settings.max_search_results
    try:
        req_max = int(raw_max) if raw_max is not None else cap
    except (TypeError, ValueError):
        req_max = cap
    max_results = max(1, min(cap, req_max))

    if settings.simulated:
        return _sim_return(
            "jira.search_issues",
            {
                "total": 1,
                "maxResults": max_results,
                "issues": [
                    {
                        "key": "SIM-1",
                        "fields": {
                            "summary": "simulated issue (jira.tools simulated mode)"
                        },
                    },
                ],
            },
            issue_key=None,
            checkpoint=False,
        )

    params = {
        "jql": jql,
        "maxResults": max_results,
        "fields": "summary,status,assignee",
    }
    path = "/rest/api/3/search"
    with build_client(settings) as client:
        body = request_json(client, settings, "GET", path, params=params)
    if body.get("ok") is False or body.get("error"):
        return body
    if "issues" not in body:
        return {"ok": False, "error": "unexpected_response"}
    return {"ok": True, "simulated": False, **body}


def run_get_issue(
    settings: JiraToolsSettings, arguments: dict[str, Any]
) -> dict[str, Any]:
    _require_scope(settings.scopes, "read")
    issue_key = _require_issue_key(arguments.get("issue_key"))

    if settings.simulated:
        return _sim_return(
            "jira.get_issue",
            {"key": issue_key, "fields": {"summary": "simulated issue"}},
            issue_key=None,
            checkpoint=False,
        )

    fields = arguments.get("fields")
    params: dict[str, Any] = {}
    if isinstance(fields, list) and fields:
        params["fields"] = ",".join(str(x) for x in fields)

    path = f"/rest/api/3/issue/{issue_key}"
    with build_client(settings) as client:
        body = request_json(client, settings, "GET", path, params=params or None)
    if body.get("ok") is False or body.get("error"):
        return body
    if "key" not in body and "id" not in body:
        return {"ok": False, "error": "unexpected_response"}
    return {"ok": True, "simulated": False, **body}


def run_add_comment(
    settings: JiraToolsSettings, arguments: dict[str, Any]
) -> dict[str, Any]:
    _require_scope(settings.scopes, "comment")
    issue_key = _require_issue_key(arguments.get("issue_key"))
    text = str(arguments.get("body") or "").strip()
    if not text:
        msg = "jira.add_comment requires non-empty body"
        raise ValueError(msg)

    if settings.simulated:
        return _sim_return(
            "jira.add_comment",
            {"issue_key": issue_key, "comment_id": "sim-comment"},
            issue_key=issue_key,
            checkpoint=True,
        )

    payload = {"body": plain_text_comment_body(text)}
    path = f"/rest/api/3/issue/{issue_key}/comment"
    with build_client(settings) as client:
        body = request_json(client, settings, "POST", path, json_body=payload)
    if body.get("ok") is False or body.get("error"):
        return body
    cid = _record_issue_checkpoint(tool_name="jira.add_comment", issue_key=issue_key)
    return {"ok": True, "simulated": False, **body, "checkpoint_id": cid}


def _transition_id_for_name(transitions: object, transition_name: str) -> str:
    if not isinstance(transitions, list) or not transition_name:
        return ""
    lower = transition_name.lower()
    for item in transitions:
        if not isinstance(item, dict):
            continue
        nm = str(item.get("name") or "").strip().lower()
        if nm == lower:
            return str(item.get("id") or "").strip()
    return ""


def _resolve_explicit_or_named_transition(
    client: object,
    settings: JiraToolsSettings,
    path_trans: str,
    explicit_id: str,
    transition_name: str,
) -> tuple[str, dict[str, Any] | None]:
    """Return ``(transition_id, error_body)``; error_body is set on GET failures."""

    if explicit_id:
        return explicit_id, None
    tr_body = request_json(client, settings, "GET", path_trans)
    if tr_body.get("ok") is False or tr_body.get("error"):
        return "", tr_body
    transitions = tr_body.get("transitions") if isinstance(tr_body, dict) else None
    return _transition_id_for_name(transitions, transition_name), None


def run_transition_issue(
    settings: JiraToolsSettings, arguments: dict[str, Any]
) -> dict[str, Any]:
    _require_scope(settings.scopes, "transition")
    issue_key = _require_issue_key(arguments.get("issue_key"))

    if settings.simulated:
        return _sim_return(
            "jira.transition_issue",
            {"issue_key": issue_key, "transition_id": "sim"},
            issue_key=issue_key,
            checkpoint=True,
        )

    tid = arguments.get("transition_id")
    explicit = str(tid).strip() if tid is not None else ""
    transition_name = str(arguments.get("transition_name") or "").strip()

    path_trans = f"/rest/api/3/issue/{issue_key}/transitions"
    with build_client(settings) as client:
        transition_id, err = _resolve_explicit_or_named_transition(
            client,
            settings,
            path_trans,
            explicit,
            transition_name,
        )
        if err is not None:
            return err
        if not transition_id:
            msg = "transition_id or transition_name must resolve for jira.transition_issue"
            raise ValueError(msg)

        post_body = {"transition": {"id": transition_id}}
        body = request_json(
            client,
            settings,
            "POST",
            path_trans,
            json_body=post_body,
        )

    if body.get("ok") is False or body.get("error"):
        return body
    cid = _record_issue_checkpoint(
        tool_name="jira.transition_issue",
        issue_key=issue_key,
        extra={"transition_id": transition_id},
    )
    return {"ok": True, "simulated": False, **body, "checkpoint_id": cid}


def run_create_issue(
    settings: JiraToolsSettings, arguments: dict[str, Any]
) -> dict[str, Any]:
    _require_scope(settings.scopes, "create")
    project_key = str(arguments.get("project_key") or "").strip().upper()
    summary = str(arguments.get("summary") or "").strip()
    issue_type = str(arguments.get("issue_type") or "").strip()
    if not project_key or not summary or not issue_type:
        msg = "jira.create_issue requires project_key, summary, issue_type"
        raise ValueError(msg)
    if (
        settings.allowed_project_keys
        and project_key not in settings.allowed_project_keys
    ):
        msg = "project_key is not in allowedProjectKeys for this deployment"
        raise ValueError(msg)

    if settings.simulated:
        fake_key = f"{project_key}-SIM"
        return _sim_return(
            "jira.create_issue",
            {"key": fake_key, "self": f"{settings.site_url}/browse/{fake_key}"},
            issue_key=fake_key,
            checkpoint=True,
        )

    fields: dict[str, Any] = {
        "project": {"key": project_key},
        "summary": summary,
        "issuetype": {"name": issue_type},
    }
    desc = str(arguments.get("description") or "").strip()
    if desc:
        fields["description"] = plain_text_comment_body(desc)

    payload = {"fields": fields}
    with build_client(settings) as client:
        body = request_json(
            client, settings, "POST", "/rest/api/3/issue", json_body=payload
        )

    if body.get("ok") is False or body.get("error"):
        return body
    key = str(body.get("key") or "")
    cid = _record_issue_checkpoint(
        tool_name="jira.create_issue",
        issue_key=key or project_key,
    )
    return {"ok": True, "simulated": False, **body, "checkpoint_id": cid}


def run_update_issue(
    settings: JiraToolsSettings, arguments: dict[str, Any]
) -> dict[str, Any]:
    _require_scope(settings.scopes, "update")
    issue_key = _require_issue_key(arguments.get("issue_key"))
    raw_fields = arguments.get("fields")
    if not isinstance(raw_fields, dict) or not raw_fields:
        msg = "jira.update_issue requires a non-empty fields object"
        raise ValueError(msg)

    if settings.allowed_project_keys:
        proj = raw_fields.get("project")
        pk = ""
        if isinstance(proj, dict):
            pk = str(proj.get("key") or "").strip().upper()
        elif isinstance(proj, str):
            pk = proj.strip().upper()
        if pk and pk not in settings.allowed_project_keys:
            msg = "update targets a project outside allowedProjectKeys"
            raise ValueError(msg)

    if settings.simulated:
        return _sim_return(
            "jira.update_issue",
            {"issue_key": issue_key, "updated": True},
            issue_key=issue_key,
            checkpoint=True,
        )

    payload = {"fields": raw_fields}
    path = f"/rest/api/3/issue/{issue_key}"
    with build_client(settings) as client:
        body = request_json(client, settings, "PUT", path, json_body=payload)

    if body.get("ok") is False or body.get("error"):
        return body
    cid = _record_issue_checkpoint(tool_name="jira.update_issue", issue_key=issue_key)
    return {"ok": True, "simulated": False, **body, "checkpoint_id": cid}
