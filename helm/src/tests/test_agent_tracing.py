"""Tests for W&B / checkpoint observability stubs (OpenSpec operator contract)."""

from __future__ import annotations

import pytest

from agent.agent_tracing import (
    MANDATORY_WANDB_TAG_KEYS,
    checkpoint_store_kind,
    observability_summary,
    wandb_trace_stub_config,
    wandb_tracing_ready,
)
from agent.checkpointing import checkpoints_globally_enabled


def test_defaults_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(
        "HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED", raising=False
    )
    monkeypatch.delenv("HOSTED_AGENT_WANDB_ENABLED", raising=False)
    monkeypatch.delenv("WANDB_API_KEY", raising=False)
    monkeypatch.delenv("WANDB_PROJECT", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_WANDB_PROJECT", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINT_STORE", raising=False)
    cfg = wandb_trace_stub_config()
    assert cfg.tracing_enabled_intent is False
    assert cfg.api_key_configured is False
    assert wandb_tracing_ready(cfg) is False
    assert checkpoint_store_kind() == "memory"


@pytest.mark.parametrize("flag", ("1", "true", "yes", "on"))
def test_tracing_ready_when_configured(
    monkeypatch: pytest.MonkeyPatch, flag: str
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED", flag)
    monkeypatch.setenv("WANDB_API_KEY", "secret")
    monkeypatch.setenv("WANDB_PROJECT", "demo")
    assert wandb_tracing_ready() is True


def test_wandb_tracing_ready_accepts_legacy_wandb_enabled_env(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-CHART-RTV-002] Legacy ``HOSTED_AGENT_WANDB_ENABLED`` still expresses tracing intent."""

    monkeypatch.delenv(
        "HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED", raising=False
    )
    monkeypatch.setenv("HOSTED_AGENT_WANDB_ENABLED", "true")
    monkeypatch.setenv("WANDB_API_KEY", "secret")
    monkeypatch.setenv("WANDB_PROJECT", "demo")
    assert wandb_tracing_ready() is True


def test_checkpoint_store_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_STORE", "memory")
    assert checkpoint_store_kind() == "memory"


def test_checkpoint_store_none_disables_feature_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_STORE", "none")
    assert checkpoint_store_kind() == "none"
    assert checkpoints_globally_enabled() is False
    summary = observability_summary()
    assert summary["feature_flags"]["checkpoints_enabled"] is False


def test_observability_summary_includes_mandatory_keys(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(
        "HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED", raising=False
    )
    monkeypatch.delenv("HOSTED_AGENT_WANDB_ENABLED", raising=False)
    summary = observability_summary()
    assert summary["checkpoint_store"] == "memory"
    wandb = summary["wandb"]
    assert wandb["tracing_enabled_intent"] is False
    assert wandb["mandatory_run_tag_keys"] == list(MANDATORY_WANDB_TAG_KEYS)
