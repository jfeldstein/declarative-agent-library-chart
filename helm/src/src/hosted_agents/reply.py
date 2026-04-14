"""Map configured system prompt to a plain-text trigger response."""

from __future__ import annotations

import re

_RESPOND_PATTERN = re.compile(
    r'Respond\s*,\s*["\x27](?P<body>.+?)["\x27]',
    re.IGNORECASE | re.DOTALL,
)


def trigger_reply_text(system_prompt: str) -> str:
    """Return the HTTP body for POST /api/v1/trigger.

    If the prompt contains a line like ``Respond, "Hello :wave:"`` (single or double
    quotes), returns the inner literal. Otherwise returns the stripped prompt.
    """
    stripped = system_prompt.strip()
    if not stripped:
        msg = "system prompt is required"
        raise ValueError(msg)
    match = _RESPOND_PATTERN.search(stripped)
    if match:
        return match.group("body").strip()
    return stripped
