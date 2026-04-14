"""LangGraph pipeline for ``POST /api/v1/trigger`` (single external launch path)."""

from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from hosted_agents.agent_models import TriggerBody
from hosted_agents.checkpointing import (
    checkpoints_globally_enabled,
    effective_checkpoint_store,
    resolve_checkpointer,
)
from hosted_agents.observability.checkpointer import build_checkpointer
from hosted_agents.observability.run_context import (
    bind_run_context,
    get_run_id,
    set_wandb_session,
)
from hosted_agents.observability.settings import ObservabilitySettings
from hosted_agents.observability.trajectory import trajectory_recorder
from hosted_agents.observability.wandb_trace import WandbTraceSession
from hosted_agents.reply import trigger_reply_text
from hosted_agents.run_context import (
    TriggerRunIds,
    reset_tool_sequence,
    reset_trigger_ids,
    set_trigger_ids,
)
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.supervisor import run_supervisor_agent
from hosted_agents.trigger_context import TriggerContext
from hosted_agents.trigger_errors import TriggerHttpError
from hosted_agents.trigger_steps import run_skill_load_json, run_tool_json

# Re-export for tests / scripts that patch subagent execution.
from hosted_agents.subagent_exec import _run_subagent_text as _run_subagent_text

__all__ = [
    "TriggerHttpError",
    "TriggerContext",
    "compiled_trigger_graph",
    "compiled_trigger_graph_for_tests",
    "get_compiled_trigger_graph",
    "get_thread_checkpoint_history",
    "get_thread_state",
    "get_thread_state_history",
    "get_thread_state_snapshot",
    "run_trigger_graph",
    "_run_subagent_text",
]


class _GraphState(TypedDict, total=False):
    output: str
    skill_json: str
    stage: str


def _obs(ctx: TriggerContext) -> ObservabilitySettings:
    return ctx.observability or ObservabilitySettings.from_env()


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


def _pipeline(state: _GraphState, config: RunnableConfig) -> _GraphState:
    ctx: TriggerContext = config["configurable"]["ctx"]
    out = _execute_trigger(ctx)
    rid = get_run_id()
    if rid:
        trajectory_recorder.append(rid, "pipeline", {"stage": "single"})
    return {"output": out, "stage": "done"}


def _node_load_skill(state: _GraphState, config: RunnableConfig) -> _GraphState:
    ctx: TriggerContext = config["configurable"]["ctx"]
    body = ctx.body or TriggerBody()
    if not body.load_skill:
        return {}
    sj = run_skill_load_json(ctx.cfg, body.load_skill)
    rid = get_run_id()
    if rid:
        trajectory_recorder.append(
            rid, "load_skill", {"skill": body.load_skill, "preview_chars": len(sj)}
        )
    return {"skill_json": sj}


def _route_after_load(state: _GraphState, config: RunnableConfig) -> str:
    ctx: TriggerContext = config["configurable"]["ctx"]
    body = ctx.body or TriggerBody()
    if body.tool:
        return "tool"
    skill_json = state.get("skill_json")
    if skill_json is not None:
        if not ctx.cfg.subagents or body.message is None:
            return "emit_skill"
    if ctx.cfg.subagents:
        return "supervisor"
    return "reply"


def _node_emit_skill(state: _GraphState, config: RunnableConfig) -> _GraphState:
    sj = state.get("skill_json") or ""
    rid = get_run_id()
    if rid:
        trajectory_recorder.append(rid, "emit_skill_json", {})
    return {"output": sj, "stage": "done"}


def _node_tool(state: _GraphState, config: RunnableConfig) -> _GraphState:
    ctx: TriggerContext = config["configurable"]["ctx"]
    body = ctx.body or TriggerBody()
    assert body.tool
    out = run_tool_json(ctx.cfg, body.tool, body.tool_arguments)
    return {"output": out, "stage": "done"}


def _node_supervisor(state: _GraphState, config: RunnableConfig) -> _GraphState:
    ctx: TriggerContext = config["configurable"]["ctx"]
    body = ctx.body or TriggerBody()
    user_message = (body.message or "").strip()
    out = run_supervisor_agent(ctx, user_message)
    rid = get_run_id()
    if rid:
        trajectory_recorder.append(rid, "supervisor", {"chars": len(out)})
    return {"output": out, "stage": "done"}


def _node_reply(state: _GraphState, config: RunnableConfig) -> _GraphState:
    ctx: TriggerContext = config["configurable"]["ctx"]
    out = trigger_reply_text(ctx.system_prompt)
    rid = get_run_id()
    if rid:
        trajectory_recorder.append(rid, "reply", {"chars": len(out)})
    return {"output": out, "stage": "done"}


_compiled_graph: Any | None = None
_compiled_graph_key: tuple[Any, ...] | None = None


def _graph_key(ctx: TriggerContext) -> tuple[Any, ...]:
    obs = _obs(ctx)
    use_cp = checkpoints_globally_enabled() and not ctx.ephemeral
    store_kind = effective_checkpoint_store()
    backend = obs.checkpoint_backend if obs.checkpoints_enabled else store_kind
    return (use_cp, obs.checkpoints_enabled, backend, ctx.ephemeral)


def _resolve_checkpointer(
    ctx: TriggerContext, obs: ObservabilitySettings
) -> Any | None:
    if not checkpoints_globally_enabled() or ctx.ephemeral:
        return None
    if obs.checkpoints_enabled:
        return build_checkpointer(obs)
    cp, _ = resolve_checkpointer()
    return cp


def compiled_trigger_graph(ctx: TriggerContext) -> Any:
    """Return a compiled graph for this checkpointing mode (cached)."""

    global _compiled_graph, _compiled_graph_key
    key = _graph_key(ctx)
    if _compiled_graph is not None and _compiled_graph_key == key:
        return _compiled_graph

    obs = _obs(ctx)
    checkpointer = _resolve_checkpointer(ctx, obs)
    use_checkpointing = checkpointer is not None

    if not use_checkpointing:
        g = StateGraph(_GraphState)
        g.add_node("pipeline", _pipeline)
        g.add_edge(START, "pipeline")
        g.add_edge("pipeline", END)
        _compiled_graph = g.compile()
    else:
        g = StateGraph(_GraphState)
        g.add_node("load_skill", _node_load_skill)
        g.add_node("emit_skill", _node_emit_skill)
        g.add_node("tool", _node_tool)
        g.add_node("supervisor", _node_supervisor)
        g.add_node("reply", _node_reply)
        g.add_edge(START, "load_skill")
        g.add_conditional_edges(
            "load_skill",
            _route_after_load,
            {
                "tool": "tool",
                "emit_skill": "emit_skill",
                "supervisor": "supervisor",
                "reply": "reply",
            },
        )
        g.add_edge("emit_skill", END)
        g.add_edge("tool", END)
        g.add_edge("supervisor", END)
        g.add_edge("reply", END)
        _compiled_graph = g.compile(checkpointer=checkpointer)

    _compiled_graph_key = key
    return _compiled_graph


def get_compiled_trigger_graph(ctx: TriggerContext) -> Any:
    """Return a compiled graph, with or without checkpointer (cached per mode)."""
    return compiled_trigger_graph(ctx)


def compiled_trigger_graph_for_tests(*, with_checkpointer: bool = True) -> Any:
    """Force-build one variant (used by tests that patch the graph)."""
    ctx = trigger_context_for_admin_reads()
    if not with_checkpointer:
        return compiled_trigger_graph(
            TriggerContext(
                cfg=ctx.cfg,
                body=ctx.body,
                system_prompt=ctx.system_prompt,
                request_id=ctx.request_id,
                run_id=ctx.run_id,
                thread_id=ctx.thread_id,
                ephemeral=True,
                tenant_id=ctx.tenant_id,
                observability=ctx.observability,
            )
        )
    return compiled_trigger_graph(ctx)


def run_trigger_graph(ctx: TriggerContext) -> str:
    """Run the compiled LangGraph once and return plain-text HTTP body."""
    obs = _obs(ctx)
    reset_tool_sequence()
    tid_tok = set_trigger_ids(
        TriggerRunIds(
            run_id=ctx.run_id,
            thread_id=ctx.thread_id,
            request_id=ctx.request_id,
        ),
    )
    bind_run_context(
        run_id=ctx.run_id,
        thread_id=ctx.thread_id,
        request_correlation_id=ctx.request_id,
    )
    trajectory_recorder.start(ctx.run_id, ctx.thread_id)

    tags = WandbTraceSession.mandatory_tags(
        agent_id=None,
        environment=None,
        skill_id=None,
        skill_version=None,
        model_id=None,
        prompt_hash=None,
        rollout_arm="primary",
        thread_id=ctx.thread_id,
        request_correlation_id=ctx.request_id,
    )
    wandb_session = WandbTraceSession(settings=obs, run_name=ctx.run_id, tags=tags)
    set_wandb_session(wandb_session if obs.wandb_enabled else None)

    graph = compiled_trigger_graph(ctx)
    thread_cfg: dict[str, Any] = {
        "configurable": {"ctx": ctx, "thread_id": ctx.thread_id}
    }
    try:
        result = graph.invoke({"output": ""}, config=thread_cfg)
    finally:
        set_wandb_session(None)
        wandb_session.finish()
        reset_trigger_ids(tid_tok)

    assert isinstance(result, dict)
    return str(result["output"])


def trigger_context_for_admin_reads() -> TriggerContext:
    """Minimal :class:`TriggerContext` for checkpoint read APIs (operator tooling)."""

    return TriggerContext(
        cfg=RuntimeConfig.from_env(),
        body=None,
        system_prompt="-",
        request_id="admin-read",
        run_id="admin-read",
        thread_id="admin-read",
        ephemeral=False,
        tenant_id=None,
        observability=ObservabilitySettings.from_env(),
    )


def thread_read_config(thread_id: str) -> dict[str, Any]:
    """Build LangGraph read config for ``get_state`` / ``get_state_history``."""

    return {"configurable": {"thread_id": thread_id}}


def get_thread_state(
    thread_id: str,
    *,
    ctx_template: TriggerContext | None = None,
    require_operator_checkpoint_flag: bool = True,
) -> Any:
    """Latest checkpoint snapshot for ``thread_id`` (requires checkpointing enabled)."""

    ctx = ctx_template or trigger_context_for_admin_reads()
    obs = _obs(ctx)
    if require_operator_checkpoint_flag and not obs.checkpoints_enabled:
        msg = "checkpointing is disabled"
        raise RuntimeError(msg)
    if not checkpoints_globally_enabled():
        msg = "checkpointing is disabled"
        raise RuntimeError(msg)
    graph = compiled_trigger_graph(ctx)
    return graph.get_state(thread_read_config(thread_id))


def get_thread_state_history(
    thread_id: str,
    *,
    ctx_template: TriggerContext | None = None,
    require_operator_checkpoint_flag: bool = True,
) -> list[Any]:
    ctx = ctx_template or trigger_context_for_admin_reads()
    obs = _obs(ctx)
    if require_operator_checkpoint_flag and not obs.checkpoints_enabled:
        msg = "checkpointing is disabled"
        raise RuntimeError(msg)
    if not checkpoints_globally_enabled():
        msg = "checkpointing is disabled"
        raise RuntimeError(msg)
    graph = compiled_trigger_graph(ctx)
    return list(graph.get_state_history(thread_read_config(thread_id)))


def get_thread_state_snapshot(thread_id: str) -> Any:
    """Latest snapshot for ``thread_id`` (``HOSTED_AGENT_CHECKPOINT_STORE`` gate only)."""
    return get_thread_state(thread_id, require_operator_checkpoint_flag=False)


def get_thread_checkpoint_history(thread_id: str) -> list[Any]:
    """Checkpoint history for ``thread_id`` (``HOSTED_AGENT_CHECKPOINT_STORE`` gate only)."""
    return get_thread_state_history(thread_id, require_operator_checkpoint_flag=False)
