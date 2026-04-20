"""Subscribe to lifecycle events and forward to :class:`WandbTraceSession`."""

from __future__ import annotations

import time
from typing import Any, Mapping

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.observability.plugins.wandb.trace import WandbTraceSession
from agent.observability.plugins_config import ObservabilityPluginsConfig
from agent.observability.run_context import get_wandb_session, set_wandb_session
from agent.observability.settings import ObservabilitySettings
from agent.observability.wandb_run_tags import wandb_mandatory_tags_from_run_identity
from agent.runtime_identity import RunIdentity, run_identity_from_flat_dict


def register_wandb_trace_plugin(
    bus: SyncEventBus, _cfg: ObservabilityPluginsConfig | None = None
) -> None:
    """Wire W&B tracing to standard lifecycle events (agent process only)."""

    bus.subscribe(EventName.RUN_STARTED, _on_run_started)
    bus.subscribe(EventName.RUN_ENDED, _on_run_ended)
    bus.subscribe(EventName.TOOL_CALL_COMPLETED, _on_tool_call_completed)
    bus.subscribe(EventName.FEEDBACK_RECORDED, _on_feedback_recorded)


def _wandb_tags_from_payload(p: Mapping[str, Any]) -> dict[str, str]:
    """Build W&B mandatory tags from neutral lifecycle payload fields (ADR 0016)."""

    raw = p.get("run_identity")
    data = raw if isinstance(raw, dict) else {}
    ri = run_identity_from_flat_dict({str(k): v for k, v in data.items()})
    if ri is None:
        ri = RunIdentity()
    tid = str(p.get("thread_id") or "")
    rid_raw = p.get("request_correlation_id")
    rc = str(rid_raw).strip() if rid_raw is not None else ""
    return wandb_mandatory_tags_from_run_identity(
        ri,
        thread_id=tid,
        request_correlation_id=rc or None,
    )


def _on_run_started(event: LifecycleEvent) -> None:
    p = event.payload
    obs = p.get("observability")
    if not isinstance(obs, ObservabilitySettings):
        return
    run_id = str(p.get("run_id") or "")
    tags = _wandb_tags_from_payload(p)
    run_name = run_id or str(p.get("run_name") or "")
    if obs.wandb_enabled:
        sess = WandbTraceSession(settings=obs, run_name=run_name, tags=dict(tags))
        set_wandb_session(sess)
    else:
        set_wandb_session(None)


def _on_run_ended(_event: LifecycleEvent) -> None:
    sess = get_wandb_session()
    if sess is None:
        return
    try:
        sess.finish()
    finally:
        set_wandb_session(None)


def _duration_s(payload: dict[str, Any]) -> float:
    if payload.get("duration_s") is not None:
        return float(payload["duration_s"])
    return time.perf_counter() - float(payload["started_at"])


def _on_tool_call_completed(event: LifecycleEvent) -> None:
    sess = get_wandb_session()
    if sess is None:
        return
    p = event.payload
    tc = p.get("tool_call_id")
    if tc is None or str(tc).strip() == "":
        return
    sess.log_tool_span(
        tool_call_id=str(tc),
        tool_name=str(p["tool"]),
        duration_s=_duration_s(p),
    )


def _on_feedback_recorded(event: LifecycleEvent) -> None:
    p = event.payload
    settings = p.get("observability_settings")
    if not isinstance(settings, ObservabilitySettings) or not settings.wandb_enabled:
        return
    run_id = str(p.get("run_id") or "")
    tags = _wandb_tags_from_payload(p)
    late = WandbTraceSession(settings=settings, run_name=run_id, tags=tags)
    try:
        late.log_feedback(
            tool_call_id=str(p["tool_call_id"]),
            checkpoint_id=p.get("checkpoint_id"),
            feedback_label=str(p["feedback_label"]),
            feedback_source=str(p["feedback_source"]),
        )
    finally:
        late.finish()
