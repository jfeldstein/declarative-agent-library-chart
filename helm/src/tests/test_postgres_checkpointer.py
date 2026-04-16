"""Postgres checkpointer wiring (mocked; no real database)."""

from __future__ import annotations

import pytest

from hosted_agents.observability.checkpointer import (
    build_checkpointer,
    reset_checkpoint_postgres_pool,
)
from hosted_agents.observability.settings import ObservabilitySettings


def test_build_checkpointer_postgres_requires_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", "1")
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_BACKEND", "postgres")
    monkeypatch.delenv("HOSTED_AGENT_POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_USE_PGLITE", raising=False)
    reset_checkpoint_postgres_pool()
    obs = ObservabilitySettings.from_env()
    with pytest.raises(
        RuntimeError,
        match="HOSTED_AGENT_POSTGRES_URL",
    ):
        build_checkpointer(obs)


def test_build_checkpointer_postgres_validates_scheme(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", "1")
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_BACKEND", "postgres")
    monkeypatch.setenv("HOSTED_AGENT_POSTGRES_URL", "mysql://wrong")
    reset_checkpoint_postgres_pool()
    obs = ObservabilitySettings.from_env()
    with pytest.raises(RuntimeError, match="postgres://"):
        build_checkpointer(obs)


def test_build_checkpointer_postgres_constructs_saver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINTS_ENABLED", "1")
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_BACKEND", "postgres")
    monkeypatch.setenv(
        "HOSTED_AGENT_POSTGRES_URL",
        "postgres://user:pass@127.0.0.1:5432/appdb",
    )
    reset_checkpoint_postgres_pool()

    pool_holder: dict[str, object] = {}

    class FakePool:
        def __init__(self, *args: object, **kwargs: object) -> None:
            pool_holder["args"] = (args, kwargs)

        def close(self) -> None:
            pool_holder["closed"] = True

    class FakeSaver:
        def __init__(self, conn: object) -> None:
            self.conn = conn

        def setup(self) -> None:
            pool_holder["setup"] = True

    import hosted_agents.observability.checkpointer as ch

    obs = ObservabilitySettings.from_env()
    monkeypatch.setattr(ch, "_checkpoint_connection_pool_cls", lambda: FakePool)
    monkeypatch.setattr(ch, "_checkpoint_postgres_saver_cls", lambda: FakeSaver)
    saver = build_checkpointer(obs)
    assert isinstance(saver, FakeSaver)
    assert pool_holder.get("setup") is True
    assert "args" in pool_holder
