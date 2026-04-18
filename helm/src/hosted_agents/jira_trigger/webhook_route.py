"""HTTP POST handler: shared-secret verification and JSON webhook envelope."""

from __future__ import annotations

import json
import logging
import secrets
import uuid
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from hosted_agents.jira_trigger.config import JiraTriggerSettings
from hosted_agents.jira_trigger.dispatch import dispatch_jira_webhook
from hosted_agents.metrics import observe_jira_trigger_inbound

_LOG = logging.getLogger(__name__)


def _extract_inbound_secret(request: Request) -> str:
    """Secret material supplied by Jira or an operator-controlled proxy (never logged)."""
    q = request.query_params.get("secret")
    if isinstance(q, str) and q.strip():
        return q.strip()
    # Custom header for operators who cannot rely on query strings.
    h = request.headers.get("X-Jira-Webhook-Secret")
    if isinstance(h, str) and h.strip():
        return h.strip()
    return ""


def _verify_shared_secret(request: Request, configured: str) -> bool:
    incoming = _extract_inbound_secret(request)
    if not incoming or not configured:
        return False
    return secrets.compare_digest(configured, incoming)


def _json_object_from_body(raw_body: bytes) -> dict[str, Any]:
    try:
        data = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        observe_jira_trigger_inbound("http", "bad_json")
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(data, dict):
        observe_jira_trigger_inbound("http", "bad_json")
        raise HTTPException(status_code=400, detail="JSON body must be an object")
    return data


def register_jira_trigger_http_route(
    app: FastAPI, settings: JiraTriggerSettings
) -> None:
    """Register POST handler when Jira webhook verification is configured."""

    if not settings.http_configured():
        return

    secret = settings.webhook_secret
    http_path = settings.http_path

    @app.post(http_path)
    async def jira_webhook_callback(
        request: Request,
        background_tasks: BackgroundTasks,
    ) -> JSONResponse:
        raw_body = await request.body()
        if not _verify_shared_secret(request, secret):
            observe_jira_trigger_inbound("http", "rejected")
            raise HTTPException(status_code=401, detail="Invalid Jira webhook secret")

        payload = _json_object_from_body(raw_body)
        rid = getattr(request.state, "request_id", None) or request.headers.get(
            "x-request-id"
        )
        req_id = str(rid).strip() if rid else str(uuid.uuid4())
        delivery = (request.headers.get("X-Atlassian-Webhook-Identifier") or "").strip()

        deduper = getattr(request.app.state, "jira_trigger_deduper", None)

        def _run() -> None:
            try:
                dispatch_jira_webhook(
                    payload,
                    raw_body=raw_body,
                    request_id=req_id,
                    delivery_header=delivery,
                    deduper=deduper,
                    settings_event_dedupe=settings.event_dedupe,
                )
            except Exception:
                _LOG.exception("jira_trigger_webhook_dispatch_failed")

        background_tasks.add_task(_run)
        return JSONResponse({"ok": True})
