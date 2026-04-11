"""LangGraph pipeline for ``POST /api/v1/trigger`` (single external launch path)."""

from __future__ import annotations

from typing import Any, TypedDict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from hosted_agents.agent_models import TriggerBody
from hosted_agents.reply import trigger_reply_text
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
    "run_trigger_graph",
    "_run_subagent_text",
]


class _GraphState(TypedDict):
    output: str


def _execute_trigger(ctx: TriggerContext) -> str:
    body = ctx.body or TriggerBody()

    if body.load_skill:
        skill_json = run_skill_load_json(ctx.cfg, body.load_skill)
        if not body.tool:
            # Without ``message``, keep the progressive-disclosure short-circuit (skills).
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
