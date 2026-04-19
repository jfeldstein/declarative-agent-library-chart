"""HTTP POST handler: shared-secret verification and JSON webhook envelope."""

from __future__ import annotations

import logging
import secrets

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from agent.observability.middleware import publish_jira_trigger_inbound
from agent.triggers.http_common import parse_utf8_json_object, request_id_from_request
from agent.triggers.jira.config import JiraTriggerSettings
from agent.triggers.jira.dispatch import dispatch_jira_webhook

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
            publish_jira_trigger_inbound(transport="http", outcome="rejected")
            raise HTTPException(status_code=401, detail="Invalid Jira webhook secret")

        payload = parse_utf8_json_object(
            raw_body,
            on_bad_json=lambda: publish_jira_trigger_inbound(
                transport="http", outcome="bad_json"
            ),
        )
        req_id = request_id_from_request(request)
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
