"""Postgres URL resolution: ``HOSTED_AGENT_POSTGRES_URL`` + legacy fallbacks."""

from __future__ import annotations

import pytest

from hosted_agents.observability.postgres_env import effective_postgres_url
from hosted_agents.observability.settings import ObservabilitySettings


def test_effective_postgres_url_prefers_unified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_POSTGRES_URL", "postgresql://u:p@a:1/db")
    monkeypatch.setenv(
        "HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", "postgresql://ignored:ignored@b:2/x"
    )
    assert effective_postgres_url() == "postgresql://u:p@a:1/db"


def test_effective_postgres_url_legacy_checkpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_POSTGRES_URL", raising=False)
    monkeypatch.setenv(
        "HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", "postgresql://legacy:legacy@c:3/y"
    )
    monkeypatch.delenv("HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL", raising=False)
    assert effective_postgres_url() == "postgresql://legacy:legacy@c:3/y"


def test_effective_postgres_url_legacy_observability(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", raising=False)
    monkeypatch.setenv(
        "HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL", "postgresql://obs:o@db:5432/o"
    )
    assert effective_postgres_url() == "postgresql://obs:o@db:5432/o"


def test_settings_checkpoint_postgres_url_from_legacy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("HOSTED_AGENT_POSTGRES_URL", raising=False)
    monkeypatch.setenv(
        "HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", "postgresql://x:y@h:5432/db"
    )
    monkeypatch.delenv("HOSTED_AGENT_USE_PGLITE", raising=False)
    s = ObservabilitySettings.from_env()
    assert s.checkpoint_postgres_url == "postgresql://x:y@h:5432/db"
