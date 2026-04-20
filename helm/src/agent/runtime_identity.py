"""Resolve per-run identity once at trigger entry (ADR 0016).

Canonical ``HOSTED_AGENT_*`` / alias precedence for labeling lives here only.
Downstream code reads :class:`RunIdentity` on :class:`~agent.trigger_context.TriggerContext`
or durable correlation — not scattered ``os.environ`` lookups for these fields.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from agent.agent_models import TriggerBody


def _first_nonempty_env(*keys: str) -> str | None:
    for k in keys:
        v = os.environ.get(k, "").strip()
        if v:
            return v
    return None


def _skill_id_from_body(body: TriggerBody | None) -> str | None:
    if body is None:
        return None
    if body.load_skill and str(body.load_skill).strip():
        return str(body.load_skill).strip()
    if body.tool and str(body.tool).strip():
        return str(body.tool).strip()
    return None


def resolve_rollout_arm_from_env() -> str:
    return _first_nonempty_env("HOSTED_AGENT_ROLLOUT_ARM") or "primary"


@dataclass(frozen=True)
class RunIdentity:
    """Neutral run facts for metrics, tracing, and durable correlation (vendor-agnostic)."""

    agent_id: str | None = None
    environment: str | None = None
    skill_id: str | None = None
    skill_version: str | None = None
    model_id: str | None = None
    prompt_hash: str | None = None
    rollout_arm: str = "primary"

    def as_flat_str_dict(self) -> dict[str, str]:
        """String map for lifecycle event payloads (omit unset keys)."""

        out: dict[str, str] = {}
        if self.agent_id:
            out["agent_id"] = self.agent_id
        if self.environment:
            out["environment"] = self.environment
        if self.skill_id:
            out["skill_id"] = self.skill_id
        if self.skill_version:
            out["skill_version"] = self.skill_version
        if self.model_id:
            out["model_id"] = self.model_id
        if self.prompt_hash:
            out["prompt_hash"] = self.prompt_hash
        if self.rollout_arm:
            out["rollout_arm"] = self.rollout_arm
        return out


def resolve_run_identity(*, body: TriggerBody | None) -> RunIdentity:
    """Resolve identity from env and trigger body (single precedence rule)."""

    env_skill = _first_nonempty_env("HOSTED_AGENT_SKILL_ID")
    body_skill = _skill_id_from_body(body)
    skill_id = body_skill or env_skill

    return RunIdentity(
        agent_id=_first_nonempty_env("HOSTED_AGENT_ID", "HOSTED_AGENT_AGENT_ID"),
        environment=_first_nonempty_env("HOSTED_AGENT_ENV", "ENVIRONMENT", "ENV"),
        skill_id=skill_id,
        skill_version=_first_nonempty_env("HOSTED_AGENT_SKILL_VERSION"),
        model_id=_first_nonempty_env(
            "HOSTED_AGENT_CHAT_MODEL", "HOSTED_AGENT_MODEL_ID"
        ),
        prompt_hash=_first_nonempty_env("HOSTED_AGENT_PROMPT_HASH"),
        rollout_arm=resolve_rollout_arm_from_env(),
    )


def run_identity_from_flat_dict(data: dict[str, object] | None) -> RunIdentity | None:
    """Restore :class:`RunIdentity` from JSON/dict (e.g. Postgres ``run_identity``)."""

    if data is None:
        return None
    if not data:
        return RunIdentity()

    def s(key: str) -> str | None:
        raw = data.get(key)
        if raw is None:
            return None
        t = str(raw).strip()
        return t or None

    ra = s("rollout_arm")
    return RunIdentity(
        agent_id=s("agent_id"),
        environment=s("environment"),
        skill_id=s("skill_id"),
        skill_version=s("skill_version"),
        model_id=s("model_id"),
        prompt_hash=s("prompt_hash"),
        rollout_arm=ra or "primary",
    )
