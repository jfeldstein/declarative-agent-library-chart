"""Checkpointing, Slack feedback, and runtime operator routes."""

from __future__ import annotations

import json
import sys
import uuid
from typing import TypedDict
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from agent.app import create_app
from agent.observability.correlation import (
    SlackMessageRef,
    ToolCorrelation,
    correlation_store,
)
from agent.observability.feedback import feedback_store
from agent.observability.run_context import bind_run_context, set_wandb_session
from agent.observability.settings import ObservabilitySettings
from agent.observability.side_effects import side_effect_checkpoints
from agent.tools.dispatch import invoke_tool
from agent.observability.checkpointer import reset_compiled_trigger_graph_cache
from agent.trigger_graph import get_thread_state, get_thread_state_history


def _reset_graph() -> None:
    reset_compiled_trigger_graph_cache()


def test_runtime_summary_includes_observability_flags(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", "1")
    monkeypatch.setenv("HOSTED_AGENT_WANDB_ENABLED", "true")
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    r = client.get("/api/v1/runtime/summary")
    assert r.status_code == 200
    body = r.json()
    assert body["observability"]["checkpoints_enabled"] is True
    assert body["observability"]["wandb_enabled"] is True


def test_thread_state_requires_checkpointing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", raising=False)
    _reset_graph()
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    r = client.get(f"/api/v1/runtime/threads/{uuid.uuid4()}/state")
    assert r.status_code == 503


def test_thread_state_and_history_when_checkpointing_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", "1")
    monkeypatch.setenv(
        "HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps(["sample.echo"])
    )
    _reset_graph()
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    tid = "thread-checkpoints-1"
    resp = client.post(
        "/api/v1/trigger",
        json={"tool": "sample.echo", "tool_arguments": {"message": "x"}},
        headers={"X-Agent-Thread-Id": tid},
    )
    assert resp.status_code == 200
    st = client.get(f"/api/v1/runtime/threads/{tid}/state")
    assert st.status_code == 200
    assert "values" in st.json()
    hist = client.get(f"/api/v1/runtime/threads/{tid}/checkpoints")
    assert hist.status_code == 200
    assert len(hist.json()["checkpoints"]) >= 1


def test_ephemeral_skips_checkpoint_persistence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", "1")
    monkeypatch.setenv(
        "HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps(["sample.echo"])
    )
    _reset_graph()
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    tid = "thread-ephemeral"
    resp = client.post(
        "/api/v1/trigger",
        json={
            "tool": "sample.echo",
            "tool_arguments": {"message": "x"},
            "ephemeral": True,
        },
        headers={"X-Agent-Thread-Id": tid},
    )
    assert resp.status_code == 200
    hist = client.get(f"/api/v1/runtime/threads/{tid}/checkpoints")
    assert hist.status_code == 200
    # Ephemeral invocations skip persistence; no durable checkpoints for this thread.
    assert hist.json()["checkpoints"] == []


def test_side_effects_route_lists_slack_post(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps(["slack.post_message"])
    )
    _reset_graph()
    feedback_store.reset()
    side_effect_checkpoints.reset()
    correlation_store.reset()
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    tid = "thread-sidefx"
    bind_run_context(run_id="run-sfx", thread_id=tid)
    invoke_tool(
        "slack.post_message",
        {"channel_id": "C123", "text": "hello"},
    )
    r = client.get(f"/api/v1/runtime/threads/{tid}/side-effects")
    assert r.status_code == 200
    items = r.json()["side_effects"]
    assert len(items) == 1
    assert items[0]["tool_name"] == "slack.post_message"


def test_slack_reaction_logs_feedback_via_wandb_sdk_when_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Reaction → correlation → W&B ``run.log`` / ``finish`` (mock SDK), not only in-memory store."""
    monkeypatch.setenv("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED", "true")
    monkeypatch.setenv("HOSTED_AGENT_WANDB_ENABLED", "true")
    monkeypatch.setenv("WANDB_PROJECT", "e2e-proj")
    monkeypatch.setenv("WANDB_API_KEY", "test-key")
    monkeypatch.setenv(
        "HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON",
        json.dumps({"+1": "positive"}),
    )
    feedback_store.reset()
    correlation_store.reset()
    mock_wandb = MagicMock()
    wb_run = MagicMock()
    wb_run.id = "wandb-run-e2e"
    mock_wandb.init = MagicMock(return_value=wb_run)
    mock_wandb.finish = MagicMock()
    monkeypatch.setitem(sys.modules, "wandb", mock_wandb)

    ref = SlackMessageRef(channel_id="C1", message_ts="1.0")
    correlation_store.put_slack_message(
        ref,
        ToolCorrelation(
            tool_call_id="tc-e2e",
            run_id="r-e2e",
            thread_id="t-e2e",
            checkpoint_id="cp-e2e",
            tool_name="slack.post_message",
        ),
    )
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    r = client.post(
        "/api/v1/integrations/slack/reactions",
        json={
            "channel_id": "C1",
            "message_ts": "1.0",
            "reaction": "+1",
            "event_id": "evt-e2e",
            "user_id": "U1",
        },
    )
    assert r.status_code == 200
    mock_wandb.init.assert_called_once()
    wb_run.log.assert_called()
    wb_run.finish.assert_called_once()


def test_slack_reaction_records_human_feedback(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED", "true")
    monkeypatch.setenv(
        "HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON",
        json.dumps({"+1": "positive"}),
    )
    feedback_store.reset()
    correlation_store.reset()
    ref = SlackMessageRef(channel_id="C1", message_ts="1.0")
    correlation_store.put_slack_message(
        ref,
        ToolCorrelation(
            tool_call_id="tc-1",
            run_id="r1",
            thread_id="t1",
            checkpoint_id="cp-1",
            tool_name="slack.post_message",
        ),
    )
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    payload = {
        "channel_id": "C1",
        "message_ts": "1.0",
        "reaction": "+1",
        "event_id": "evt-1",
        "user_id": "U1",
    }
    r = client.post("/api/v1/integrations/slack/reactions", json=payload)
    assert r.status_code == 200
    assert r.json()["status"] == "recorded"
    listed = client.get("/api/v1/runtime/feedback/human")
    assert listed.status_code == 200
    assert listed.json()["events"][0]["label_id"] == "positive"


def test_slack_reaction_removed_retracts_human_feedback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED", "true")
    monkeypatch.setenv(
        "HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON",
        json.dumps({"+1": "positive"}),
    )
    feedback_store.reset()
    correlation_store.reset()
    ref = SlackMessageRef(channel_id="C1", message_ts="1.0")
    correlation_store.put_slack_message(
        ref,
        ToolCorrelation(
            tool_call_id="tc-1",
            run_id="r1",
            thread_id="t1",
            checkpoint_id="cp-1",
            tool_name="slack.post_message",
        ),
    )
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    client.post(
        "/api/v1/integrations/slack/reactions",
        json={
            "channel_id": "C1",
            "message_ts": "1.0",
            "reaction": "+1",
            "event_id": "evt-add",
            "user_id": "U1",
        },
    )
    assert client.get("/api/v1/runtime/feedback/human").json()["events"]
    rm = client.post(
        "/api/v1/integrations/slack/reactions",
        json={
            "channel_id": "C1",
            "message_ts": "1.0",
            "reaction": "+1",
            "event_id": "evt-rm",
            "user_id": "U1",
            "event_type": "reaction_removed",
        },
    )
    assert rm.status_code == 200
    assert rm.json()["status"] == "retracted"
    assert client.get("/api/v1/runtime/feedback/human").json()["events"] == []


def test_slack_reaction_positive_then_negative_retracts_positive(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED", "true")
    monkeypatch.setenv(
        "HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON",
        json.dumps({"+1": "positive", "-1": "negative"}),
    )
    feedback_store.reset()
    correlation_store.reset()
    ref = SlackMessageRef(channel_id="C1", message_ts="1.0")
    correlation_store.put_slack_message(
        ref,
        ToolCorrelation(
            tool_call_id="tc-1",
            run_id="r1",
            thread_id="t1",
            checkpoint_id="cp-1",
            tool_name="slack.post_message",
        ),
    )
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    client.post(
        "/api/v1/integrations/slack/reactions",
        json={
            "channel_id": "C1",
            "message_ts": "1.0",
            "reaction": "+1",
            "user_id": "U1",
        },
    )
    client.post(
        "/api/v1/integrations/slack/reactions",
        json={
            "channel_id": "C1",
            "message_ts": "1.0",
            "reaction": "-1",
            "user_id": "U1",
        },
    )
    evs = client.get("/api/v1/runtime/feedback/human").json()["events"]
    assert len(evs) == 1
    assert evs[0]["label_id"] == "negative"


def test_slack_reaction_negative_then_positive_retracts_negative(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED", "true")
    monkeypatch.setenv(
        "HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON",
        json.dumps({"+1": "positive", "-1": "negative"}),
    )
    feedback_store.reset()
    correlation_store.reset()
    ref = SlackMessageRef(channel_id="C1", message_ts="1.0")
    correlation_store.put_slack_message(
        ref,
        ToolCorrelation(
            tool_call_id="tc-1",
            run_id="r1",
            thread_id="t1",
            checkpoint_id="cp-1",
            tool_name="slack.post_message",
        ),
    )
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    client.post(
        "/api/v1/integrations/slack/reactions",
        json={
            "channel_id": "C1",
            "message_ts": "1.0",
            "reaction": "-1",
            "user_id": "U1",
        },
    )
    client.post(
        "/api/v1/integrations/slack/reactions",
        json={
            "channel_id": "C1",
            "message_ts": "1.0",
            "reaction": "+1",
            "user_id": "U1",
        },
    )
    evs = client.get("/api/v1/runtime/feedback/human").json()["events"]
    assert len(evs) == 1
    assert evs[0]["label_id"] == "positive"


def test_slack_orphan_without_correlation(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED", "true")
    feedback_store.reset()
    correlation_store.reset()
    app = create_app(system_prompt='Respond, "Hi"')
    client = TestClient(app)
    r = client.post(
        "/api/v1/integrations/slack/reactions",
        json={
            "channel_id": "C9",
            "message_ts": "9.9",
            "reaction": "+1",
            "event_id": "e2",
            "user_id": "U9",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "orphan"
    assert feedback_store.orphans()


def test_run_tool_json_logs_span_when_wandb_session_bound(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv(
        "HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps(["sample.echo"])
    )
    calls: list[dict] = []

    class _Sess:
        def log_tool_span(self, **kwargs: object) -> None:
            calls.append(dict(kwargs))

    bind_run_context(run_id="r-wandb", thread_id="t-wandb")
    set_wandb_session(_Sess())
    try:
        from agent.runtime_config import RuntimeConfig
        from agent.trigger_steps import run_tool_json

        run_tool_json(RuntimeConfig.from_env(), "sample.echo", {"message": "z"})
    finally:
        set_wandb_session(None)
    assert calls and calls[0]["tool_name"] == "sample.echo"


def test_get_thread_state_functions_directly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", "1")
    monkeypatch.setenv(
        "HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps(["sample.echo"])
    )
    _reset_graph()
    from agent.agent_models import TriggerBody
    from agent.runtime_config import RuntimeConfig
    from agent.runtime_identity import resolve_run_identity
    from agent.trigger_context import TriggerContext
    from agent.trigger_graph import run_trigger_graph

    tid = "direct-api"
    tb = TriggerBody(tool="sample.echo", tool_arguments={"message": "y"})
    ctx = TriggerContext(
        cfg=RuntimeConfig.from_env(),
        run_identity=resolve_run_identity(body=tb),
        body=tb,
        system_prompt='Respond, "Hi"',
        request_id="req",
        thread_id=tid,
        run_id=str(uuid.uuid4()),
        observability=ObservabilitySettings.from_env(),
    )
    run_trigger_graph(ctx)
    snap = get_thread_state(tid)
    assert getattr(snap, "values", None) is not None
    hist = get_thread_state_history(tid)
    assert isinstance(hist, list)


def test_langgraph_memory_checkpoint_resume() -> None:
    """Completed tasks are not re-run after a mid-graph failure (MemorySaver)."""

    from langgraph.checkpoint.memory import MemorySaver
    from langgraph.graph import END, START, StateGraph

    class _S(TypedDict):
        n: int

    attempts = {"count": 0}

    def _a(state: _S) -> _S:
        return {"n": 1}

    def _b(state: _S) -> _S:
        attempts["count"] += 1
        if attempts["count"] == 1:
            msg = "boom"
            raise RuntimeError(msg)
        return {"n": 2}

    g = StateGraph(_S)
    g.add_node("a", _a)
    g.add_node("b", _b)
    g.add_edge(START, "a")
    g.add_edge("a", "b")
    g.add_edge("b", END)
    app = g.compile(checkpointer=MemorySaver())
    cfg: dict = {"configurable": {"thread_id": "resume-langgraph"}}
    with pytest.raises(RuntimeError, match="boom"):
        app.invoke({"n": 0}, config=cfg)
    out = app.invoke({"n": 0}, config=cfg)
    assert out["n"] == 2
    assert attempts["count"] == 2
