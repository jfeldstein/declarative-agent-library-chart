"""Cursor persistence backends for scraper incremental state.

Traceability: [DALC-REQ-SCRAPER-CURSOR-001] [DALC-REQ-SCRAPER-CURSOR-002]
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path

import psycopg


def _safe_scope(scope: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "_", scope)[:80]


class CursorStore:
    def get_state(self, integration: str, scope: str, key: str) -> str | None:
        raise NotImplementedError

    def set_state(self, integration: str, scope: str, key: str, value: str) -> None:
        raise NotImplementedError


class FileCursorStore(CursorStore):
    """Compatibility adapter for existing Jira/Slack on-disk cursor files."""

    def _jira_path(self, scope: str, key: str) -> Path:
        root = Path(os.environ.get("JIRA_WATERMARK_DIR", "/tmp/jira-scraper-watermark").strip())
        root.mkdir(parents=True, exist_ok=True)
        qhash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
        return root / f"watermark-{_safe_scope(scope)}-{qhash}.json"

    def _slack_path(self, scope: str, key: str) -> Path:
        root = Path(os.environ.get("SLACK_STATE_DIR", "/tmp/slack-scraper-state").strip())
        root.mkdir(parents=True, exist_ok=True)
        return root / f"{_safe_scope(scope)}-{key}.json"

    def _generic_path(self, integration: str, scope: str, key: str) -> Path:
        root = Path(os.environ.get("SCRAPER_CURSOR_DIR", "/tmp/scraper-cursor-state").strip())
        root.mkdir(parents=True, exist_ok=True)
        khash = hashlib.sha256(key.encode("utf-8")).hexdigest()[:24]
        return root / f"{integration}-{_safe_scope(scope)}-{khash}.json"

    def _path(self, integration: str, scope: str, key: str) -> Path:
        if integration == "jira":
            return self._jira_path(scope, key)
        if integration == "slack":
            return self._slack_path(scope, key)
        return self._generic_path(integration, scope, key)

    def get_state(self, integration: str, scope: str, key: str) -> str | None:
        path = self._path(integration, scope, key)
        if not path.is_file():
            return None
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if not isinstance(data, dict):
            return None
        if integration == "jira":
            v = data.get("last_updated")
        elif integration == "slack":
            v = data.get("watermark_ts")
        else:
            v = data.get("value")
        return str(v).strip() if v is not None and str(v).strip() else None

    def set_state(self, integration: str, scope: str, key: str, value: str) -> None:
        path = self._path(integration, scope, key)
        if integration == "jira":
            payload: dict[str, str] = {"last_updated": value}
        elif integration == "slack":
            payload = {"watermark_ts": value}
        else:
            payload = {"value": value}
        path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


class PostgresCursorStore(CursorStore):
    def __init__(self, dsn: str):
        self._dsn = dsn
        self._ddl_ready = False

    def _key_hash(self, key: str) -> str:
        return hashlib.sha256(key.encode("utf-8")).hexdigest()

    def _ensure_table(self) -> None:
        if self._ddl_ready:
            return
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS scraper_cursor_state (
                        integration TEXT NOT NULL,
                        scope TEXT NOT NULL,
                        key_hash TEXT NOT NULL,
                        logical_key TEXT NOT NULL,
                        value TEXT NOT NULL,
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        PRIMARY KEY (integration, scope, key_hash)
                    )
                    """
                )
        self._ddl_ready = True

    def get_state(self, integration: str, scope: str, key: str) -> str | None:
        self._ensure_table()
        kh = self._key_hash(key)
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT value
                    FROM scraper_cursor_state
                    WHERE integration = %s AND scope = %s AND key_hash = %s
                    """,
                    (integration, scope, kh),
                )
                row = cur.fetchone()
        if not row:
            return None
        value = row[0]
        return str(value) if value is not None else None

    def set_state(self, integration: str, scope: str, key: str, value: str) -> None:
        self._ensure_table()
        kh = self._key_hash(key)
        with psycopg.connect(self._dsn, autocommit=True) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO scraper_cursor_state (integration, scope, key_hash, logical_key, value)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (integration, scope, key_hash)
                    DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                    """,
                    (integration, scope, kh, key[:512], value),
                )


def cursor_store_from_env() -> CursorStore:
    backend = os.environ.get("SCRAPER_CURSOR_BACKEND", "file").strip().lower() or "file"
    if backend != "postgres":
        return FileCursorStore()
    dsn = os.environ.get("SCRAPER_POSTGRES_URL", "").strip() or os.environ.get(
        "HOSTED_AGENT_POSTGRES_URL", ""
    ).strip()
    if not dsn:
        raise RuntimeError(
            "SCRAPER_CURSOR_BACKEND=postgres requires SCRAPER_POSTGRES_URL or HOSTED_AGENT_POSTGRES_URL"
        )
    return PostgresCursorStore(dsn)
