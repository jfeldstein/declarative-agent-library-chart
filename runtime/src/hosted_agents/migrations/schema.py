"""Load and apply bundled observability DDL (idempotent)."""

from __future__ import annotations

from importlib import resources


def observability_ddl_text() -> str:
    return (
        resources.files("hosted_agents.migrations")
        .joinpath("001_hosted_agents_observability.sql")
        .read_text(encoding="utf-8")
    )


def iter_observability_statements() -> list[str]:
    """Split SQL file on semicolon boundaries (no function bodies in this DDL)."""

    raw = observability_ddl_text()
    lines = [ln for ln in raw.splitlines() if not ln.strip().startswith("--")]
    text = "\n".join(lines)
    return [s.strip() for s in text.split(";") if s.strip()]


def apply_observability_schema(conn: object) -> None:
    """Execute DDL using an open psycopg connection (autocommit recommended)."""

    cur = conn.cursor()
    try:
        for stmt in iter_observability_statements():
            cur.execute(stmt)
    finally:
        cur.close()
