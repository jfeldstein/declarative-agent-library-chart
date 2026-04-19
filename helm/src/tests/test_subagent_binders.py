"""Pinned LangChain shapes for subagent tools + direct ``_run_subagent_text`` wiring."""

from __future__ import annotations

import pytest
from langchain.tools import ToolRuntime

from agent.agent_models import SubagentInvokeBody, TriggerBody
from agent.runtime_config import RuntimeConfig
from agent.supervisor import _build_subagent_tool
from agent.trigger_context import TriggerContext


def _ctx(*, subagents: list[dict]) -> TriggerContext:
    cfg = RuntimeConfig(
        rag_base_url="http://rag",
        subagents=subagents,
        skills=[],
        enabled_mcp_tools=[],
    )
    return TriggerContext(
        cfg=cfg,
        body=TriggerBody(message="m"),
        system_prompt="s",
        request_id="rid-1",
        run_id="run",
        thread_id="thr",
        observability=None,
    )


def test_rag_tool_params_exact() -> None:
    entry = {"name": "raggy", "role": "rag", "description": "d"}
    tool_obj = _build_subagent_tool(entry)
    schema = getattr(tool_obj, "args_schema", None)
    assert schema is not None
    fields = getattr(schema, "model_fields", {})
    # LangChain injects ToolRuntime separately; it may appear in the generated schema model.
    public = set(fields.keys()) - {"runtime"}
    assert public == {
        "query",
        "scope",
        "top_k",
        "expand_relationships",
        "relationship_types",
        "max_hops",
    }


def test_metrics_tool_params_exact() -> None:
    entry = {
        "name": "metrics",
        "role": "metrics",
        "exposeAsTool": True,
        "description": "m",
    }
    tool_obj = _build_subagent_tool(entry)
    schema = getattr(tool_obj, "args_schema", None)
    assert schema is None or not (
        set(getattr(schema, "model_fields", {}).keys()) - {"runtime"}
    )


def test_default_tool_params_exact() -> None:
    entry = {"name": "helper", "role": "default", "description": "d"}
    tool_obj = _build_subagent_tool(entry)
    schema = getattr(tool_obj, "args_schema", None)
    assert schema is not None
    fields = getattr(schema, "model_fields", {})
    public = set(fields.keys()) - {"runtime"}
    assert public == {"task"}


def test_subagent_tool_calls_run_subagent_text(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[tuple] = []

    def fake(cfg: RuntimeConfig, name: str, rag: SubagentInvokeBody | None, rid: str):
        calls.append((cfg, name, rag, rid))
        return "ok"

    monkeypatch.setattr(
        "agent.supervisor._run_subagent_text",
        fake,
    )
    entry = {
        "name": "metrics",
        "role": "metrics",
        "exposeAsTool": True,
        "description": "x",
    }
    tool_obj = _build_subagent_tool(entry)
    ctx = _ctx(subagents=[entry])
    rt = ToolRuntime(
        state={},
        context=ctx,
        config={},
        stream_writer=lambda *_: None,
        tool_call_id=None,
        store=None,
    )
    out = tool_obj.invoke({"runtime": rt})
    assert out == "ok"
    assert len(calls) == 1
    cfg, name, rag, rid = calls[0]
    assert name == "metrics"
    assert rag is None
    assert rid == "rid-1"
    assert cfg is ctx.cfg
