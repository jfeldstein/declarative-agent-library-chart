"""LangGraph pipeline for ``POST /api/v1/trigger`` (single external launch path)."""

from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from hosted_agents.agent_models import TriggerBody
from hosted_agents.checkpointing import (
    checkpoints_globally_enabled,
    compiled_graph_cache,
    resolve_checkpointer,
)
from hosted_agents.reply import trigger_reply_text
from hosted_agents.run_context import (
    TriggerRunIds,
    reset_tool_sequence,
    reset_trigger_ids,
    set_trigger_ids,
)
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.subagent_exec import _run_subagent_text as _run_subagent_text
from hosted_agents.supervisor import run_supervisor_agent
from hosted_agents.trigger_context import TriggerContext
from hosted_agents.trigger_errors import TriggerHttpError
from hosted_agents.trigger_steps import run_skill_load_json, run_tool_json
from hosted_agents.wandb_session import active_wandb_run_id, wandb_run_scope

_EMPTY_CFG = RuntimeConfig(
    rag_base_url="",
    subagents=[],
    skills=[],
    enabled_mcp_tools=[],
)

__all__ = [
    "TriggerHttpError",
    "TriggerContext",
    "compiled_trigger_graph_for_tests",
    "get_compiled_trigger_graph",
    "get_thread_checkpoint_history",
    "get_thread_state_snapshot",
    "run_trigger_graph",
    "_run_subagent_text",
]


class _GraphState(TypedDict, total=False):
    """Graph state; ``pre`` + ``pipeline`` nodes yield two checkpoints per invoke."""

    stage: str
    output: str
    trace_meta: dict[str, Any]


def _execute_trigger(ctx: TriggerContext) -> str:
    body = ctx.body or TriggerBody()

    if body.load_skill:
        skill_json = run_skill_load_json(ctx.cfg, body.load_skill)
        if not body.tool:
            if not ctx.cfg.subagents or body.message is None:
                return skill_json

    if body.tool:
        return run_tool_json(ctx.cfg, body.tool, body.tool_arguments)

    if ctx.cfg.subagents:
        user_message = (body.message or "").strip()
        return run_supervisor_agent(ctx, user_message)

    return trigger_reply_text(ctx.system_prompt)


def _pre(state: _GraphState, config: RunnableConfig) -> _GraphState:
    return {**state, "stage": "started"}


def _pipeline(state: _GraphState, config: RunnableConfig) -> _GraphState:
    ctx: TriggerContext = config["configurable"]["ctx"]
    out = _execute_trigger(ctx)
    meta: dict[str, Any] = {}
    if rid := active_wandb_run_id():
        meta["wandb_run_id"] = rid
    meta["run_id"] = ctx.run_id
    meta["thread_id"] = ctx.thread_id
    return {**state, "output": out, "stage": "done", "trace_meta": meta}


def _build_state_graph() -> StateGraph:
    g = StateGraph(_GraphState)
    g.add_node("pre", _pre)
    g.add_node("pipeline", _pipeline)
    g.add_edge(START, "pre")
    g.add_edge("pre", "pipeline")
    g.add_edge("pipeline", END)
    return g


def _uses_checkpointer(ctx: TriggerContext) -> bool:
    if ctx.ephemeral:
        return False
    return checkpoints_globally_enabled()


def _compiled_graph_for_mode(*, with_checkpointer: bool) -> Any:
    key = "with_checkpointer" if with_checkpointer else "no_checkpointer"
    cache = compiled_graph_cache()
    if key in cache:
        return cache[key]
    builder = _build_state_graph()
    if with_checkpointer:
        cp, _ = resolve_checkpointer()
        compiled = builder.compile(checkpointer=cp)
    else:
        compiled = builder.compile()
    cache[key] = compiled
    return compiled


def get_compiled_trigger_graph(ctx: TriggerContext) -> Any:
    """Return a compiled graph, with or without checkpointer (cached per mode)."""
    return _compiled_graph_for_mode(with_checkpointer=_uses_checkpointer(ctx))


def compiled_trigger_graph_for_tests(*, with_checkpointer: bool = True) -> Any:
    """Force-build one variant (used by tests that patch the graph)."""
    return _compiled_graph_for_mode(with_checkpointer=with_checkpointer)


def run_trigger_graph(ctx: TriggerContext) -> str:
    """Run the LangGraph pipeline once and return plain-text HTTP body."""
    reset_tool_sequence()
    tid_tok = set_trigger_ids(
        TriggerRunIds(
            run_id=ctx.run_id,
            thread_id=ctx.thread_id,
            request_id=ctx.request_id,
        ),
    )
    try:
        with wandb_run_scope(ctx):
            graph = get_compiled_trigger_graph(ctx)
            config: RunnableConfig = {"configurable": {"thread_id": ctx.thread_id, "ctx": ctx}}
            result = graph.invoke({"stage": "pending"}, config=config)
        return str(result.get("output", ""))
    finally:
        reset_trigger_ids(tid_tok)


def _thread_inspection_context(thread_id: str) -> TriggerContext:
    return TriggerContext(
        cfg=_EMPTY_CFG,
        body=None,
        system_prompt="",
        request_id="internal",
        run_id="internal",
        thread_id=thread_id,
        ephemeral=False,
    )


def get_thread_state_snapshot(thread_id: str) -> Any:
    """Latest :class:`langgraph.types.StateSnapshot` for ``thread_id`` (requires checkpointer graph)."""
    graph = get_compiled_trigger_graph(_thread_inspection_context(thread_id))
    cfg: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    return graph.get_state(cfg)


def get_thread_checkpoint_history(thread_id: str) -> list[Any]:
    graph = get_compiled_trigger_graph(_thread_inspection_context(thread_id))
    cfg: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    return list(graph.get_state_history(cfg))
