"""Unit tests for observability settings and run context (delivery step 1)."""

from __future__ import annotations

import json

import pytest

from hosted_agents.observability import run_context as obs_rc
from hosted_agents.observability.settings import ObservabilitySettings


@pytest.fixture(autouse=True)
def _reset_observability_context() -> None:
    """Contextvars persist across tests in one process; clear around each case."""
    obs_rc._run_id.set(None)  # noqa: SLF001
    obs_rc._thread_id.set(None)  # noqa: SLF001
    obs_rc._tool_call_id.set(None)  # noqa: SLF001
    obs_rc._request_correlation_id.set(None)  # noqa: SLF001
    obs_rc._wandb_session.set(None)  # noqa: SLF001
    yield
    obs_rc._run_id.set(None)  # noqa: SLF001
    obs_rc._thread_id.set(None)  # noqa: SLF001
    obs_rc._tool_call_id.set(None)  # noqa: SLF001
    obs_rc._request_correlation_id.set(None)  # noqa: SLF001
    obs_rc._wandb_session.set(None)  # noqa: SLF001


def test_observability_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINT_BACKEND", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_WANDB_ENABLED", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_ATIF_EXPORT_ENABLED", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_SHADOW_ENABLED", raising=False)
    monkeypatch.delenv("WANDB_PROJECT", raising=False)
    monkeypatch.delenv("WANDB_ENTITY", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_OPERATIONAL_MAPPER_FLAGS_JSON", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_SHADOW_ALLOW_TENANTS_JSON", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_SHADOW_SAMPLE_RATE", raising=False)

    s = ObservabilitySettings.from_env()
    assert s.checkpoints_enabled is False
    assert s.checkpoint_backend == "memory"
    assert s.checkpoint_postgres_url is None
    assert s.wandb_enabled is False
    assert s.slack_feedback_enabled is False
    assert s.atif_export_enabled is False
    assert s.shadow_enabled is False
    assert s.wandb_project is None
    assert s.wandb_entity is None
    assert s.slack_emoji_map == {}
    assert s.shadow_sample_rate == 0.0
    assert s.shadow_allow_tenants == frozenset()
    assert s.operational_mapper_flags == {}


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("1", True),
        ("true", True),
        ("yes", True),
        ("on", True),
        ("0", False),
        ("FALSE", False),
    ],
)
def test_observability_settings_truthy_flags(
    monkeypatch: pytest.MonkeyPatch, raw: str, expected: bool
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", raw)
    s = ObservabilitySettings.from_env()
    assert s.checkpoints_enabled is expected


def test_observability_settings_slack_emoji_map(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON",
        json.dumps({"+1": "positive", "bad": 3}),
    )
    s = ObservabilitySettings.from_env()
    assert s.slack_emoji_map == {"+1": "positive"}


def test_observability_settings_slack_emoji_map_invalid_type(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON", json.dumps(["x"]))
    with pytest.raises(ValueError, match="must be a JSON object"):
        ObservabilitySettings.from_env()


def test_observability_settings_operational_mappers(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "HOSTED_AGENT_OPERATIONAL_MAPPER_FLAGS_JSON",
        json.dumps({"a": True, "b": False, "c": "no"}),
    )
    s = ObservabilitySettings.from_env()
    assert s.operational_mapper_flags == {"a": True, "b": False}


def test_observability_settings_shadow_tenants_and_rate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_SHADOW_ALLOW_TENANTS_JSON", json.dumps(["t1", 2]))
    monkeypatch.setenv("HOSTED_AGENT_SHADOW_SAMPLE_RATE", "2.5")
    s = ObservabilitySettings.from_env()
    assert s.shadow_allow_tenants == frozenset({"t1", "2"})
    assert s.shadow_sample_rate == 1.0

    monkeypatch.setenv("HOSTED_AGENT_SHADOW_SAMPLE_RATE", "nope")
    s2 = ObservabilitySettings.from_env()
    assert s2.shadow_sample_rate == 0.0


def test_observability_settings_checkpoint_backend_strip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_BACKEND", "  postgres  ")
    s = ObservabilitySettings.from_env()
    assert s.checkpoint_backend == "postgres"


def test_observability_settings_checkpoint_backend_empty_falls_back(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_BACKEND", "   ")
    s = ObservabilitySettings.from_env()
    assert s.checkpoint_backend == "memory"


def test_obs_run_context_bind_and_getters() -> None:
    obs_rc.bind_run_context(run_id="r1", thread_id="t1", request_correlation_id="c1")
    assert obs_rc.get_run_id() == "r1"
    assert obs_rc.get_thread_id() == "t1"
    assert obs_rc.get_request_correlation_id() == "c1"


def test_obs_run_context_correlation_defaults_to_run_id() -> None:
    obs_rc.bind_run_context(run_id="r2", thread_id="t2")
    assert obs_rc.get_request_correlation_id() == "r2"


def test_obs_tool_call_and_wandb_session() -> None:
    tid = obs_rc.new_tool_call_id(prefix="pfx")
    assert tid.startswith("pfx-")
    assert obs_rc.get_tool_call_id() == tid

    obs_rc.clear_tool_call_id()
    assert obs_rc.get_tool_call_id() is None

    obs_rc.set_wandb_session({"mock": True})
    assert obs_rc.get_wandb_session() == {"mock": True}
    obs_rc.set_wandb_session(None)
    assert obs_rc.get_wandb_session() is None
