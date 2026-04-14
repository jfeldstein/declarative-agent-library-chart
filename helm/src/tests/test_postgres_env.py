"""Postgres URL from ``HOSTED_AGENT_POSTGRES_URL``."""

from __future__ import annotations

import pytest

from hosted_agents.observability.postgres_env import postgres_url
from hosted_agents.observability.settings import ObservabilitySettings


def test_postgres_url_reads_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_POSTGRES_URL", "postgresql://u:p@a:1/db")
    assert postgres_url() == "postgresql://u:p@a:1/db"


def test_postgres_url_empty_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_POSTGRES_URL", raising=False)
    assert postgres_url() == ""


def test_settings_checkpoint_postgres_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_POSTGRES_URL", "postgresql://x:y@h:5432/db")
    monkeypatch.delenv("HOSTED_AGENT_USE_PGLITE", raising=False)
    s = ObservabilitySettings.from_env()
    assert s.checkpoint_postgres_url == "postgresql://x:y@h:5432/db"
