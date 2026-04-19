"""Mandatory W&B tag resolution (env + trigger context)."""

from __future__ import annotations

import pytest

from agent.agent_models import TriggerBody
from agent.observability.wandb_run_tags import wandb_mandatory_tags_for_run
from agent.runtime_config import RuntimeConfig
from agent.trigger_context import TriggerContext


def _ctx(body: TriggerBody | None) -> TriggerContext:
    return TriggerContext(
        cfg=RuntimeConfig(
            rag_base_url="",
            subagents=[],
            skills=[],
            enabled_mcp_tools=[],
        ),
        body=body,
        system_prompt="s",
        request_id="req-99",
        run_id="run-99",
        thread_id="thr-99",
    )


def test_tags_from_env_and_thread(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_ID", "agent-a")
    monkeypatch.setenv("HOSTED_AGENT_ENV", "staging")
    monkeypatch.setenv("HOSTED_AGENT_SKILL_VERSION", "v2")
    monkeypatch.setenv("HOSTED_AGENT_CHAT_MODEL", "gpt-test")
    monkeypatch.setenv("HOSTED_AGENT_PROMPT_HASH", "deadbeef")
    monkeypatch.setenv("HOSTED_AGENT_ROLLOUT_ARM", "shadow-a")
    tags = wandb_mandatory_tags_for_run(thread_id="t1", ctx=None)
    assert tags["agent_id"] == "agent-a"
    assert tags["environment"] == "staging"
    assert tags["skill_version"] == "v2"
    assert tags["model_id"] == "gpt-test"
    assert tags["prompt_hash"] == "deadbeef"
    assert tags["rollout_arm"] == "shadow-a"
    assert tags["thread_id"] == "t1"


def test_skill_id_prefers_load_skill_over_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SKILL_ID", "from-env")
    ctx = _ctx(TriggerBody(load_skill="from-body"))
    tags = wandb_mandatory_tags_for_run(thread_id="t2", ctx=ctx)
    assert tags["skill_id"] == "from-body"


def test_skill_id_falls_back_to_tool(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_SKILL_ID", raising=False)
    ctx = _ctx(TriggerBody(tool="sample.echo", tool_arguments={}))
    tags = wandb_mandatory_tags_for_run(thread_id="t3", ctx=ctx)
    assert tags["skill_id"] == "sample.echo"


def test_request_correlation_from_ctx(monkeypatch: pytest.MonkeyPatch) -> None:
    ctx = _ctx(None)
    tags = wandb_mandatory_tags_for_run(thread_id="t4", ctx=ctx)
    assert tags["request_correlation_id"] == "req-99"
