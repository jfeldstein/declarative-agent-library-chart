"""Versioned global label registry for explicit human feedback (OpenSpec: ``agent-feedback-model``)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

_REGISTRY_PATH = (
    Path(__file__).resolve().parent / "data" / "feedback_registry.v1.json"
)


@dataclass(frozen=True)
class FeedbackRegistry:
    registry_id: str
    schema_version: str
    slack_emoji_to_label: dict[str, str]
    labels: dict[str, dict[str, Any]]


@lru_cache(maxsize=1)
def load_feedback_registry() -> FeedbackRegistry:
    """Load the bundled global registry (v1 JSON). New labels ship with registry bumps."""
    raw = _REGISTRY_PATH.read_text(encoding="utf-8")
    data = json.loads(raw)
    return FeedbackRegistry(
        registry_id=str(data["registry_id"]),
        schema_version=str(data["schema_version"]),
        slack_emoji_to_label={
            str(k).strip().lower(): str(v)
            for k, v in (data.get("slack_emoji_to_label") or {}).items()
        },
        labels={str(k): dict(v) for k, v in (data.get("labels") or {}).items()},
    )


def resolve_slack_reaction(emoji: str) -> tuple[str, str] | None:
    """Return ``(label_id, registry schema_version)`` or ``None`` if unmapped."""
    reg = load_feedback_registry()
    key = emoji.strip().strip(":").lower()
    label_id = reg.slack_emoji_to_label.get(key)
    if not label_id or label_id not in reg.labels:
        return None
    return label_id, reg.schema_version
