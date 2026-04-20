"""Optional Weights & Biases run lifecycle for trigger invocations."""

from __future__ import annotations

import os
from contextlib import contextmanager, suppress
from contextvars import ContextVar
from typing import Any, Generator

from agent.agent_tracing import wandb_tracing_ready
from agent.trigger_context import TriggerContext

_wandb_run_id: ContextVar[str | None] = ContextVar("wandb_run_id", default=None)


def active_wandb_run_id() -> str | None:
    return _wandb_run_id.get()


def _tag_dict_for_run(ctx: TriggerContext) -> dict[str, str]:
    """Config tags from :attr:`~agent.trigger_context.TriggerContext.run_identity` (ADR 0016)."""

    tags = dict(ctx.run_identity.as_flat_str_dict())
    tags["thread_id"] = ctx.thread_id
    tags["run_id"] = ctx.run_id
    return {k: v for k, v in tags.items() if v}


@contextmanager
def wandb_run_scope(
    ctx: TriggerContext,
) -> Generator[dict[str, Any] | None, None, None]:
    """Start/finish a W&B run when tracing is fully configured; else yield ``None``."""
    if not wandb_tracing_ready():
        yield None
        return
    try:
        import wandb
    except ImportError:
        yield None
        return

    project = (
        os.environ.get("WANDB_PROJECT", "").strip()
        or os.environ.get("HOSTED_AGENT_WANDB_PROJECT", "").strip()
    )
    entity = os.environ.get("WANDB_ENTITY", "").strip() or None
    tags = _tag_dict_for_run(ctx)
    run = wandb.init(
        project=project,
        entity=entity,
        id=ctx.run_id,
        name=ctx.run_id[:120],
        config=dict(tags),
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
        with suppress(Exception):
            wandb.finish()
        _wandb_run_id.reset(token)
