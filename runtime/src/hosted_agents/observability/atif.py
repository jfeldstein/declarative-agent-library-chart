"""ATIF-oriented export and positive-feedback mining (schema version pinned in output)."""

from __future__ import annotations

import hashlib
from typing import Any

from hosted_agents.observability.trajectory import CanonicalTrajectory, TrajectoryStep

DEFAULT_ATIF_SCHEMA_VERSION = "atif-0.1-placeholder"


def _redact(obj: Any, blocklist_keys: set[str]) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            ks = str(k)
            if ks.lower() in blocklist_keys:
                out[ks] = "[REDACTED]"
            else:
                out[ks] = _redact(v, blocklist_keys)
        return out
    if isinstance(obj, list):
        return [_redact(x, blocklist_keys) for x in obj]
    return obj


def export_atif_batch(
    trajectories: list[CanonicalTrajectory],
    *,
    schema_version: str = DEFAULT_ATIF_SCHEMA_VERSION,
    redact_keys: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Emit ATIF-shaped documents (placeholder schema) for operator export jobs."""

    keys = redact_keys or {"password", "token", "secret", "authorization"}
    out: list[dict[str, Any]] = []
    for tr in trajectories:
        steps_out: list[dict[str, Any]] = []
        for s in tr.steps:
            steps_out.append(
                {
                    "kind": s.kind,
                    "created_at": s.created_at,
                    "payload": _redact(s.payload, keys),
                }
            )
        out.append(
            {
                "schema_version": schema_version,
                "run_id": tr.run_id,
                "thread_id": tr.thread_id,
                "steps": steps_out,
            }
        )
    return out


def _feedback_scalar(step: TrajectoryStep) -> int | None:
    if step.kind != "human_feedback":
        return None
    label = str(step.payload.get("label_id") or "")
    scalar = step.payload.get("scalar")
    if isinstance(scalar, int):
        return scalar
    if label == "positive":
        return 1
    if label == "negative":
        return -1
    return None


def positive_mining_filter(
    tr: CanonicalTrajectory,
    *,
    allow_negative_terminal: bool = False,
    contrastive: bool = False,
) -> CanonicalTrajectory | None:
    """Default positive mining: drop trajectories with negative labeled feedback."""

    fb_steps = [s for s in tr.steps if _feedback_scalar(s) is not None]
    if not fb_steps:
        return None
    scalars = [_feedback_scalar(s) for s in fb_steps]
    assert scalars  # for type checkers
    if contrastive:
        return tr
    if any(s < 0 for s in scalars if s is not None):
        return None
    if not allow_negative_terminal and scalars[-1] is not None and scalars[-1] < 0:
        return None
    return tr


def hash_tag_value(value: str, *, prefix: str = "h") -> str:
    """Stable short hash for high-cardinality or sensitive tag values."""

    digest = hashlib.sha256(value.encode()).hexdigest()[:12]
    return f"{prefix}_{digest}"
