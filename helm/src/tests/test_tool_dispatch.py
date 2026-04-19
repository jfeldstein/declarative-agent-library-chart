"""Tests for in-process tool dispatch."""

from __future__ import annotations

import pytest

from hosted_agents.tools.dispatch import invoke_tool


def test_sample_echo() -> None:
    out = invoke_tool("sample.echo", {"message": "hi"})
    assert out == {"echo": "hi"}


def test_unknown_tool() -> None:
    with pytest.raises(KeyError):
        invoke_tool("nope", {})
