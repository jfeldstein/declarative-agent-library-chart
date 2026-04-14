"""Postgres observability repositories (mocked pool; no real database)."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field

import pytest

from hosted_agents.observability.correlation import SlackMessageRef, ToolCorrelation
from hosted_agents.observability.feedback import (
    HumanFeedbackEvent,
    OrphanReactionEvent,
    RunOperationalEvent,
)
from hosted_agents.observability.postgres_repos import (
    PostgresCorrelationStore,
    PostgresFeedbackStore,
    PostgresSideEffectStore,
    PostgresSpanSummaryStore,
)
from hosted_agents.observability.side_effects import SideEffectCheckpoint
from hosted_agents.observability.span_summaries import ToolSpanSummary


@dataclass
class _PoolState:
    fetchone: dict | None = None
    fetchall_queue: list[list[dict]] = field(default_factory=list)


class _FakeCursor:
    def __init__(self, state: _PoolState) -> None:
        self._state = state

    def execute(self, query: str, params: object | None = None) -> None:
        return None

    def fetchone(self) -> dict | None:
        return self._state.fetchone

    def fetchall(self) -> list[dict]:
        if self._state.fetchall_queue:
            return list(self._state.fetchall_queue.pop(0))
        return []

    def __enter__(self) -> _FakeCursor:
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def close(self) -> None:
        return None


class _FakeConn:
    def __init__(self, state: _PoolState) -> None:
        self._state = state

    def cursor(self, row_factory: object | None = None) -> _FakeCursor:
        return _FakeCursor(self._state)


class _FakePool:
    def __init__(self, state: _PoolState) -> None:
        self._state = state

    @contextmanager
    def connection(self) -> object:
        yield _FakeConn(self._state)


def test_postgres_correlation_put_and_get() -> None:
    st = _PoolState(
        fetchone={
            "tool_call_id": "tc1",
            "run_id": "r1",
            "thread_id": "t1",
            "checkpoint_id": "cp1",
            "tool_name": "slack.post_message",
            "wandb_run_id": None,
        },
    )
    pool = _FakePool(st)
    store = PostgresCorrelationStore(pool)  # type: ignore[arg-type]
    ref = SlackMessageRef(channel_id="C1", message_ts="1.2")
    corr = ToolCorrelation(
        tool_call_id="tc1",
        run_id="r1",
        thread_id="t1",
        checkpoint_id="cp1",
        tool_name="slack.post_message",
    )
    store.put_slack_message(ref, corr)
    got = store.get_by_slack(ref)
    assert got is not None
    assert got.tool_call_id == "tc1"


def test_postgres_feedback_human_and_lists() -> None:
    st = _PoolState(
        fetchall_queue=[
            [
                {
                    "registry_id": "reg",
                    "schema_version": "1",
                    "label_id": "pos",
                    "tool_call_id": "tc",
                    "checkpoint_id": None,
                    "run_id": "r",
                    "thread_id": "t",
                    "feedback_source": "slack",
                    "agent_id": None,
                    "dedupe_key": "d1",
                    "created_epoch": 1.0,
                }
            ],
            [
                {
                    "kind": "k",
                    "run_id": "r",
                    "thread_id": "t",
                    "payload": {},
                    "created_epoch": 1.0,
                }
            ],
            [
                {
                    "channel_id": "C",
                    "message_ts": "1",
                    "reason": "x",
                    "raw_event_id": None,
                    "created_epoch": 1.0,
                }
            ],
        ],
    )
    pool = _FakePool(st)
    fb = PostgresFeedbackStore(pool)  # type: ignore[arg-type]
    ev = HumanFeedbackEvent(
        registry_id="reg",
        schema_version="1",
        label_id="pos",
        tool_call_id="tc",
        checkpoint_id=None,
        run_id="r",
        thread_id="t",
        feedback_source="slack",
        dedupe_key="d1",
    )
    assert fb.record_human(ev) is not None
    fb.record_operational(
        RunOperationalEvent(kind="k", run_id="r", thread_id="t", payload={"a": 1})
    )
    fb.record_orphan_reaction(
        OrphanReactionEvent(
            channel_id="C",
            message_ts="1",
            reason="x",
            raw_event_id=None,
        )
    )
    human = fb.human_events()
    assert len(human) == 1
    assert human[0].tool_call_id == "tc"
    assert len(fb.operational_events()) == 1
    assert len(fb.orphans()) == 1


def test_postgres_side_effect_add_and_list() -> None:
    st = _PoolState(
        fetchall_queue=[
            [
                {
                    "checkpoint_id": "se1",
                    "run_id": "r",
                    "thread_id": "t1",
                    "tool_call_id": "tc",
                    "tool_name": "slack.post_message",
                    "external_ref": {"channel_id": "C"},
                    "created_at": 1.0,
                }
            ]
        ],
    )
    pool = _FakePool(st)
    se = PostgresSideEffectStore(pool)  # type: ignore[arg-type]
    se.add(
        SideEffectCheckpoint(
            checkpoint_id="se1",
            run_id="r",
            thread_id="t1",
            tool_call_id="tc",
            tool_name="slack.post_message",
            external_ref={"channel_id": "C"},
            created_at=1.0,
        )
    )
    rows = se.by_thread("t1")
    assert len(rows) == 1
    assert rows[0].checkpoint_id == "se1"


def test_postgres_span_summary_record() -> None:
    st = _PoolState()
    pool = _FakePool(st)
    sp = PostgresSpanSummaryStore(pool)  # type: ignore[arg-type]
    sp.record(
        ToolSpanSummary(
            tool_call_id="tc",
            run_id="r",
            thread_id="t",
            tool_name="sample.echo",
            duration_ms=12,
            outcome="success",
            args_hash="abc",
        )
    )


def test_build_observability_stores_postgres_requires_url(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("HOSTED_AGENT_OBSERVABILITY_STORE", "postgres")
    monkeypatch.delenv("HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_CHECKPOINT_POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_POSTGRES_URL", raising=False)
    monkeypatch.delenv("HOSTED_AGENT_USE_PGLITE", raising=False)
    from hosted_agents.observability.settings import ObservabilitySettings
    from hosted_agents.observability.stores import (
        build_observability_stores,
        reset_observability_stores_cache,
    )

    reset_observability_stores_cache()
    obs = ObservabilitySettings.from_env()
    with pytest.raises(RuntimeError, match="HOSTED_AGENT_OBSERVABILITY_POSTGRES_URL"):
        build_observability_stores(obs)
