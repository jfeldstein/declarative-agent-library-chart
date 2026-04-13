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
from hosted_agents.observability.atif import export_atif_batch
from hosted_agents.observability.feedback import feedback_store
from hosted_agents.observability.settings import ObservabilitySettings
from hosted_agents.observability.side_effects import side_effect_checkpoints
from hosted_agents.observability.slack_ingest import handle_slack_reaction_event
from hosted_agents.observability.trajectory import trajectory_recorder
from hosted_agents.o11y_logging import configure_request_logging
from hosted_agents.o11y_middleware import ObservabilityMiddleware
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.skills_state import unlocked_tools
from hosted_agents.trigger_graph import (
    TriggerContext,
    TriggerHttpError,
    get_thread_checkpoint_history,
    get_thread_state,
    get_thread_state_history,
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
    for key in (
        "x-thread-id",
        "X-Thread-Id",
        "x-agent-thread-id",
        "X-Agent-Thread-Id",
    ):
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
        obs = ObservabilitySettings.from_env()
        run_id = str(uuid.uuid4())
        req_id = _request_id(request)
        ephemeral = bool(payload.ephemeral) if payload is not None else False
        thread_id = _resolve_thread_id(request, payload)
        tenant_hdr = (request.headers.get("x-tenant-id") or "").strip()
        ctx = TriggerContext(
            cfg=cfg,
            body=payload,
            system_prompt=prompt,
            request_id=req_id,
            run_id=run_id,
            thread_id=thread_id,
            ephemeral=ephemeral,
            tenant_id=tenant_hdr or None,
            observability=obs,
        )

        try:
            out = run_trigger_graph(ctx)
        except ValueError as exc:
            observe_http_trigger("client_error", start)
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except TriggerHttpError as exc:
            observe_http_trigger(
                "client_error" if exc.status_code < 500 else "server_error",
                start,
            )
            raise HTTPException(exc.status_code, exc.detail) from exc
        except Exception:
            observe_http_trigger("server_error", start)
            raise
        observe_http_trigger("success", start)
        return out

    @app.get("/api/v1/runtime/summary")
    def runtime_summary() -> JSONResponse:
        cfg = RuntimeConfig.from_env()
        obs = ObservabilitySettings.from_env()
        obs_payload: dict[str, object] = dict(observability_summary())
        obs_payload.update(
            {
                "checkpoints_enabled": obs.checkpoints_enabled,
                "checkpoint_backend": obs.checkpoint_backend,
                "wandb_enabled": obs.wandb_enabled,
                "slack_feedback_enabled": obs.slack_feedback_enabled,
                "atif_export_enabled": obs.atif_export_enabled,
                "shadow_enabled": obs.shadow_enabled,
            },
        )
        return JSONResponse(
            {
                "rag_configured": bool(cfg.rag_base_url),
                "subagents": [s.get("name") for s in cfg.subagents if s.get("name")],
                "skills": [s.get("name") for s in cfg.skills if s.get("name")],
                "enabled_mcp_tools": list(cfg.enabled_mcp_tools),
                "skill_unlocked_tools": sorted(unlocked_tools()),
                "launch_path": "POST /api/v1/trigger",
                "orchestration": "langgraph",
                "observability": obs_payload,
            },
        )

    @app.get("/api/v1/runtime/threads/{thread_id}/state")
    def thread_state(thread_id: str) -> JSONResponse:
        try:
            snap = get_thread_state(thread_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        values = getattr(snap, "values", {}) or {}
        nxt = getattr(snap, "next", ()) or ()
        cfg = getattr(snap, "config", {}) or {}
        return JSONResponse(
            {
                "thread_id": thread_id,
                "values": values,
                "next": list(nxt) if not isinstance(nxt, list) else nxt,
                "config": cfg,
            }
        )

    @app.get("/api/v1/runtime/threads/{thread_id}/checkpoints")
    def thread_checkpoints(thread_id: str) -> JSONResponse:
        try:
            hist = get_thread_state_history(thread_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        out: list[dict] = []
        for h in hist:
            out.append(
                {
                    "values": getattr(h, "values", {}) or {},
                    "config": getattr(h, "config", {}) or {},
                    "metadata": getattr(h, "metadata", {}) or {},
                }
            )
        return JSONResponse({"thread_id": thread_id, "checkpoints": out})

    @app.get("/api/v1/runtime/threads/{thread_id}/side-effects")
    def thread_side_effects(thread_id: str) -> JSONResponse:
        recs = side_effect_checkpoints.by_thread(thread_id)
        return JSONResponse(
            {
                "thread_id": thread_id,
                "side_effects": [
                    {
                        "checkpoint_id": r.checkpoint_id,
                        "run_id": r.run_id,
                        "tool_call_id": r.tool_call_id,
                        "tool_name": r.tool_name,
                        "external_ref": r.external_ref,
                        "created_at": r.created_at,
                    }
                    for r in recs
                ],
            }
        )

    @app.post("/api/v1/integrations/slack/reactions")
    async def slack_reactions(request: Request) -> JSONResponse:
        obs = ObservabilitySettings.from_env()
        try:
            raw = await request.json()
        except json.JSONDecodeError as exc:
            raise HTTPException(status_code=400, detail="Invalid JSON body") from exc
        if not isinstance(raw, dict):
            raise HTTPException(status_code=400, detail="JSON body must be an object")
        result = handle_slack_reaction_event(raw, settings=obs)
        return JSONResponse(result)

    @app.get("/api/v1/runtime/feedback/human")
    def list_human_feedback() -> JSONResponse:
        evs = feedback_store.human_events()
        return JSONResponse(
            {
                "events": [
                    {
                        "registry_id": e.registry_id,
                        "schema_version": e.schema_version,
                        "label_id": e.label_id,
                        "tool_call_id": e.tool_call_id,
                        "checkpoint_id": e.checkpoint_id,
                        "run_id": e.run_id,
                        "thread_id": e.thread_id,
                        "feedback_source": e.feedback_source,
                        "agent_id": e.agent_id,
                    }
                    for e in evs
                ]
            }
        )

    @app.get("/api/v1/runtime/exports/atif")
    def export_atif(run_id: str) -> JSONResponse:
        obs = ObservabilitySettings.from_env()
        if not obs.atif_export_enabled:
            raise HTTPException(status_code=503, detail="ATIF export is disabled")
        if not run_id.strip():
            raise HTTPException(status_code=400, detail="run_id is required")
        tr = trajectory_recorder.get(run_id.strip())
        if tr is None:
            raise HTTPException(status_code=404, detail="run_id not found")
        docs = export_atif_batch([tr])
        return JSONResponse({"documents": docs})

    @app.get("/api/v1/trigger/threads/{thread_id}/state")
    def get_trigger_thread_state(thread_id: str) -> JSONResponse:
        _require_checkpoints_enabled()
        try:
            snap = get_thread_state_snapshot(thread_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
        return JSONResponse(_snapshot_to_dict(snap))

    @app.get("/api/v1/trigger/threads/{thread_id}/checkpoints")
    def get_trigger_thread_checkpoints(thread_id: str) -> JSONResponse:
        _require_checkpoints_enabled()
        try:
            hist = get_thread_checkpoint_history(thread_id)
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
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
