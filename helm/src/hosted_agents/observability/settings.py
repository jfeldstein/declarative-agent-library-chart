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
    """Runtime integration flags (checkpoints, W&B, Slack feedback); env-driven."""

    checkpoints_enabled: bool
    checkpoint_backend: str
    checkpoint_postgres_url: str | None
    postgres_pool_max: int
    observability_store: str
    wandb_enabled: bool
    slack_feedback_enabled: bool
    wandb_project: str | None
    wandb_entity: str | None
    slack_emoji_map: dict[str, str]
    operational_mapper_flags: dict[str, bool]

    @classmethod
    def from_env(cls) -> ObservabilitySettings:
        from hosted_agents.observability.pglite_runtime import ensure_pglite_embedded
        from hosted_agents.observability.postgres_env import postgres_url

        ensure_pglite_embedded()
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
        pool_raw = os.environ.get("HOSTED_AGENT_POSTGRES_POOL_MAX", "5").strip()
        try:
            pg_pool = max(1, min(50, int(pool_raw or "5")))
        except ValueError:
            pg_pool = 5
        obs_store = (
            os.environ.get("HOSTED_AGENT_OBSERVABILITY_STORE", "memory").strip().lower()
            or "memory"
        )
        if obs_store not in {"memory", "postgres"}:
            msg = f"unknown HOSTED_AGENT_OBSERVABILITY_STORE={obs_store!r}"
            raise ValueError(msg)
        return cls(
            checkpoints_enabled=_truthy("HOSTED_AGENT_CHECKPOINTS_ENABLED"),
            checkpoint_backend=os.environ.get(
                "HOSTED_AGENT_CHECKPOINT_BACKEND", "memory"
            ).strip()
            or "memory",
            checkpoint_postgres_url=postgres_url() or None,
            postgres_pool_max=pg_pool,
            observability_store=obs_store,
            wandb_enabled=_truthy("HOSTED_AGENT_WANDB_ENABLED"),
            slack_feedback_enabled=_truthy("HOSTED_AGENT_SLACK_FEEDBACK_ENABLED"),
            wandb_project=os.environ.get("WANDB_PROJECT", "").strip() or None,
            wandb_entity=os.environ.get("WANDB_ENTITY", "").strip() or None,
            slack_emoji_map=emoji_map,
            operational_mapper_flags=mappers,
        )

    def effective_observability_postgres_url(self) -> str | None:
        """URL for observability DDL when ``observability_store`` is ``postgres``."""

        if self.observability_store != "postgres":
            return None
        return self.checkpoint_postgres_url
