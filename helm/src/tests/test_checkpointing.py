"""LangGraph checkpointer and thread state HTTP APIs."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from agent.app import create_app
from agent.checkpointing import clear_memory_checkpointer
from agent.skills_state import reset_skill_unlocked_tools
from tests.conftest import patch_supervisor_fake_model, tool_then_text_responses


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    reset_skill_unlocked_tools()
    monkeypatch.setenv("HOSTED_AGENT_SYSTEM_PROMPT", 'Respond, "Main"')
    monkeypatch.setenv(
        "HOSTED_AGENT_SUBAGENTS_JSON",
        json.dumps(
            [
                {
                    "name": "s1",
                    "systemPrompt": 'Respond, "Sub1"',
                    "description": "Test specialist s1",
                },
            ],
        ),
    )
    monkeypatch.setenv("HOSTED_AGENT_SKILLS_JSON", json.dumps([]))
    monkeypatch.setenv("HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON", json.dumps([]))
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_STORE", "memory")
    return TestClient(create_app())


def test_thread_checkpoints_grow_with_invokes(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses("subagent_s1", {"task": "go"}, final_text="ok"),
    )
    tid = "conv-checkpoint-a"
    r1 = client.post("/api/v1/trigger", json={"message": "call s1", "thread_id": tid})
    assert r1.status_code == 200
    h1 = client.get(f"/api/v1/trigger/threads/{tid}/checkpoints")
    assert h1.status_code == 200
    n1 = len(h1.json())
    assert n1 >= 2
    r2 = client.post("/api/v1/trigger", json={"message": "again", "thread_id": tid})
    assert r2.status_code == 200
    n2 = len(client.get(f"/api/v1/trigger/threads/{tid}/checkpoints").json())
    assert n2 > n1


def test_thread_state_returns_snapshot(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses("subagent_s1", {"task": "go"}, final_text="ok"),
    )
    tid = "conv-state-b"
    client.post("/api/v1/trigger", json={"message": "call s1", "thread_id": tid})
    st = client.get(f"/api/v1/trigger/threads/{tid}/state")
    assert st.status_code == 200
    body = st.json()
    assert "values" in body
    assert body["values"].get("stage") == "done"


def test_checkpoint_apis_disabled_when_store_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_STORE", "none")
    clear_memory_checkpointer()
    c = TestClient(create_app())
    r = c.get("/api/v1/trigger/threads/any/state")
    assert r.status_code == 503


def test_ephemeral_invocation_leaves_no_history(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses("subagent_s1", {"task": "go"}, final_text="ok"),
    )
    tid = "conv-eph-c"
    r = client.post(
        "/api/v1/trigger",
        json={"message": "call s1", "thread_id": tid, "ephemeral": True},
    )
    assert r.status_code == 200
    hist = client.get(f"/api/v1/trigger/threads/{tid}/checkpoints").json()
    assert hist == []


def test_thread_id_from_header(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    patch_supervisor_fake_model(
        monkeypatch,
        tool_then_text_responses("subagent_s1", {"task": "go"}, final_text="ok"),
    )
    tid = "from-header-xyz"
    client.post(
        "/api/v1/trigger",
        json={"message": "call s1"},
        headers={"X-Thread-Id": tid},
    )
    st = client.get(f"/api/v1/trigger/threads/{tid}/state")
    assert st.status_code == 200
