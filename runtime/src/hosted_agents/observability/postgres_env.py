"""Shared Postgres DSN from a single env var, with legacy fallbacks."""

from __future__ import annotations

import os

# Canonical: one DSN for checkpoint + observability Postgres when both use the same DB.
_POSTGRES_URL = "HOSTED_AGENT_POSTGRES_URL"
# Deprecated: still honored if ``HOSTED_AGENT_POSTGRES_URL`` is unset.
_LEGACY_CHECKPOINT = "HOSTED_AGENT_CHECKPOINT_POSTGRES_URL"
_LEGACY_OBSERVABILITY = "HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL"


def effective_postgres_url() -> str:
    """First non-empty URL among unified + legacy env keys."""

    for key in (_POSTGRES_URL, _LEGACY_CHECKPOINT, _LEGACY_OBSERVABILITY):
        v = os.environ.get(key, "").strip()
        if v:
            return v
    return ""
