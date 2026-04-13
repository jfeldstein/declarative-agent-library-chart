"""ATIF (Agent Trajectory Interchange Format) export via canonical trajectory adapter.

The interchange pin is **ATIF v1.4** as documented by Harbor (Laude Institute):
https://www.harborframework.com/docs/agents/trajectory-format

The runtime keeps an internal step shape (:class:`CanonicalTrajectory`); this module
maps it to ATIF JSON. Optional validation with Harbor's ``TrajectoryValidator`` is
a documented follow-up (ADR 0003).
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from typing import Any

from hosted_agents.observability.trajectory import CanonicalTrajectory, TrajectoryStep

# Pin per Harbor docs: https://www.harborframework.com/docs/agents/trajectory-format
DEFAULT_ATIF_SCHEMA_VERSION = "ATIF-v1.4"

# Internal source-of-truth step semantics before ATIF mapping (provenance in export ``extra``).
CANONICAL_TRAJECTORY_FORMAT_VERSION = "hosted-agents-canonical-v1"


def _iso8601_z(epoch_s: float) -> str:
    return datetime.fromtimestamp(epoch_s, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


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


def _agent_block() -> dict[str, Any]:
    name = os.environ.get("HOSTED_AGENT_ATIF_AGENT_NAME", "").strip() or "config-first-hosted-agents"
    version = os.environ.get("HOSTED_AGENT_ATIF_AGENT_VERSION", "").strip() or "0.1.0"
    model = os.environ.get("HOSTED_AGENT_ATIF_MODEL_NAME", "").strip() or "unknown"
    return {"name": name, "version": version, "model_name": model}


def _step_to_atif(step_id: int, s: TrajectoryStep, *, keys: set[str]) -> dict[str, Any]:
    pl = _redact(s.payload, keys)
    ts = _iso8601_z(s.created_at)

    if s.kind == "tool":
        tool = str(pl.get("tool") or "tool")
        tcid = str(pl.get("tool_call_id") or f"call_{step_id}")
        result = pl.get("result")
        content: str
        try:
            content = json.dumps(result, default=str)
        except TypeError:
            content = str(result)
        return {
            "step_id": step_id,
            "timestamp": ts,
            "source": "agent",
            "message": "",
            "tool_calls": [
                {
                    "tool_call_id": tcid,
                    "function_name": tool,
                    "arguments": pl.get("arguments")
                    if isinstance(pl.get("arguments"), dict)
                    else {},
                }
            ],
            "observation": {
                "results": [{"source_call_id": tcid, "content": content}],
            },
        }

    if s.kind == "human_feedback":
        return {
            "step_id": step_id,
            "timestamp": ts,
            "source": "system",
            "message": "human_feedback",
            "extra": {"hosted_agents": {"kind": "human_feedback", "payload": pl}},
        }

    return {
        "step_id": step_id,
        "timestamp": ts,
        "source": "system",
        "message": s.kind,
        "extra": {"hosted_agents": {"kind": s.kind, "payload": pl}},
    }


def canonical_to_atif_v1_4(
    tr: CanonicalTrajectory,
    *,
    schema_version: str = DEFAULT_ATIF_SCHEMA_VERSION,
    redact_keys: set[str] | None = None,
) -> dict[str, Any]:
    """Map a :class:`CanonicalTrajectory` to a single ATIF v1.4 trajectory document."""

    keys = redact_keys or {"password", "token", "secret", "authorization"}
    steps_out: list[dict[str, Any]] = []
    for i, s in enumerate(tr.steps, start=1):
        steps_out.append(_step_to_atif(i, s, keys=keys))

    n = len(steps_out)
    return {
        "schema_version": schema_version,
        "session_id": tr.run_id,
        "agent": _agent_block(),
        "steps": steps_out,
        "final_metrics": {
            "total_steps": n,
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_cached_tokens": 0,
            "total_cost_usd": 0.0,
        },
        "extra": {
            "hosted_agents": {
                "canonical_format": CANONICAL_TRAJECTORY_FORMAT_VERSION,
                "thread_id": tr.thread_id,
                "run_id": tr.run_id,
            }
        },
    }


def export_atif_batch(
    trajectories: list[CanonicalTrajectory],
    *,
    schema_version: str = DEFAULT_ATIF_SCHEMA_VERSION,
    redact_keys: set[str] | None = None,
) -> list[dict[str, Any]]:
    """Emit one ATIF v1.4 trajectory document per :class:`CanonicalTrajectory`."""

    return [
        canonical_to_atif_v1_4(tr, schema_version=schema_version, redact_keys=redact_keys)
        for tr in trajectories
    ]


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
