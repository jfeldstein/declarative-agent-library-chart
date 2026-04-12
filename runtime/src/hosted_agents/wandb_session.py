"""Optional Weights & Biases run lifecycle for trigger invocations."""

from __future__ import annotations

import os
from contextlib import contextmanager
from contextvars import ContextVar, Token
from typing import Any, Generator

from hosted_agents.agent_tracing import wandb_tracing_ready
from hosted_agents.trigger_context import TriggerContext

_wandb_run_id: ContextVar[str | None] = ContextVar("wandb_run_id", default=None)


def active_wandb_run_id() -> str | None:
    return _wandb_run_id.get()


def _tag_dict_for_run(ctx: TriggerContext) -> dict[str, str]:
    """Bounded tag/config values only (no free-text blobs)."""

    def pick(*keys: str) -> str | None:
        for k in keys:
            v = os.environ.get(k, "").strip()
            if v:
                return v
        return None

    tags: dict[str, str] = {}
    if v := pick("HOSTED_AGENT_ID", "HOSTED_AGENT_AGENT_ID"):
        tags["agent_id"] = v
    if v := pick("HOSTED_AGENT_ENV", "ENVIRONMENT", "ENV"):
        tags["environment"] = v
    if v := pick("HOSTED_AGENT_SKILL_ID"):
        tags["skill_id"] = v
    if v := pick("HOSTED_AGENT_SKILL_VERSION"):
        tags["skill_version"] = v
    if v := pick("HOSTED_AGENT_CHAT_MODEL", "HOSTED_AGENT_MODEL_ID"):
        tags["model_id"] = v
    if v := pick("HOSTED_AGENT_PROMPT_HASH"):
        tags["prompt_hash"] = v
    tags["thread_id"] = ctx.thread_id
    tags["run_id"] = ctx.run_id
    return {k: v for k, v in tags.items() if v}


@contextmanager
def wandb_run_scope(ctx: TriggerContext) -> Generator[dict[str, Any] | None, None, None]:
    """Start/finish a W&B run when tracing is fully configured; else yield ``None``."""
    token: Token | None = None
    if not wandb_tracing_ready():
        yield None
        return
    try:
        import wandb
    except ImportError:
        yield None
        return

    wb = wandb
    project = (
        os.environ.get("WANDB_PROJECT", "").strip()
        or os.environ.get("HOSTED_AGENT_WANDB_PROJECT", "").strip()
    )
    entity = os.environ.get("WANDB_ENTITY", "").strip() or None
    tags = _tag_dict_for_run(ctx)
    run = wb.init(
        project=project,
        entity=entity,
        id=ctx.run_id,
        name=ctx.run_id[:120],
        config={k: v for k, v in tags.items() if v},
        reinit=True,
    )
    meta = {
        "wandb_run_id": getattr(run, "id", None) or ctx.run_id,
        "wandb_project": project,
        "wandb_entity": entity,
    }
    token = _wandb_run_id.set(str(meta["wandb_run_id"]))
    try:
        yield meta
    finally:
        try:
            wb.finish()
        except Exception:
            pass
        if token is not None:
            _wandb_run_id.reset(token)
