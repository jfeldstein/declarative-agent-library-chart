"""Supervisor MCP tool binding invariants."""

from __future__ import annotations

import pytest
from langchain.tools import ToolRuntime
from pydantic import BaseModel

from agent.agent_models import TriggerBody
from agent.runtime_config import RuntimeConfig
from agent.supervisor import _bind
from agent.tools.contract import ToolSpec
from agent.tools.registry import load_registry, sanitize_tool_name
from agent.tools.sample_echo import TOOLS as SAMPLE_TOOLS
from agent.trigger_context import TriggerContext


class _Msg(BaseModel):
    message: str = "x"


def test_bind_decorates_with_sanitized_name_and_args_schema() -> None:
    """[DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-001] Structured typed fields via args_schema."""

    spec = ToolSpec(
        id="x.y",
        description="d",
        args_schema=_Msg,
        handler=lambda _: {"ok": True},
    )
    tool_obj = _bind(spec)
    assert getattr(tool_obj, "name", None) == sanitize_tool_name(spec.id)
    assert getattr(tool_obj, "args_schema", None) is _Msg


def test_bind_invokes_run_tool_json_with_spec_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-002] Bound tools share the ``run_tool_json`` → ``invoke_tool`` path."""

    calls: list[tuple[str, dict[str, object]]] = []

    def fake_run(cfg: RuntimeConfig, tid: str, args: dict[str, object]) -> str:
        calls.append((tid, args))
        return "{}"

    monkeypatch.setattr("agent.supervisor.run_tool_json", fake_run)

    spec = SAMPLE_TOOLS[0]
    tool_obj = _bind(spec)
    cfg = RuntimeConfig(
        rag_base_url="",
        subagents=[],
        skills=[],
        enabled_mcp_tools=["sample.echo"],
    )
    ctx = TriggerContext(
        cfg=cfg,
        body=TriggerBody(message="m"),
        system_prompt="s",
        request_id="r",
        run_id="run",
        thread_id="t",
        observability=None,
    )
    rt = ToolRuntime(
        state={},
        context=ctx,
        config={},
        stream_writer=lambda *_: None,
        tool_call_id=None,
        store=None,
    )
    tool_obj.func(rt, message="hi")
    assert calls == [("sample.echo", {"message": "hi"})]


def test_no_json_blob_fallback_for_registered_ids() -> None:
    """[DALC-REQ-TYPED-LANGCHAIN-TOOL-BINDINGS-003] No generic ``arguments_json`` wrapper for registry tools."""

    for spec in load_registry().values():
        schema = getattr(_bind(spec), "args_schema", None)
        assert schema is not None
        names = set(getattr(schema, "model_fields", {}).keys()) - {"runtime"}
        assert names, spec.id
        assert "arguments_json" not in names


@pytest.mark.parametrize("tid", sorted(load_registry().keys()))
def test_bind_registry_tools_have_nonempty_typed_args(tid: str) -> None:
    reg = load_registry()
    schema = getattr(_bind(reg[tid]), "args_schema", None)
    assert schema is not None
    fields = set(getattr(schema, "model_fields", {}).keys()) - {"runtime"}
    assert len(fields) >= 1
