"""Tests for trigger reply mapping."""

import pytest

from hosted_agents.reply import trigger_reply_text


def test_trigger_reply_extracts_respond_double_quotes() -> None:
    prompt = 'Respond, "Hello :wave:"'
    assert trigger_reply_text(prompt) == "Hello :wave:"


def test_trigger_reply_extracts_respond_single_quotes() -> None:
    prompt = "Respond, 'Hi there'"
    assert trigger_reply_text(prompt) == "Hi there"


def test_trigger_reply_falls_back_to_full_prompt() -> None:
    prompt = "Just be helpful."
    assert trigger_reply_text(prompt) == "Just be helpful."


def test_trigger_reply_strips_outer_whitespace() -> None:
    prompt = '  Respond, "x"  '
    assert trigger_reply_text(prompt) == "x"


def test_trigger_reply_empty_raises() -> None:
    with pytest.raises(ValueError, match="system prompt is required"):
        trigger_reply_text("")
    with pytest.raises(ValueError, match="system prompt is required"):
        trigger_reply_text("   \n")
