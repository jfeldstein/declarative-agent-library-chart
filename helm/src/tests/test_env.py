"""Tests for environment-backed config."""

import pytest

from hosted_agents.env import SYSTEM_PROMPT_ENV_KEY, system_prompt_from_env


def test_system_prompt_from_env_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(SYSTEM_PROMPT_ENV_KEY, raising=False)
    assert system_prompt_from_env() == ""


def test_system_prompt_from_env_set(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYSTEM_PROMPT_ENV_KEY, "  hello  ")
    assert system_prompt_from_env() == "hello"


def test_system_prompt_from_env_empty_string(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(SYSTEM_PROMPT_ENV_KEY, "   \n\t  ")
    assert system_prompt_from_env() == ""
