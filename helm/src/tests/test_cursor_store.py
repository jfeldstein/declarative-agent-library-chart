"""Tests for scraper cursor persistence backends."""

from __future__ import annotations

import types

import pytest

from hosted_agents.scrapers import cursor_store


def test_file_store_jira_compat_roundtrip(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[DALC-REQ-SCRAPER-CURSOR-001]"""
    monkeypatch.setenv("JIRA_WATERMARK_DIR", str(tmp_path / "jira"))
    store = cursor_store.FileCursorStore()
    store.set_state("jira", "scope-a", "project = DEMO", "2024-03-01T00:00:00.000+0000")

    value = store.get_state("jira", "scope-a", "project = DEMO")
    assert value == "2024-03-01T00:00:00.000+0000"


def test_file_store_slack_compat_roundtrip(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """[DALC-REQ-SCRAPER-CURSOR-001]"""
    monkeypatch.setenv("SLACK_STATE_DIR", str(tmp_path / "slack"))
    store = cursor_store.FileCursorStore()
    store.set_state("slack", "scope-b", "C123", "1712509312.123456")

    value = store.get_state("slack", "scope-b", "C123")
    assert value == "1712509312.123456"


def test_postgres_store_issues_idempotent_ddl_and_upsert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """[DALC-REQ-SCRAPER-CURSOR-002]"""
    sql_calls: list[tuple[str, object]] = []

    class FakeCursor:
        def __enter__(self) -> "FakeCursor":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def execute(self, sql: str, params: object = None) -> None:
            sql_calls.append((" ".join(sql.split()), params))

        def fetchone(self) -> tuple[str] | None:
            return ("stored",)

    class FakeConn:
        def __enter__(self) -> "FakeConn":
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def cursor(self) -> FakeCursor:
            return FakeCursor()

    def fake_connect(dsn: str, autocommit: bool = False) -> FakeConn:
        assert dsn == "postgres://example"
        assert autocommit is True
        return FakeConn()

    monkeypatch.setattr(
        cursor_store, "psycopg", types.SimpleNamespace(connect=fake_connect)
    )

    store = cursor_store.PostgresCursorStore("postgres://example")
    store.set_state("jira", "scope-x", "k1", "v1")
    assert store.get_state("jira", "scope-x", "k1") == "stored"

    ddl_calls = [
        sql
        for sql, _ in sql_calls
        if "CREATE TABLE IF NOT EXISTS scraper_cursor_state" in sql
    ]
    upsert_calls = [
        sql for sql, _ in sql_calls if "INSERT INTO scraper_cursor_state" in sql
    ]
    select_calls = [sql for sql, _ in sql_calls if "SELECT value" in sql]
    assert len(ddl_calls) == 1
    assert len(upsert_calls) == 1
    assert len(select_calls) == 1
