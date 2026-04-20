"""Langfuse SDK bridge: lifecycle bus → traces / generations / spans / scores (Phase 2).

[DALC-REQ-LANGFUSE-TRACE-001]

[DALC-REQ-LANGFUSE-TRACE-003] PII and prompt redaction remain the responsibility of HTTP/graph
middleware and stores; this bridge records only bounded operational fields (identifiers, counts,
structured labels). See ``openspec/changes/observability-plugin-langfuse/design.md``.
"""

from __future__ import annotations

import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any

from langfuse import Langfuse, propagate_attributes

from agent.observability.events import EventName, LifecycleEvent, SyncEventBus
from agent.observability.events.types import FeedbackRecordedLifecycleEvent
from agent.observability.plugins_config import LangfusePluginSettings
from agent.observability.run_context import get_run_id, get_thread_id
from agent.trigger_context import TriggerContext


def build_langfuse_client(settings: LangfusePluginSettings) -> Langfuse | None:
    """Construct a Langfuse client when enabled and keys are present (else None)."""

    if not settings.enabled:
        return None
    public_key = settings.public_key or ""
    secret_key = settings.secret_key or ""
    host = settings.host or ""
    if not public_key or not secret_key or not host:
        return None
    kwargs: dict[str, Any] = {
        "public_key": public_key,
        "secret_key": secret_key,
        "host": host,
    }
    flush_interval = settings.flush_interval_seconds
    if flush_interval is not None and flush_interval > 0:
        kwargs["flush_interval"] = flush_interval
    return Langfuse(**kwargs)


@dataclass
class _RunMeta:
    trace_id: str
    thread_id: str
    user_id: str | None
    tags: list[str] = field(default_factory=list)


class LangfuseLifecycleBridge:
    """Subscribes to the synchronous lifecycle bus and mirrors events to Langfuse."""

    def __init__(self, client: Any) -> None:
        self._client = client
        self._runs: dict[str, _RunMeta] = {}

    def register(self, bus: SyncEventBus) -> None:
        bus.subscribe(EventName.LLM_GENERATION_FIRST_TOKEN, self._on_llm_first_token)
        bus.subscribe(EventName.LLM_GENERATION_COMPLETED, self._on_llm_completed)
        bus.subscribe(EventName.TOOL_CALL_COMPLETED, self._on_tool_completed)
        bus.subscribe(EventName.TOOL_CALL_FAILED, self._on_tool_failed)
        bus.subscribe(EventName.SKILL_LOAD_COMPLETED, self._on_skill_completed)
        bus.subscribe(EventName.SKILL_LOAD_FAILED, self._on_skill_failed)
        bus.subscribe(
            EventName.SUBAGENT_INVOCATION_COMPLETED, self._on_subagent_completed
        )
        bus.subscribe(EventName.SUBAGENT_INVOCATION_FAILED, self._on_subagent_failed)
        bus.subscribe(EventName.RAG_EMBED_COMPLETED, self._on_rag_embed)
        bus.subscribe(EventName.RAG_QUERY_COMPLETED, self._on_rag_query)
        bus.subscribe(EventName.TRIGGER_REQUEST_RESPONDED, self._on_trigger_responded)
        bus.subscribe(EventName.FEEDBACK_RECORDED, self._on_feedback_recorded)

    def _resolve_ctx(
        self, payload: Mapping[str, Any]
    ) -> tuple[str | None, TriggerContext | None]:
        ctx = payload.get("ctx")
        if isinstance(ctx, TriggerContext):
            return ctx.run_id, ctx
        rid = get_run_id()
        return (str(rid) if rid else None), None

    def _ensure_meta(self, run_id: str, tc: TriggerContext | None) -> _RunMeta:
        cur = self._runs.get(run_id)
        if cur is not None:
            if tc and tc.tenant_id and cur.user_id != tc.tenant_id:
                cur.user_id = tc.tenant_id
            return cur
        tid = self._client.create_trace_id()
        thread_id = (
            tc.thread_id if tc is not None else (get_thread_id() or "unknown-thread")
        )
        user_id = tc.tenant_id if tc is not None else None
        meta = _RunMeta(trace_id=tid, thread_id=thread_id, user_id=user_id, tags=[])
        self._runs[run_id] = meta
        return meta

    def _trace_ctx(self, meta: _RunMeta) -> dict[str, str]:
        return {"trace_id": meta.trace_id}

    def _with_attrs(self, meta: _RunMeta | None, fn: Any) -> None:
        if meta is None:
            fn()
            return
        with propagate_attributes(
            session_id=meta.thread_id,
            user_id=meta.user_id,
            tags=meta.tags or None,
            trace_name="hosted-agent-run",
        ):
            fn()

    def _on_llm_first_token(self, event: LifecycleEvent) -> None:
        p = event.payload
        run_id, tc = self._resolve_ctx(p)
        if not run_id:
            return
        meta = self._ensure_meta(run_id, tc)

        def _emit() -> None:
            obs = self._client.start_observation(
                trace_context=self._trace_ctx(meta),
                name="llm.first_token",
                as_type="span",
                metadata={"seconds": float(p.get("seconds") or 0.0)},
            )
            obs.end()

        self._with_attrs(meta, _emit)

    def _on_llm_completed(self, event: LifecycleEvent) -> None:
        p = event.payload
        run_id, tc = self._resolve_ctx(p)
        if not run_id:
            return
        meta = self._ensure_meta(run_id, tc)
        it = p.get("input_tokens")
        ot = p.get("output_tokens")
        usage: dict[str, int] = {}
        if isinstance(it, int) and it >= 0:
            usage["prompt_tokens"] = it
        if isinstance(ot, int) and ot >= 0:
            usage["completion_tokens"] = ot

        def _emit() -> None:
            gen = self._client.start_observation(
                trace_context=self._trace_ctx(meta),
                name="llm.generation",
                as_type="generation",
                model="langchain-chat",
                metadata={"result_label": str(p.get("result") or "")},
                usage_details=usage or None,
            )
            gen.update(
                output={
                    "bounded": True,
                    "note": "no raw prompt/output; middleware owns PII",
                },
            )
            gen.end()

        self._with_attrs(meta, _emit)

    def _tool_span(self, payload: Mapping[str, Any], *, ok: bool | None) -> None:
        run_id, tc = self._resolve_ctx(payload)
        if not run_id:
            return
        meta = self._ensure_meta(run_id, tc)
        tool = str(payload.get("tool") or "unknown-tool")
        started_at = float(payload.get("started_at") or time.time())

        def _emit() -> None:
            span = self._client.start_observation(
                trace_context=self._trace_ctx(meta),
                name=f"tool:{tool}",
                as_type="tool",
                input={"tool": tool, "started_at": started_at},
            )
            out: dict[str, Any] = {"ok": ok} if ok is not None else {"failed": True}
            span.update(output=out)
            span.end()

        self._with_attrs(meta, _emit)

    def _on_tool_completed(self, event: LifecycleEvent) -> None:
        p = event.payload
        ok = bool(p.get("ok", True))
        self._tool_span(p, ok=ok)

    def _on_tool_failed(self, event: LifecycleEvent) -> None:
        self._tool_span(event.payload, ok=False)

    def _simple_span(self, event: LifecycleEvent, *, name: str, field_key: str) -> None:
        p = event.payload
        run_id, tc = self._resolve_ctx(p)
        if not run_id:
            return
        meta = self._ensure_meta(run_id, tc)
        label = str(p.get(field_key) or name)

        def _emit() -> None:
            sp = self._client.start_observation(
                trace_context=self._trace_ctx(meta),
                name=name,
                as_type="span",
                input={field_key: label},
            )
            sp.end()

        self._with_attrs(meta, _emit)

    def _on_skill_completed(self, event: LifecycleEvent) -> None:
        self._simple_span(event, name="skill.load", field_key="skill")

    def _on_skill_failed(self, event: LifecycleEvent) -> None:
        self._simple_span(event, name="skill.load.failed", field_key="skill")

    def _on_subagent_completed(self, event: LifecycleEvent) -> None:
        self._simple_span(event, name="subagent.invoke", field_key="subagent")

    def _on_subagent_failed(self, event: LifecycleEvent) -> None:
        self._simple_span(event, name="subagent.invoke.failed", field_key="subagent")

    def _rag_span(self, event: LifecycleEvent, *, kind: str) -> None:
        p = event.payload
        run_id, tc = self._resolve_ctx(p)
        if not run_id:
            return
        meta = self._ensure_meta(run_id, tc)

        def _emit() -> None:
            sp = self._client.start_observation(
                trace_context=self._trace_ctx(meta),
                name=kind,
                as_type="retriever",
                input={
                    "result": str(p.get("result") or ""),
                    "elapsed_seconds": float(p.get("elapsed_seconds") or 0.0),
                },
            )
            sp.end()

        self._with_attrs(meta, _emit)

    def _on_rag_embed(self, event: LifecycleEvent) -> None:
        self._rag_span(event, kind="rag.embed")

    def _on_rag_query(self, event: LifecycleEvent) -> None:
        self._rag_span(event, kind="rag.query")

    def _on_trigger_responded(self, event: LifecycleEvent) -> None:
        """Flush batched exporter data after trigger handling; annotate trigger flavor."""

        p = event.payload
        run_id, tc = self._resolve_ctx(p)
        if run_id:
            meta = self._runs.get(run_id)
            if meta is None:
                meta = self._ensure_meta(run_id, tc)
            trig = str(p.get("trigger") or "unknown")
            tag = f"trigger:{trig}"
            if tag not in meta.tags:
                meta.tags.append(tag)

            def _emit() -> None:
                sp = self._client.start_observation(
                    trace_context=self._trace_ctx(meta),
                    name="trigger.responded",
                    as_type="span",
                    input={"trigger": trig},
                )
                sp.end()

            self._with_attrs(meta, _emit)
        try:
            self._client.flush()
        except Exception:
            return

    def _on_feedback_recorded(self, event: LifecycleEvent) -> None:
        """Record human feedback as a Langfuse score when we can resolve the trace."""

        if not isinstance(event, FeedbackRecordedLifecycleEvent):
            return
        p = event.payload
        run_id = str(p["run_id"])
        meta = self._runs.get(run_id)
        if meta is None:
            return
        meta_fb: dict[str, Any] = {
            "feedback_label": p["feedback_label"],
            "feedback_source": p["feedback_source"],
            "tool_call_id": p["tool_call_id"],
            "checkpoint_id": p["checkpoint_id"],
        }
        scalar = p.get("feedback_scalar")
        if scalar is not None:
            value: Any = scalar
        else:
            value = p["feedback_label"]
        self._client.create_score(
            name="human_feedback",
            value=value,
            trace_id=meta.trace_id,
            session_id=str(p["thread_id"]),
            metadata=meta_fb,
        )


def register_langfuse_plugin(bus: SyncEventBus, client: Langfuse | None) -> None:
    """Attach Langfuse subscribers when ``client`` is configured.

    [DALC-REQ-LANGFUSE-TRACE-001]
    """

    if client is None:
        return
    LangfuseLifecycleBridge(client).register(bus)
