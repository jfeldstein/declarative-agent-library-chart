"""Contract-style tests for W&B SDK interaction shape (mocked SDK)."""

from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from hosted_agents.observability.settings import ObservabilitySettings
from hosted_agents.observability.wandb_trace import WandbTraceSession


@pytest.fixture()
def fake_wandb(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """A stand-in module whose ``init``/``Run`` surface matches the W&B Python SDK."""

    mod = MagicMock()
    run = MagicMock()
    run.id = "wandb-run-1"
    mod.init = MagicMock(return_value=run)
    mod.finish = MagicMock()
    monkeypatch.setitem(sys.modules, "wandb", mod)
    return mod


def test_wandb_trace_session_init_matches_sdk_entrypoint(
    monkeypatch: pytest.MonkeyPatch, fake_wandb: MagicMock
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_WANDB_ENABLED", "true")
    monkeypatch.setenv("WANDB_PROJECT", "contract-proj")
    obs = ObservabilitySettings.from_env()

    tags = {"agent_id": "a1", "thread_id": "th1", "rollout_arm": "primary"}
    sess = WandbTraceSession(settings=obs, run_name="run-contract", tags=tags)

    fake_wandb.init.assert_called_once()
    call_kw = fake_wandb.init.call_args.kwargs
    assert call_kw["project"] == "contract-proj"
    assert call_kw["name"] == "run-contract"
    assert isinstance(call_kw["tags"], list)
    assert any("agent_id=a1" in t for t in call_kw["tags"])

    sess.log_tool_span(
        tool_call_id="tc-1",
        tool_name="noop",
        duration_s=0.01,
    )
    sess.log_feedback(
        tool_call_id="tc-1",
        checkpoint_id="cp-1",
        feedback_label="positive",
        feedback_source="slack_reaction",
    )
    sess.finish()
    sess._wandb_run.log.assert_called()
    sess._wandb_run.finish.assert_called_once()
