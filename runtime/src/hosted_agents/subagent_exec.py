"""Execute configured subagent roles (metrics, rag, default)."""

from __future__ import annotations

import time
import httpx
from prometheus_client import generate_latest

from hosted_agents.agent_models import SubagentInvokeBody
from hosted_agents.metrics import observe_subagent
from hosted_agents.reply import trigger_reply_text
from hosted_agents.runtime_config import RuntimeConfig, subagent_system_prompt
from hosted_agents.trigger_errors import TriggerHttpError


def _httpx_headers(request_id: str) -> dict[str, str]:
    return {"X-Request-Id": request_id}


def _run_subagent_text(
    cfg: RuntimeConfig,
    name: str,
    rag_payload: SubagentInvokeBody | None,
    request_id: str,
    *,
    default_task: str | None = None,
) -> str:
    start = time.perf_counter()
    entry = next((s for s in cfg.subagents if str(s.get("name")) == name), None)
    if entry is None:
        observe_subagent(name, "error", start)
        raise TriggerHttpError(404, "subagent not found")

    role = str(entry.get("role") or "default").strip().lower()

    if role == "metrics":
        observe_subagent(name, "success", start)
        return generate_latest().decode("utf-8")

    if role == "rag":
        if not cfg.rag_base_url:
            observe_subagent(name, "error", start)
            raise TriggerHttpError(503, "HOSTED_AGENT_RAG_BASE_URL is not set")
        rb = rag_payload or SubagentInvokeBody()
        q = (rb.query or "").strip()
        if not q:
            observe_subagent(name, "error", start)
            raise TriggerHttpError(
                400,
                "non-empty 'query' argument is required for rag role",
            )
        url = f"{cfg.rag_base_url.rstrip('/')}/v1/query"
        req_json = rb.model_dump(exclude_none=True)
        req_json["query"] = q
        try:
            with httpx.Client(
                timeout=30.0,
                headers=_httpx_headers(request_id),
            ) as client:
                resp = client.post(url, json=req_json)
                resp.raise_for_status()
        except httpx.HTTPError as exc:
            observe_subagent(name, "error", start)
            msg = f"rag subagent request failed: {exc!s}"
            raise TriggerHttpError(502, msg) from exc
        observe_subagent(name, "success", start)
        return resp.text

    prompt = subagent_system_prompt(entry)
    if default_task and default_task.strip():
        prompt = f"{prompt}\n\nUser task:\n{default_task.strip()}"
    if not prompt.strip():
        observe_subagent(name, "error", start)
        raise TriggerHttpError(400, "subagent has empty system prompt")
    try:
        out = trigger_reply_text(prompt)
    except ValueError as exc:
        observe_subagent(name, "error", start)
        raise TriggerHttpError(400, str(exc)) from exc
    observe_subagent(name, "success", start)
    return out
