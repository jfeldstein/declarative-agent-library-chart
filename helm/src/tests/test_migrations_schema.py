"""Bundled observability DDL loader.

[DALC-REQ-POSTGRES-AGENT-PERSISTENCE-004] Idempotent schema apply for shipped SQL.
"""

from __future__ import annotations

from agent.migrations.schema import (
    apply_observability_schema,
    iter_observability_statements,
    observability_ddl_text,
)


def test_observability_ddl_text_nonempty() -> None:
    assert "CREATE SCHEMA" in observability_ddl_text()
    assert "hosted_agents" in observability_ddl_text()


def test_iter_observability_statements_splits() -> None:
    stmts = iter_observability_statements()
    assert len(stmts) >= 5
    assert any("CREATE SCHEMA" in s for s in stmts)


def test_apply_observability_schema_executes() -> None:
    executed: list[str] = []

    class Cur:
        def execute(self, q: str, p: object | None = None) -> None:
            executed.append(q.strip())

        def close(self) -> None:
            return None

    class Conn:
        def cursor(self) -> Cur:
            return Cur()

    apply_observability_schema(Conn())
    assert len(executed) == len(iter_observability_statements())
