"""Supervisor agent (``create_agent``) + subagent/MCP LangChain tools.

[DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-002] MCP tools bind via ``_bind`` → ``run_tool_json`` → ``invoke_tool``.
"""

from __future__ import annotations

import re
from typing import Any

from langchain.agents import create_agent
from langchain.messages import AIMessage, HumanMessage
from langchain.tools import ToolRuntime, tool

from agent.agent_models import SubagentInvokeBody
from agent.chat_model import resolve_chat_model
from agent.llm_metrics import SupervisorLlmMetricsCallback
from agent.skills_state import unlocked_tools
from agent.subagent_exec import _run_subagent_text
from agent.tools.contract import ToolSpec
from agent.tools.registry import load_registry, sanitize_tool_name
from agent.trigger_context import TriggerContext
from agent.trigger_errors import TriggerHttpError
from agent.trigger_steps import run_tool_json


def _sanitize_tool_name_fragment(raw: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9_]+", "_", raw.strip()).strip("_")
    return s or "subagent"


def subagent_exposed_as_tool(entry: dict[str, Any]) -> bool:
    """``role: metrics`` is hidden unless ``exposeAsTool`` is explicitly true."""

    role = str(entry.get("role") or "default").strip().lower()
    raw = entry.get("exposeAsTool")
    if raw is not None:
        return bool(raw)
    return role != "metrics"


def subagent_tool_description(entry: dict[str, Any]) -> str:
    for key in ("description", "toolDescription", "tool_description"):
        d = entry.get(key)
        if isinstance(d, str) and d.strip():
            return d.strip()
    name = str(entry.get("name") or "subagent")
    role = str(entry.get("role") or "default")
    return (
        f"Specialist `{name}` ({role} role). "
        "Invoke when the user needs this specialist's behavior."
    )


def subagent_tools_appendix(cfg_subagents: list[dict[str, Any]]) -> str:
    """Enumerate configured tools for the supervisor system prompt (LangChain subagents guidance)."""

    lines: list[str] = []
    for entry in cfg_subagents:
        name = str(entry.get("name") or "").strip()
        if not name or not subagent_exposed_as_tool(entry):
            continue
        desc = subagent_tool_description(entry)
        lines.append(f"- **{name}**: {desc}")
    return "\n".join(lines)


def build_supervisor_system_prompt(ctx: TriggerContext) -> str:
    base = ctx.system_prompt.strip()
    appendix = subagent_tools_appendix(ctx.cfg.subagents)
    if appendix:
        return (
            f"{base}\n\n"
            "## Available specialists (tools)\n"
            "You may call the following tools when delegation helps. "
            "Tool schemas include names and parameters.\n\n"
            f"{appendix}\n"
        )
    return base


def _bind(spec: ToolSpec) -> Any:
    @tool(
        sanitize_tool_name(spec.id),
        description=spec.description,
        args_schema=spec.args_schema,
    )
    def _run(runtime: ToolRuntime[TriggerContext], **kwargs: Any) -> str:
        return run_tool_json(runtime.context.cfg, spec.id, kwargs)

    return _run


def _build_subagent_tool(entry: dict[str, Any]) -> Any:
    role = str(entry.get("role") or "default").strip().lower()
    name = str(entry.get("name") or "").strip()
    safe = _sanitize_tool_name_fragment(name)
    tool_id = f"subagent_{safe}"
    description = subagent_tool_description(entry)

    if role == "rag":

        @tool(tool_id, description=description)
        def _rag_tool(
            query: str,
            runtime: ToolRuntime[TriggerContext],
            scope: str = "default",
            top_k: int = 5,
            expand_relationships: bool = False,
            relationship_types: list[str] | None = None,
            max_hops: int = 1,
        ) -> str:
            rag_payload = SubagentInvokeBody(
                query=query,
                scope=scope,
                top_k=top_k,
                expand_relationships=expand_relationships,
                relationship_types=relationship_types,
                max_hops=max_hops,
            )
            return _run_subagent_text(
                runtime.context.cfg,
                name,
                rag_payload,
                runtime.context.request_id,
            )

        return _rag_tool

    if role == "metrics":

        @tool(tool_id, description=description)
        def _metrics_tool(runtime: ToolRuntime[TriggerContext]) -> str:
            return _run_subagent_text(
                runtime.context.cfg,
                name,
                None,
                runtime.context.request_id,
            )

        return _metrics_tool

    @tool(tool_id, description=description)
    def _default_tool(task: str, runtime: ToolRuntime[TriggerContext]) -> str:
        return _run_subagent_text(
            runtime.context.cfg,
            name,
            None,
            runtime.context.request_id,
            default_task=task,
        )

    return _default_tool


def build_supervisor_tools(ctx: TriggerContext) -> list[Any]:
    """Merge order: **subagent tools** (config order), then **MCP** tools (sorted by id)."""

    tools: list[Any] = []
    for entry in ctx.cfg.subagents:
        name = str(entry.get("name") or "").strip()
        if not name or not subagent_exposed_as_tool(entry):
            continue
        tools.append(_build_subagent_tool(entry))
    allowed = set(ctx.cfg.enabled_mcp_tools) | set(unlocked_tools())
    reg = load_registry()
    tools.extend(_bind(reg[tid]) for tid in sorted(allowed & reg.keys()))
    return tools


def extract_final_ai_text(result: dict[str, Any]) -> str:
    messages = result.get("messages") or []
    if not messages:
        return ""
    last = messages[-1]
    if isinstance(last, AIMessage):
        content = last.content
        if isinstance(content, str):
            return content
        return str(content)
    return str(getattr(last, "content", last))


def run_supervisor_agent(ctx: TriggerContext, user_message: str) -> str:
    try:
        model = resolve_chat_model()
    except ValueError as exc:
        raise TriggerHttpError(503, str(exc)) from exc
    tools = build_supervisor_tools(ctx)
    system_prompt = build_supervisor_system_prompt(ctx)
    agent = create_agent(
        model,
        tools=tools,
        system_prompt=system_prompt,
        context_schema=TriggerContext,
    )
    llm_cb = SupervisorLlmMetricsCallback(ctx)
    result = agent.invoke(
        {"messages": [HumanMessage(content=user_message)]},
        context=ctx,
        config={"callbacks": [llm_cb]},
    )
    return extract_final_ai_text(result)
