"""LangChain callbacks and helpers for LLM token / TTFT Prometheus metrics.

Traceability: [DALC-REQ-TOKEN-MET-001] [DALC-REQ-TOKEN-MET-002] [DALC-REQ-TOKEN-MET-003]
[DALC-REQ-TOKEN-MET-005]
"""

from __future__ import annotations

import math
import os
import time
from typing import Any
from uuid import UUID

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from agent.metrics import (
    observe_llm_completion_metrics,
    observe_llm_time_to_first_token,
)
from agent.trigger_context import TriggerContext


def _parse_cost_rates_from_env() -> tuple[float | None, float | None]:
    """Return per-token USD rates when both are configured as finite non-negative floats."""

    def _one(key: str) -> float | None:
        raw = os.environ.get(key, "").strip()
        if not raw:
            return None
        try:
            v = float(raw)
        except ValueError:
            return None
        if not math.isfinite(v) or v < 0:
            return None
        return v

    return (
        _one("HOSTED_AGENT_LLM_EST_COST_USD_PER_INPUT_TOKEN"),
        _one("HOSTED_AGENT_LLM_EST_COST_USD_PER_OUTPUT_TOKEN"),
    )


def _usage_tokens_from_message(msg: AIMessage) -> tuple[int | None, int | None]:
    md = getattr(msg, "usage_metadata", None) or {}
    if not isinstance(md, dict):
        return None, None
    it = md.get("input_tokens")
    ot = md.get("output_tokens")
    if it is not None and not isinstance(it, int):
        try:
            it = int(it)
        except (TypeError, ValueError):
            it = None
    if ot is not None and not isinstance(ot, int):
        try:
            ot = int(ot)
        except (TypeError, ValueError):
            ot = None
    if it is not None and it < 0:
        it = None
    if ot is not None and ot < 0:
        ot = None
    return it, ot


class SupervisorLlmMetricsCallback(BaseCallbackHandler):
    """Records TTFT, token counts, missing usage, and estimated cost for chat model runs."""

    def __init__(self, ctx: TriggerContext) -> None:
        super().__init__()
        self._ctx = ctx
        self._runs: dict[UUID, dict[str, Any]] = {}

    def on_chat_model_start(
        self,
        serialized: dict[str, Any],
        messages: list[list[Any]],
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        self._runs[run_id] = {"t0": time.perf_counter(), "ttft_done": False}

    def on_llm_new_token(
        self,
        token: str,
        *,
        chunk: Any = None,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        if not (token and str(token).strip()):
            return
        st = self._runs.get(run_id)
        if st is None or st.get("ttft_done"):
            return
        elapsed = max(time.perf_counter() - st["t0"], 0.0)
        observe_llm_time_to_first_token(
            self._ctx,
            elapsed,
            streaming_label="true",
            result="success",
        )
        st["ttft_done"] = True

    def on_llm_end(
        self,
        response: LLMResult,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        st = self._runs.pop(run_id, None)
        if st is not None:
            ttft_done = bool(st.get("ttft_done"))
            if not ttft_done:
                elapsed = max(time.perf_counter() - st["t0"], 0.0)
                observe_llm_time_to_first_token(
                    self._ctx,
                    elapsed,
                    streaming_label="false",
                    result="success",
                )
        # If ``st`` is missing (no paired ``on_chat_model_start`` for this ``run_id``),
        # skip TTFT — using ``perf_counter()`` as t0 would emit bogus near-zero samples.

        it: int | None = None
        ot: int | None = None
        try:
            gen = response.generations[0][0]
        except IndexError:
            gen = None
        if isinstance(gen, ChatGeneration):
            msg = gen.message
            if isinstance(msg, AIMessage):
                it, ot = _usage_tokens_from_message(msg)

        in_rate, out_rate = _parse_cost_rates_from_env()
        observe_llm_completion_metrics(
            self._ctx,
            input_tokens=it,
            output_tokens=ot,
            input_rate_usd=in_rate,
            output_rate_usd=out_rate,
            result="success",
        )

    def on_llm_error(
        self,
        error: BaseException,
        *,
        run_id: UUID,
        parent_run_id: UUID | None = None,
        tags: list[str] | None = None,
        **kwargs: Any,
    ) -> Any:
        self._runs.pop(run_id, None)
