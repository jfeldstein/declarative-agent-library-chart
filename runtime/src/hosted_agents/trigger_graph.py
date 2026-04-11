"""LangGraph pipeline for ``POST /api/v1/trigger`` (single external launch path)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any, TypedDict

import httpx
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from prometheus_client import generate_latest

from hosted_agents.agent_models import SubagentInvokeBody, TriggerBody
from hosted_agents.metrics import (
    observe_mcp_tool,
    observe_skill_load,
    observe_subagent,
)
from hosted_agents.reply import trigger_reply_text
from hosted_agents.runtime_config import RuntimeConfig, subagent_system_prompt
from hosted_agents.skills_state import unlock_tools, unlocked_tools
from hosted_agents.tools_impl.dispatch import invoke_tool


class TriggerHttpError(Exception):
    """Maps to a non-200 HTTP response from the FastAPI layer."""

    def __init__(self, status_code: int, detail: str) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(detail)


@dataclass(frozen=True)
class TriggerContext:
    cfg: RuntimeConfig
    body: TriggerBody | None
    system_prompt: str
    request_id: str


class _GraphState(TypedDict):
    output: str


def _rag_payload(body: TriggerBody) -> SubagentInvokeBody:
    return SubagentInvokeBody(
        query=body.query,
        scope=body.scope,
        top_k=body.top_k,
        expand_relationships=body.expand_relationships,
        relationship_types=body.relationship_types,
        max_hops=body.max_hops,
    )


def _httpx_headers(request_id: str) -> dict[str, str]:
    return {"X-Request-Id": request_id}


def _run_subagent_text(
    cfg: RuntimeConfig,
    name: str,
    rag_payload: SubagentInvokeBody | None,
    request_id: str,
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
                "JSON body with non-empty 'query' is required for rag role",
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


def _run_skill_load_json(cfg: RuntimeConfig, name: str) -> str:
    start = time.perf_counter()
    entry = next((s for s in cfg.skills if str(s.get("name")) == name), None)
    if entry is None:
        observe_skill_load(name, "error", start)
        raise TriggerHttpError(404, "skill not found")
    raw_extra = entry.get("extraTools") or entry.get("extra_tools") or []
    extra = [str(x) for x in raw_extra] if isinstance(raw_extra, list) else []
    unlock_tools(extra)
    prompt = str(entry.get("prompt") or "")
    observe_skill_load(name, "success", start)
    return json.dumps({"name": name, "prompt": prompt, "activated_tools": extra})


def _run_tool_json(cfg: RuntimeConfig, tool: str, arguments: dict[str, Any]) -> str:
    start = time.perf_counter()
    allowed = set(cfg.enabled_mcp_tools) | set(unlocked_tools())
    if tool not in allowed:
        observe_mcp_tool(tool, "error", start)
        raise TriggerHttpError(403, "tool is not enabled for this deployment")
    try:
        result = invoke_tool(tool, arguments)
    except KeyError as exc:
        observe_mcp_tool(tool, "error", start)
        raise TriggerHttpError(404, str(exc)) from exc
    observe_mcp_tool(tool, "success", start)
    return json.dumps({"tool": tool, "result": result})


def _execute_trigger(ctx: TriggerContext) -> str:
    cfg = ctx.cfg
    body = ctx.body or TriggerBody()
    request_id = ctx.request_id

    if body.load_skill:
        skill_json = _run_skill_load_json(cfg, body.load_skill)
        if not body.subagent and not body.tool:
            return skill_json

    if body.subagent:
        # Non-``rag`` roles ignore ``rag_payload``; ``rag`` uses these fields from the trigger body.
        return _run_subagent_text(
            cfg,
            body.subagent,
            _rag_payload(body),
            request_id,
        )

    if body.tool:
        return _run_tool_json(cfg, body.tool, body.tool_arguments)

    return trigger_reply_text(ctx.system_prompt)


def _pipeline(state: _GraphState, config: RunnableConfig) -> _GraphState:
    ctx: TriggerContext = config["configurable"]["ctx"]
    out = _execute_trigger(ctx)
    return {"output": out}


_compiled_graph: Any | None = None


def compiled_trigger_graph() -> Any:
    global _compiled_graph
    if _compiled_graph is None:
        g = StateGraph(_GraphState)
        g.add_node("pipeline", _pipeline)
        g.add_edge(START, "pipeline")
        g.add_edge("pipeline", END)
        _compiled_graph = g.compile()
    return _compiled_graph


def run_trigger_graph(ctx: TriggerContext) -> str:
    """Run the compiled LangGraph once and return plain-text HTTP body."""
    graph = compiled_trigger_graph()
    result = graph.invoke({"output": ""}, config={"configurable": {"ctx": ctx}})
    return str(result["output"])
