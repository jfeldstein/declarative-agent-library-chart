"""Build mandatory W&B tag dicts from neutral :class:`~agent.runtime_identity.RunIdentity`.

Used by integration tests and optional legacy call sites; the trigger pipeline publishes
neutral ``run_identity`` facts on the lifecycle bus — see ADR 0016.
"""

from __future__ import annotations

from dataclasses import replace

from agent.observability.plugins.wandb.trace import WandbTraceSession
from agent.runtime_identity import RunIdentity, resolve_run_identity


def wandb_mandatory_tags_from_run_identity(
    ri: RunIdentity,
    *,
    thread_id: str,
    request_correlation_id: str | None = None,
) -> dict[str, str]:
    """Map neutral identity facts to W&B mandatory tags (plugin-side interpretation)."""

    return WandbTraceSession.mandatory_tags(
        agent_id=ri.agent_id,
        environment=ri.environment,
        skill_id=ri.skill_id,
        skill_version=ri.skill_version,
        model_id=ri.model_id,
        prompt_hash=ri.prompt_hash,
        rollout_arm=ri.rollout_arm,
        thread_id=thread_id,
        request_correlation_id=request_correlation_id,
    )


def wandb_mandatory_tags_for_run(
    *,
    thread_id: str,
    ctx: object | None = None,
    request_correlation_id: str | None = None,
    rollout_arm: str | None = None,
    run_identity: RunIdentity | None = None,
) -> dict[str, str]:
    """Resolve tags from an explicit identity, ``ctx.run_identity``, or env + body."""

    ri: RunIdentity | None = run_identity
    if ri is None and ctx is not None:
        ri = getattr(ctx, "run_identity", None)
    if ri is None:
        ri = resolve_run_identity(
            body=getattr(ctx, "body", None) if ctx is not None else None,
        )
    if rollout_arm is not None:
        ri = replace(ri, rollout_arm=rollout_arm)
    rid = request_correlation_id
    if rid is None and ctx is not None:
        raw = getattr(ctx, "request_id", None)
        rid = raw if isinstance(raw, str) and raw.strip() else None

    return wandb_mandatory_tags_from_run_identity(
        ri, thread_id=thread_id, request_correlation_id=rid
    )
