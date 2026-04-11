"""LangGraph subgraphs per configured subagent (invoked from supervisor tools)."""

from __future__ import annotations

from typing import Any

from langgraph.config import get_config
from langgraph.graph import END, START, StateGraph

from hosted_agents.agent_models import SubagentInvokeBody
from hosted_agents.subagent_exec import _run_subagent_text
from hosted_agents.trigger_context import TriggerContext


def compile_subagent_subgraph(entry: dict[str, Any]) -> Any:
    """Compile a one-node graph that runs :func:`hosted_agents.subagent_exec._run_subagent_text`."""

    name = str(entry.get("name") or "").strip()
    role = str(entry.get("role") or "default").strip().lower()

    def exec_node(state: dict[str, Any]) -> dict[str, Any]:
        config = get_config()
        ctx: TriggerContext = config["configurable"]["ctx"]
        cfg = ctx.cfg
        rid = ctx.request_id
        if role == "rag":
            rag_payload = SubagentInvokeBody(
                query=state.get("query"),
                scope=state.get("scope") or "default",
                top_k=int(state.get("top_k") or 5),
                expand_relationships=bool(state.get("expand_relationships", False)),
                relationship_types=state.get("relationship_types"),
                max_hops=int(state.get("max_hops") or 1),
            )
            text = _run_subagent_text(cfg, name, rag_payload, rid)
        elif role == "metrics":
            text = _run_subagent_text(cfg, name, None, rid)
        else:
            task = (state.get("task") or "").strip() or None
            text = _run_subagent_text(cfg, name, None, rid, default_task=task)
        return {"output": text}

    g = StateGraph(dict)
    g.add_node("exec", exec_node)
    g.add_edge(START, "exec")
    g.add_edge("exec", END)
    return g.compile()
