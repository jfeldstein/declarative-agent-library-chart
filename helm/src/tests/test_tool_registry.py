"""Tests for entry-point registry loading and validation."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from agent.tools.contract import ToolSpec
from agent.tools.registry import (
    ENTRY_POINT_GROUP,
    _reset_for_tests,
    load_registry,
    register_toolspec,
    registered_ids,
    sanitize_tool_name,
)


def test_load_registry_discovers_all_builtins() -> None:
    reg = load_registry()
    keys = set(reg.keys())
    assert keys.issuperset(
        {
            "sample.echo",
            "slack.post_message",
            "slack.reactions_add",
            "slack.reactions_remove",
            "slack.chat_update",
            "slack.conversations_history",
            "slack.conversations_replies",
            "jira.search_issues",
            "jira.get_issue",
            "jira.add_comment",
            "jira.transition_issue",
            "jira.create_issue",
            "jira.update_issue",
        }
    )


def test_load_registry_is_idempotent() -> None:
    a = load_registry()
    b = load_registry()
    assert a is b


def test_duplicate_id_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_for_tests()
    reg = load_registry()

    class M(__import__("pydantic").BaseModel):  # noqa: PLC0415
        q: str = ""

    dup = ToolSpec(
        id=next(iter(reg.keys())),
        description="x",
        args_schema=M,
        handler=lambda _: {},
    )
    with pytest.raises(ValueError, match="duplicate ToolSpec id"):
        register_toolspec(dup)


def test_sanitized_collision_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_for_tests()

    class M(__import__("pydantic").BaseModel):
        x: int = 1

    specs = (
        ToolSpec(
            id="foo.bar",
            description="a",
            args_schema=M,
            handler=lambda _: {},
        ),
        ToolSpec(
            id="foo-bar",
            description="b",
            args_schema=M,
            handler=lambda _: {},
        ),
    )

    fake_ep = MagicMock()
    fake_ep.load.return_value = specs

    eps = MagicMock()
    eps.select.return_value = [fake_ep]
    monkeypatch.setattr("agent.tools.registry.entry_points", lambda: eps)
    with pytest.raises(ValueError, match="both sanitize"):
        load_registry()


def test_sanitize_empty_raises() -> None:
    with pytest.raises(ValueError):
        sanitize_tool_name("...")


def test_sanitize_preserves_underscore_run() -> None:
    assert sanitize_tool_name("slack.post_message") == "slack_post_message"


def test_register_toolspec_adds_and_rejects_dup() -> None:
    _reset_for_tests()
    load_registry()

    class M(__import__("pydantic").BaseModel):
        q: str = ""

    fresh = ToolSpec(
        id="custom.tool.__unique__",
        description="t",
        args_schema=M,
        handler=lambda _: {},
    )
    register_toolspec(fresh)
    assert fresh.id in registered_ids()
    with pytest.raises(ValueError, match="duplicate"):
        register_toolspec(fresh)


def test_non_toolspec_entry_point_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_for_tests()
    fake_ep = MagicMock()
    fake_ep.load.return_value = (object(),)
    monkeypatch.setattr(
        "agent.tools.registry.entry_points",
        lambda: MagicMock(select=lambda **_k: [fake_ep]),
    )
    with pytest.raises(TypeError, match="expected ToolSpec"):
        load_registry()


def test_reset_for_tests_clears_cache() -> None:
    load_registry()
    register_toolspec(
        ToolSpec(
            id="only.in.test.registry",
            description="z",
            args_schema=__import__("pydantic").BaseModel,
            handler=lambda _: {},
        ),
    )
    assert "only.in.test.registry" in load_registry()
    _reset_for_tests()
    reg = load_registry()
    assert "only.in.test.registry" not in reg


def test_entry_point_group_constant() -> None:
    assert ENTRY_POINT_GROUP == "declarative_agent.tools"
