"""Resolve mandatory W&B run tags from env without importing :class:`TriggerContext` (import cycle)."""

from __future__ import annotations

import os

from hosted_agents.observability.wandb_trace import WandbTraceSession


def _first_nonempty_env(*keys: str) -> str | None:
    for k in keys:
        v = os.environ.get(k, "").strip()
        if v:
            return v
    return None


def resolve_rollout_arm() -> str:
    """Rollout arm tag: ``HOSTED_AGENT_ROLLOUT_ARM`` or ``primary``."""
    return _first_nonempty_env("HOSTED_AGENT_ROLLOUT_ARM") or "primary"


def _skill_id_for_tags(ctx: object | None) -> str | None:
    """Prefer trigger body ``load_skill`` / ``tool``, else ``HOSTED_AGENT_SKILL_ID``."""
    env_skill = _first_nonempty_env("HOSTED_AGENT_SKILL_ID")
    if ctx is None:
        return env_skill
    body = getattr(ctx, "body", None)
    if body is None:
        return env_skill
    load_skill = getattr(body, "load_skill", None)
    if load_skill and str(load_skill).strip():
        return str(load_skill).strip()
    tool = getattr(body, "tool", None)
    if tool and str(tool).strip():
        return str(tool).strip()
    return env_skill


def wandb_mandatory_tags_for_run(
    *,
    thread_id: str,
    ctx: object | None = None,
    request_correlation_id: str | None = None,
    rollout_arm: str | None = None,
) -> dict[str, str]:
    """Resolve mandatory W&B tags from env and optional trigger-like ``ctx``."""

    arm = rollout_arm if rollout_arm is not None else resolve_rollout_arm()
    rid = request_correlation_id
    if rid is None and ctx is not None:
        raw = getattr(ctx, "request_id", None)
        rid = raw if isinstance(raw, str) and raw.strip() else None

    agent_id = _first_nonempty_env("HOSTED_AGENT_ID", "HOSTED_AGENT_AGENT_ID")
    environment = _first_nonempty_env("HOSTED_AGENT_ENV", "ENVIRONMENT", "ENV")
    skill_id = _skill_id_for_tags(ctx)
    skill_version = _first_nonempty_env("HOSTED_AGENT_SKILL_VERSION")
    model_id = _first_nonempty_env("HOSTED_AGENT_CHAT_MODEL", "HOSTED_AGENT_MODEL_ID")
    prompt_hash = _first_nonempty_env("HOSTED_AGENT_PROMPT_HASH")

    return WandbTraceSession.mandatory_tags(
        agent_id=agent_id,
        environment=environment,
        skill_id=skill_id,
        skill_version=skill_version,
        model_id=model_id,
        prompt_hash=prompt_hash,
        rollout_arm=arm,
        thread_id=thread_id,
        request_correlation_id=rid,
    )
