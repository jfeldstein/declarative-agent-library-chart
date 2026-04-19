"""HTTP Events API endpoint: URL verification, signing-secret verification, ``event_callback``."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from slack_sdk.signature import SignatureVerifier

from agent.metrics import observe_slack_trigger_inbound
from agent.triggers.http_common import parse_utf8_json_object, request_id_from_request
from agent.triggers.slack.config import SlackTriggerSettings
from agent.triggers.slack.dispatch import dispatch_app_mention

_LOG = logging.getLogger(__name__)


def _verify_slack_signature(
    *,
    raw_body: bytes,
    signing_secret: str,
    timestamp: str,
    signature: str,
) -> bool:
    verifier = SignatureVerifier(signing_secret)
    if not timestamp or not signature:
        return False
    return bool(verifier.is_valid(raw_body, timestamp, signature))


def _slack_http_response_for_payload(
    payload: dict[str, Any],
    *,
    request: Request,
    background_tasks: BackgroundTasks,
    settings: SlackTriggerSettings,
) -> JSONResponse:
    type_ = str(payload.get("type") or "")

    if type_ == "url_verification":
        challenge = payload.get("challenge")
        if not isinstance(challenge, str) or not challenge.strip():
            observe_slack_trigger_inbound("http", "ignored")
            raise HTTPException(
                status_code=400, detail="Missing url_verification challenge"
            )
        observe_slack_trigger_inbound("http", "challenge_ok")
        return JSONResponse({"challenge": challenge})

    if type_ != "event_callback":
        observe_slack_trigger_inbound("http", "ignored")
        return JSONResponse({"ok": True})

    deduper = getattr(request.app.state, "slack_trigger_deduper", None)
    req_id = request_id_from_request(request)

    def _run() -> None:
        try:
            dispatch_app_mention(
                payload,
                transport="http",
                request_id=req_id,
                deduper=deduper,
                settings_event_dedupe=settings.event_dedupe,
            )
        except Exception:
            _LOG.exception("slack_trigger_http_dispatch_failed")

    background_tasks.add_task(_run)
    return JSONResponse({"ok": True})


def register_slack_trigger_http_route(
    app: FastAPI, settings: SlackTriggerSettings
) -> None:
    """Register POST handler when HTTP Events API is configured (signing secret present)."""

    if not settings.enabled or not settings.http_events_configured():
        return

    signing_secret = settings.signing_secret
    http_path = settings.http_path

    @app.post(http_path)
    async def slack_events_callback(
        request: Request,
        background_tasks: BackgroundTasks,
    ) -> JSONResponse:
        raw_body = await request.body()
        ts = (request.headers.get("X-Slack-Request-Timestamp") or "").strip()
        sig = (request.headers.get("X-Slack-Signature") or "").strip()
        if not _verify_slack_signature(
            raw_body=raw_body,
            signing_secret=signing_secret,
            timestamp=ts,
            signature=sig,
        ):
            observe_slack_trigger_inbound("http", "rejected")
            raise HTTPException(status_code=401, detail="Invalid Slack signature")

        payload = parse_utf8_json_object(
            raw_body,
            on_bad_json=lambda: observe_slack_trigger_inbound("http", "bad_json"),
        )
        return _slack_http_response_for_payload(
            payload,
            request=request,
            background_tasks=background_tasks,
            settings=settings,
        )
