"""Pytest hooks for the agent runtime."""

from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

import pytest
from langchain_core.messages import AIMessage

from agent.chat_model import FakeToolChatModel

# Avoid LangSmith network noise during unit tests when LangChain/LangGraph is on the path.
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")

# Prometheus plugin mirrors lifecycle events into ``dalc_*`` metrics (chart defaults plugin off).
os.environ.setdefault(
    "HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED",
    "true",
)


@pytest.fixture(autouse=True)
def _reset_langgraph_checkpoint_isolation() -> None:
    """Fresh in-memory checkpointer + compiled graph cache per test."""
    from agent.checkpointing import clear_memory_checkpointer
    from agent.observability.checkpointer import reset_checkpoint_postgres_pool
    from agent.observability.pglite_runtime import stop_pglite_embedded
    from agent.observability.stores import reset_observability_stores_cache
    from agent.tools.registry import _reset_for_tests

    clear_memory_checkpointer()
    reset_checkpoint_postgres_pool()
    reset_observability_stores_cache()
    _reset_for_tests()
    yield
    stop_pglite_embedded()


def tool_then_text_responses(
    tool_name: str,
    tool_args: dict[str, Any],
    *,
    final_text: str = "done",
) -> FakeToolChatModel:
    """Two-turn fake model: one tool call, one plain assistant message."""

    return FakeToolChatModel(
        responses=[
            AIMessage(
                content="",
                tool_calls=[
                    {
                        "name": tool_name,
                        "args": tool_args,
                        "id": "dalc-1",
                        "type": "tool_call",
                    },
                ],
            ),
            AIMessage(content=final_text),
        ],
    )


def patch_supervisor_fake_model(
    monkeypatch: pytest.MonkeyPatch,
    fake: FakeToolChatModel,
) -> None:
    monkeypatch.setattr("agent.supervisor.resolve_chat_model", lambda: fake)


def patch_supervisor_sequence(
    monkeypatch: pytest.MonkeyPatch,
    factory: Callable[[], FakeToolChatModel],
) -> None:
    monkeypatch.setattr("agent.supervisor.resolve_chat_model", factory)
