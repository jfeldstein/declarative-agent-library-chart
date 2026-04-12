"""HTTP surface for hosted agent (generic trigger)."""

from __future__ import annotations

import json
import time
import uuid

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from hosted_agents.agent_models import RagQueryBody, TriggerBody
from hosted_agents.agent_tracing import observability_summary
from hosted_agents.checkpointing import checkpoints_globally_enabled
from hosted_agents.env import system_prompt_from_env
from hosted_agents.metrics import observe_http_trigger
from hosted_agents.o11y_logging import configure_request_logging
from hosted_agents.o11y_middleware import ObservabilityMiddleware
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.skills_state import unlocked_tools
from hosted_agents.trigger_graph import (
    TriggerContext,
    TriggerHttpError,
    get_thread_checkpoint_history,
    get_thread_state_snapshot,
    run_trigger_graph,
)


async def _parse_trigger_json(request: Request) -> dict | None:
    body = await request.body()
    if not body:
        return None
    try:
        data = json.loads(body)
    except json.JSONDecodeError as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=400, detail="Trigger JSON body must be an object"
        )
    if "subagent" in data:
        raise HTTPException(
            status_code=400,
            detail=(
                "The 'subagent' field is no longer supported. "
                "Use 'message' for the root supervisor; configured specialists are tools "
                "of that agent (LangChain subagents pattern)."
            ),
        )
    return data


def _request_id(request: Request) -> str:
    rid = getattr(request.state, "request_id", None) or request.headers.get(
        "x-request-id"
    )
    return str(rid) if rid else str(uuid.uuid4())


def _resolve_thread_id(request: Request, payload: TriggerBody | None) -> str:
    if payload and payload.thread_id and str(payload.thread_id).strip():
        return str(payload.thread_id).strip()
    for key in ("x-thread-id", "X-Thread-Id"):
        if h := request.headers.get(key):
            s = str(h).strip()
            if s:
                return s
    return str(uuid.uuid4())


def _snapshot_to_dict(sn: object) -> dict:
    return {
        "values": getattr(sn, "values", {}),
        "next": list(getattr(sn, "next", ()) or ()),
        "metadata": getattr(sn, "metadata", None),
        "config": getattr(sn, "config", None),
        "created_at": getattr(sn, "created_at", None),
        "parent_config": getattr(sn, "parent_config", None),
    }


_CHECKPOINTS_DISABLED = (
    "Checkpoints are disabled (HOSTED_AGENT_CHECKPOINT_STORE=none). "
    "Set HOSTED_AGENT_CHECKPOINT_STORE=memory to enable state APIs."
)


def _require_checkpoints_enabled() -> None:
    if not checkpoints_globally_enabled():
        raise HTTPException(status_code=503, detail=_CHECKPOINTS_DISABLED)


def create_app(*, system_prompt: str | None = None) -> FastAPI:
    """Build the ASGI app.

    If ``system_prompt`` is set, it is used for every request (tests).
    Otherwise the value comes from :func:`system_prompt_from_env`.
    """
    configure_request_logging()
    app = FastAPI(title="config-first-hosted-agents", version="0.1.0")
    app.add_middleware(ObservabilityMiddleware)

    @app.get("/metrics")
    def get_metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/api/v1/trigger", response_class=PlainTextResponse)
    async def post_trigger(request: Request) -> str:
        start = time.perf_counter()
        raw = await _parse_trigger_json(request)
        payload = TriggerBody.model_validate(raw) if raw is not None else None
        prompt = (
            system_prompt if system_prompt is not None else system_prompt_from_env()
        )
        cfg = RuntimeConfig.from_env()
        ctx = TriggerContext(
            cfg=cfg,
            body=payload,
            system_prompt=prompt,
            request_id=_request_id(request),
            run_id=str(uuid.uuid4()),
            thread_id=_resolve_thread_id(request, payload),
            ephemeral=bool(payload.ephemeral) if payload else False,
        )

        try:
            out = run_trigger_graph(ctx)
        except ValueError as exc:
            observe_http_trigger("client_error", start)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TriggerHttpError as exc:
            if exc.status_code < 500:
                observe_http_trigger("client_error", start)
            else:
                observe_http_trigger("server_error", start)
            raise HTTPException(exc.status_code, exc.detail) from exc
        except Exception:
            observe_http_trigger("server_error", start)
            raise
        observe_http_trigger("success", start)
        return out

    @app.get("/api/v1/runtime/summary")
    def runtime_summary() -> JSONResponse:
        cfg = RuntimeConfig.from_env()
        return JSONResponse(
            {
                "rag_configured": bool(cfg.rag_base_url),
                "subagents": [s.get("name") for s in cfg.subagents if s.get("name")],
                "skills": [s.get("name") for s in cfg.skills if s.get("name")],
                "enabled_mcp_tools": list(cfg.enabled_mcp_tools),
                "skill_unlocked_tools": sorted(unlocked_tools()),
                "launch_path": "POST /api/v1/trigger",
                "orchestration": "langgraph",
                "observability": observability_summary(),
            },
        )

    @app.get("/api/v1/trigger/threads/{thread_id}/state")
    def get_trigger_thread_state(thread_id: str) -> JSONResponse:
        _require_checkpoints_enabled()
        snap = get_thread_state_snapshot(thread_id)
        return JSONResponse(_snapshot_to_dict(snap))

    @app.get("/api/v1/trigger/threads/{thread_id}/checkpoints")
    def get_trigger_thread_checkpoints(thread_id: str) -> JSONResponse:
        _require_checkpoints_enabled()
        hist = get_thread_checkpoint_history(thread_id)
        return JSONResponse([_snapshot_to_dict(s) for s in hist])

    @app.post("/api/v1/rag/query")
    def rag_query(request: Request, body: RagQueryBody) -> JSONResponse:
        cfg = RuntimeConfig.from_env()
        if not cfg.rag_base_url:
            raise HTTPException(
                status_code=503, detail="HOSTED_AGENT_RAG_BASE_URL is not set"
            )
        url = f"{cfg.rag_base_url.rstrip('/')}/v1/query"
        payload_json = body.model_dump(exclude_none=True)
        rid = _request_id(request)
        try:
            with httpx.Client(timeout=30.0, headers={"X-Request-Id": rid}) as client:
                resp = client.post(url, json=payload_json)
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            raise HTTPException(
                status_code=502, detail=f"rag request failed: {exc!s}"
            ) from exc
        return JSONResponse(resp.json())

    return app
