"""Feature flags and integration settings (env-driven, ConfigMap-friendly)."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass


def _truthy(key: str, default: bool = False) -> bool:
    raw = os.environ.get(key)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _json_obj(key: str) -> dict | None:
    raw = os.environ.get(key, "").strip()
    if not raw:
        return None
    data = json.loads(raw)
    if not isinstance(data, dict):
        msg = f"{key} must be a JSON object"
        raise ValueError(msg)
    return data


@dataclass(frozen=True)
class ObservabilitySettings:
    """Layered feature flags (see ``docs/runbook-checkpointing-wandb.md``)."""

    checkpoints_enabled: bool
    checkpoint_backend: str
    checkpoint_postgres_url: str | None
    wandb_enabled: bool
    slack_feedback_enabled: bool
    atif_export_enabled: bool
    shadow_enabled: bool
    wandb_project: str | None
    wandb_entity: str | None
    slack_emoji_map: dict[str, str]
    shadow_sample_rate: float
    shadow_allow_tenants: frozenset[str]
    operational_mapper_flags: dict[str, bool]

    @classmethod
    def from_env(cls) -> ObservabilitySettings:
        emoji_raw = _json_obj("HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON")
        emoji_map: dict[str, str] = {}
        if emoji_raw:
            for k, v in emoji_raw.items():
                if isinstance(k, str) and isinstance(v, str):
                    emoji_map[k] = v
        mapper_raw = _json_obj("HOSTED_AGENT_OPERATIONAL_MAPPER_FLAGS_JSON") or {}
        mappers: dict[str, bool] = {}
        for k, v in mapper_raw.items():
            if isinstance(k, str) and isinstance(v, bool):
                mappers[k] = v
        tenants_raw = os.environ.get("HOSTED_AGENT_SHADOW_ALLOW_TENANTS_JSON", "").strip()
        tenants: set[str] = set()
        if tenants_raw:
            data = json.loads(tenants_raw)
            if isinstance(data, list):
                tenants = {str(x) for x in data}
        rate_raw = os.environ.get("HOSTED_AGENT_SHADOW_SAMPLE_RATE", "0").strip()
        try:
            rate = float(rate_raw)
        except ValueError:
            rate = 0.0
        rate = max(0.0, min(1.0, rate))
        return cls(
            checkpoints_enabled=_truthy("HOSTED_AGENT_CHECKPOINTS_ENABLED"),
            checkpoint_backend=os.environ.get(
                "HOSTED_AGENT_CHECKPOINT_BACKEND", "memory"
            ).strip()
            or "memory",
            checkpoint_postgres_url=(
                os.environ.get("HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", "").strip() or None
            ),
            wandb_enabled=_truthy("HOSTED_AGENT_WANDB_ENABLED"),
            slack_feedback_enabled=_truthy("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED"),
            atif_export_enabled=_truthy("HOSTED_AGENT_ATIF_EXPORT_ENABLED"),
            shadow_enabled=_truthy("HOSTED_AGENT_SHADOW_ENABLED"),
            wandb_project=os.environ.get("WANDB_PROJECT", "").strip() or None,
            wandb_entity=os.environ.get("WANDB_ENTITY", "").strip() or None,
            slack_emoji_map=emoji_map,
            shadow_sample_rate=rate,
            shadow_allow_tenants=frozenset(tenants),
            operational_mapper_flags=mappers,
        )
