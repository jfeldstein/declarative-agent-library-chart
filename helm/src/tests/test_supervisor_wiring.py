"""Supervisor wiring: ``create_agent`` context + error mapping."""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage

from agent.agent_models import TriggerBody
from agent.chat_model import FakeToolChatModel
from agent.llm_metrics import SupervisorLlmMetricsCallback
from agent.runtime_config import RuntimeConfig
from agent.supervisor import run_supervisor_agent
from agent.trigger_context import TriggerContext
from agent.trigger_errors import TriggerHttpError


def _ctx(enabled: list[str] | None = None) -> TriggerContext:
    cfg = RuntimeConfig(
        rag_base_url="",
        subagents=[],
        skills=[],
        enabled_mcp_tools=enabled or ["sample.echo"],
    )
    return TriggerContext(
        cfg=cfg,
        body=TriggerBody(message="m"),
        system_prompt="s",
        request_id="r",
        run_id="run",
        thread_id="t",
        observability=None,
    )


def test_run_supervisor_agent_passes_context_schema_and_context(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, object] = {}

    def fake_create_agent(*args: object, **kwargs: object):
        captured.update(kwargs)

        class _A:
            def invoke(self, *_a: object, **_kw: object) -> dict[str, object]:
                return {"messages": []}

        return _A()

    monkeypatch.setattr("agent.supervisor.create_agent", fake_create_agent)
    monkeypatch.setattr(
        "agent.supervisor.resolve_chat_model",
        lambda: FakeToolChatModel(responses=[AIMessage(content="ok")]),
    )
    monkeypatch.setattr(
        "agent.supervisor.build_supervisor_tools",
        lambda _ctx: [],
    )
    ctx = _ctx()
    run_supervisor_agent(ctx, "hello")
    assert captured.get("context_schema") is TriggerContext


def test_run_supervisor_agent_wraps_model_error_as_503(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "agent.supervisor.resolve_chat_model",
        lambda: (_ for _ in ()).throw(ValueError("no model")),
    )
    with pytest.raises(TriggerHttpError) as exc:
        run_supervisor_agent(_ctx(), "hello")
    assert exc.value.status_code == 503


def test_run_supervisor_agent_invoke_passes_callbacks(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoke_kw: dict[str, object] = {}

    class _Agent:
        def invoke(self, *_a: object, **kw: object) -> dict[str, object]:
            invoke_kw.update(kw)
            return {"messages": []}

    monkeypatch.setattr(
        "agent.supervisor.create_agent",
        lambda *a, **k: _Agent(),
    )
    monkeypatch.setattr(
        "agent.supervisor.resolve_chat_model",
        lambda: FakeToolChatModel(responses=[AIMessage(content="ok")]),
    )
    monkeypatch.setattr(
        "agent.supervisor.build_supervisor_tools",
        lambda _ctx: [],
    )
    ctx = _ctx()
    run_supervisor_agent(ctx, "hello")
    assert invoke_kw.get("context") is ctx
    cfg = invoke_kw.get("config")
    cb = cfg.get("callbacks", []) if isinstance(cfg, dict) else []
    assert any(isinstance(x, SupervisorLlmMetricsCallback) for x in cb)
