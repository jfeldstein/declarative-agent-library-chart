"""W&B run scope (mocked; OpenSpec: wandb-agent-traces)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from hosted_agents.feedback_registry import load_feedback_registry
from hosted_agents.runtime_config import RuntimeConfig
from hosted_agents.trigger_context import TriggerContext
from hosted_agents.wandb_session import _tag_dict_for_run, wandb_run_scope


def _ctx() -> TriggerContext:
    return TriggerContext(
        cfg=RuntimeConfig(
            rag_base_url="",
            subagents=[],
            skills=[],
            enabled_mcp_tools=[],
        ),
        body=None,
        system_prompt="sys",
        request_id="req-1",
        run_id="run-abc",
        thread_id="thread-xyz",
        ephemeral=False,
    )


def test_tag_dict_includes_thread_and_run(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_ID", "agent-one")
    monkeypatch.setenv("HOSTED_AGENT_ENV", "test")
    tags = _tag_dict_for_run(_ctx())
    assert tags["agent_id"] == "agent-one"
    assert tags["environment"] == "test"
    assert tags["thread_id"] == "thread-xyz"
    assert tags["run_id"] == "run-abc"


def test_wandb_run_scope_calls_init_when_configured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_WANDB_ENABLED", "true")
    monkeypatch.setenv("WANDB_API_KEY", "secret-key")
    monkeypatch.setenv("WANDB_PROJECT", "proj")
    mock_mod = MagicMock()
    mock_run = MagicMock()
    mock_run.id = "wandb-run-id"
    mock_mod.init = MagicMock(return_value=mock_run)
    mock_mod.finish = MagicMock()
    monkeypatch.setitem(sys.modules, "wandb", mock_mod)
    with wandb_run_scope(_ctx()):
        pass
    mock_mod.init.assert_called_once()
    mock_mod.finish.assert_called_once()


def test_feedback_registry_scalar_labels() -> None:
    reg = load_feedback_registry()
    assert reg.labels["positive"]["scalar"] == 1
    assert reg.labels["negative"]["scalar"] == -1
