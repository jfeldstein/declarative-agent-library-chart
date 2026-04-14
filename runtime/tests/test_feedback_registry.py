"""Global feedback label registry (OpenSpec: agent-feedback-model)."""

from __future__ import annotations

from hosted_agents.feedback_registry import (
    load_feedback_registry,
    resolve_slack_reaction,
)


def test_load_registry() -> None:
    reg = load_feedback_registry()
    assert reg.registry_id == "global-human-feedback"
    assert reg.schema_version == "1"
    assert "positive" in reg.labels


def test_resolve_slack_positive() -> None:
    assert resolve_slack_reaction("+1") == ("positive", "1")
    assert resolve_slack_reaction("thumbsup") == ("positive", "1")


def test_resolve_slack_negative() -> None:
    assert resolve_slack_reaction("-1") == ("negative", "1")


def test_resolve_unknown_emoji() -> None:
    assert resolve_slack_reaction("unknown_emoji") is None
