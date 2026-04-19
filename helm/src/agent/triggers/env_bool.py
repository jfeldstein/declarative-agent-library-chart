"""Shared env parsing for trigger bridge settings."""

from __future__ import annotations

import os


def env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}
