"""PGlite optional embed (mocked; no Node / real PGlite in CI)."""

from __future__ import annotations

import os
import sys
import types
from unittest.mock import MagicMock, patch

import pytest

from hosted_agents.observability import pglite_runtime as pr


def test_pglite_noop_when_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_USE_PGLITE", raising=False)
    pr.ensure_pglite_embedded()
    assert pr._manager is None


def test_pglite_syncs_single_url_to_both(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("HOSTED_AGENT_USE_PGLITE", raising=False)
    u = "postgresql://a:b@db:5432/x"
    monkeypatch.setenv("HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", u)
    monkeypatch.delenv("HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL", raising=False)
    pr.ensure_pglite_embedded()
    assert os.environ.get("HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL") == u


def test_pglite_starts_embedded_and_sets_urls(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_USE_PGLITE", "1")
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL", raising=False)

    fake_uri = "postgresql://postgres:postgres@127.0.0.1:65432/postgres?sslmode=disable"
    mgr = MagicMock()
    mgr.get_psycopg_uri.return_value = fake_uri

    fake_mod = types.ModuleType("py_pglite")
    fake_mod.PGliteConfig = MagicMock()
    fake_mod.PGliteManager = MagicMock(return_value=mgr)

    pr.stop_pglite_embedded()
    with patch.dict(sys.modules, {"py_pglite": fake_mod}):
        pr.ensure_pglite_embedded()

    assert os.environ["HOSTED_AGENT_CHECKPOINT_POSTGRES_URL"] == fake_uri
    assert os.environ["HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL"] == fake_uri
    mgr.start.assert_called_once()
    assert pr._manager is mgr


def test_pglite_missing_dependency_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOSTED_AGENT_USE_PGLITE", "1")
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL", raising=False)

    class _Missing(types.ModuleType):
        def __getattr__(self, _name: str) -> None:
            raise ImportError("py-pglite not installed")

    saved = sys.modules.get("py_pglite")
    try:
        sys.modules["py_pglite"] = _Missing("py_pglite")
        pr.stop_pglite_embedded()
        with pytest.raises(RuntimeError, match="uv sync --extra pglite"):
            pr.ensure_pglite_embedded()
    finally:
        pr.stop_pglite_embedded()
        if saved is not None:
            sys.modules["py_pglite"] = saved
        else:
            sys.modules.pop("py_pglite", None)
