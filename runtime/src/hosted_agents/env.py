"""Environment-backed configuration (Kubernetes ConfigMap → env)."""

from __future__ import annotations

import os

SYSTEM_PROMPT_ENV_KEY = "HOSTED_AGENT_SYSTEM_PROMPT"


def system_prompt_from_env() -> str:
    """Return the configured system prompt from the environment.

    When unset or whitespace-only, returns an empty string.
    """
    return os.environ.get(SYSTEM_PROMPT_ENV_KEY, "").strip()
