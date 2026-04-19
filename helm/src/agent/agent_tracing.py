"""Observability summary for W&B traces and checkpoint linkage.

OpenSpec: ``wandb-agent-traces``. W&B init lives in :mod:`agent.wandb_session`;
checkpointer selection in :mod:`agent.checkpointing`.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from agent.checkpointing import (
    checkpoints_globally_enabled,
    effective_checkpoint_store,
)

# Canonical keys per openspec/changes/agent-checkpointing-wandb-feedback/specs/wandb-agent-traces/spec.md
MANDATORY_WANDB_TAG_KEYS: tuple[str, ...] = (
    "agent_id",
    "environment",
    "skill_id",
    "skill_version",
    "model_id",
    "prompt_hash",
    "thread_id",
)

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_truthy(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in _TRUTHY


@dataclass(frozen=True)
class WandbTraceStubConfig:
    """Non-secret W&B-related config snapshot for operators."""

    tracing_enabled_intent: bool
    api_key_configured: bool
    project: str | None
    entity: str | None


def wandb_trace_stub_config() -> WandbTraceStubConfig:
    key = os.environ.get("WANDB_API_KEY", "").strip()
    proj = (
        os.environ.get("WANDB_PROJECT", "").strip()
        or os.environ.get("HOSTED_AGENT_WANDB_PROJECT", "").strip()
        or None
    )
    ent = os.environ.get("WANDB_ENTITY", "").strip() or None
    return WandbTraceStubConfig(
        tracing_enabled_intent=_env_truthy("HOSTED_AGENT_WANDB_ENABLED"),
        api_key_configured=bool(key),
        project=proj,
        entity=ent,
    )


def wandb_tracing_ready(cfg: WandbTraceStubConfig | None = None) -> bool:
    """True when intent flag, API key, and project are all present (still no SDK init)."""
    c = cfg or wandb_trace_stub_config()
    return c.tracing_enabled_intent and c.api_key_configured and bool(c.project)


def checkpoint_store_kind() -> str:
    """Effective ``HOSTED_AGENT_CHECKPOINT_STORE`` (default ``memory``)."""
    return effective_checkpoint_store()


def observability_summary() -> dict[str, object]:
    """Shape returned under ``observability`` in ``GET /api/v1/runtime/summary``."""
    wb = wandb_trace_stub_config()
    return {
        "checkpoint_store": checkpoint_store_kind(),
        "feature_flags": {
            "checkpoints_enabled": checkpoints_globally_enabled(),
            "slack_feedback_enabled": _env_truthy(
                "HOSTED_AGENT_SLACK_FEEDBACK_ENABLED"
            ),
        },
        "wandb": {
            "tracing_enabled_intent": wb.tracing_enabled_intent,
            "tracing_ready": wandb_tracing_ready(wb),
            "project": wb.project,
            "entity": wb.entity,
            "mandatory_run_tag_keys": list(MANDATORY_WANDB_TAG_KEYS),
        },
    }
