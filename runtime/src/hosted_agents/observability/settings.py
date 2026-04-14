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
    checkpoint_postgres_pool_max: int
    observability_store: str
    observability_postgres_url: str | None
    observability_postgres_pool_max: int
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
        tenants_raw = os.environ.get(
            "HOSTED_AGENT_SHADOW_ALLOW_TENANTS_JSON", ""
        ).strip()
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
        cp_pool_raw = os.environ.get(
            "HOSTED_AGENT_CHECKPOINT_POSTGRES_POOL_MAX", "5"
        ).strip()
        try:
            cp_pool = max(1, min(50, int(cp_pool_raw or "5")))
        except ValueError:
            cp_pool = 5
        obs_pool_raw = os.environ.get(
            "HOSTED_AGENT_OBSERVABILITY_POSTGRES_POOL_MAX", "5"
        ).strip()
        try:
            obs_pool = max(1, min(50, int(obs_pool_raw or "5")))
        except ValueError:
            obs_pool = 5
        obs_store = (
            os.environ.get("HOSTED_AGENT_OBSERVABILITY_STORE", "memory").strip().lower()
            or "memory"
        )
        if obs_store not in {"memory", "postgres"}:
            msg = f"unknown HOSTED_AGENT_OBSERVABILITY_STORE={obs_store!r}"
            raise ValueError(msg)
        obs_pg_url = (
            os.environ.get("HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL", "").strip()
            or None
        )
        return cls(
            checkpoints_enabled=_truthy("HOSTED_AGENT_CHECKPOINTS_ENABLED"),
            checkpoint_backend=os.environ.get(
                "HOSTED_AGENT_CHECKPOINT_BACKEND", "memory"
            ).strip()
            or "memory",
            checkpoint_postgres_url=(
                os.environ.get("HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", "").strip()
                or postgres_url()
                or None
            ),
            checkpoint_postgres_pool_max=cp_pool,
            observability_store=obs_store,
            observability_postgres_url=obs_pg_url,
            observability_postgres_pool_max=obs_pool,
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

    def effective_observability_postgres_url(self) -> str | None:
        """URL for application observability tables (may fall back to checkpoint URL)."""

        if self.observability_postgres_url:
            return self.observability_postgres_url
        if self.observability_store == "postgres" and self.checkpoint_postgres_url:
            return self.checkpoint_postgres_url
        return None
