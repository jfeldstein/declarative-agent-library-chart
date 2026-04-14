"""Postgres DSN from ``HOSTED_AGENT_POSTGRES_URL``."""

from __future__ import annotations

import os


def postgres_url() -> str:
    return os.environ.get("HOSTED_AGENT_POSTGRES_URL", "").strip()
