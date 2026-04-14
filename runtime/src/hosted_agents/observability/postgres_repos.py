"""Postgres-backed observability repositories (psycopg v3 + pool)."""

from __future__ import annotations

from datetime import UTC, datetime

from psycopg.rows import dict_row
from psycopg.types.json import Json
from psycopg_pool import ConnectionPool

from hosted_agents.migrations.schema import apply_observability_schema
from hosted_agents.observability.correlation import SlackMessageRef, ToolCorrelation
from hosted_agents.observability.feedback import (
    HumanFeedbackEvent,
    OrphanReactionEvent,
    RunOperationalEvent,
)
from hosted_agents.observability.side_effects import SideEffectCheckpoint
from hosted_agents.observability.span_summaries import ToolSpanSummary


def _epoch_to_ts(t: float) -> datetime:
    return datetime.fromtimestamp(t, tz=UTC)


class PostgresCorrelationStore:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def put_slack_message(self, ref: SlackMessageRef, corr: ToolCorrelation) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO hosted_agents.slack_correlation (
                      channel_id, message_ts, tool_call_id, run_id, thread_id,
                      checkpoint_id, tool_name, wandb_run_id
                    ) VALUES (
                      %(channel_id)s, %(message_ts)s, %(tool_call_id)s, %(run_id)s,
                      %(thread_id)s, %(checkpoint_id)s, %(tool_name)s, %(wandb_run_id)s
                    )
                    ON CONFLICT (channel_id, message_ts) DO UPDATE SET
                      tool_call_id = EXCLUDED.tool_call_id,
                      run_id = EXCLUDED.run_id,
                      thread_id = EXCLUDED.thread_id,
                      checkpoint_id = EXCLUDED.checkpoint_id,
                      tool_name = EXCLUDED.tool_name,
                      wandb_run_id = EXCLUDED.wandb_run_id
                    """,
                    {
                        "channel_id": ref.channel_id,
                        "message_ts": ref.message_ts,
                        "tool_call_id": corr.tool_call_id,
                        "run_id": corr.run_id,
                        "thread_id": corr.thread_id,
                        "checkpoint_id": corr.checkpoint_id,
                        "tool_name": corr.tool_name,
                        "wandb_run_id": corr.wandb_run_id,
                    },
                )

    def get_by_slack(self, ref: SlackMessageRef) -> ToolCorrelation | None:
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT tool_call_id, run_id, thread_id, checkpoint_id, tool_name, wandb_run_id
                    FROM hosted_agents.slack_correlation
                    WHERE channel_id = %s AND message_ts = %s
                    """,
                    (ref.channel_id, ref.message_ts),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return ToolCorrelation(
            tool_call_id=str(row["tool_call_id"]),
            run_id=str(row["run_id"]),
            thread_id=str(row["thread_id"]),
            checkpoint_id=str(row["checkpoint_id"]) if row["checkpoint_id"] else None,
            tool_name=str(row["tool_name"]),
            wandb_run_id=str(row["wandb_run_id"]) if row["wandb_run_id"] else None,
        )


class PostgresFeedbackStore:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def record_human(self, ev: HumanFeedbackEvent) -> HumanFeedbackEvent | None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                if ev.dedupe_key:
                    cur.execute(
                        "DELETE FROM hosted_agents.human_feedback WHERE dedupe_key = %s",
                        (ev.dedupe_key,),
                    )
                cur.execute(
                    """
                    INSERT INTO hosted_agents.human_feedback (
                      dedupe_key, registry_id, schema_version, label_id, tool_call_id,
                      checkpoint_id, run_id, thread_id, feedback_source, agent_id, created_at
                    ) VALUES (
                      %(dedupe_key)s, %(registry_id)s, %(schema_version)s, %(label_id)s,
                      %(tool_call_id)s, %(checkpoint_id)s, %(run_id)s, %(thread_id)s,
                      %(feedback_source)s, %(agent_id)s, %(created_at)s
                    )
                    """,
                    {
                        "dedupe_key": ev.dedupe_key,
                        "registry_id": ev.registry_id,
                        "schema_version": ev.schema_version,
                        "label_id": ev.label_id,
                        "tool_call_id": ev.tool_call_id,
                        "checkpoint_id": ev.checkpoint_id,
                        "run_id": ev.run_id,
                        "thread_id": ev.thread_id,
                        "feedback_source": ev.feedback_source,
                        "agent_id": ev.agent_id,
                        "created_at": _epoch_to_ts(ev.created_at),
                    },
                )
        return ev

    def record_operational(self, ev: RunOperationalEvent) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO hosted_agents.run_operational_event
                      (kind, run_id, thread_id, payload, created_at)
                    VALUES (%(kind)s, %(run_id)s, %(thread_id)s, %(payload)s, %(created_at)s)
                    """,
                    {
                        "kind": ev.kind,
                        "run_id": ev.run_id,
                        "thread_id": ev.thread_id,
                        "payload": Json(ev.payload),
                        "created_at": _epoch_to_ts(ev.created_at),
                    },
                )

    def record_orphan_reaction(self, ev: OrphanReactionEvent) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO hosted_agents.orphan_reaction
                      (channel_id, message_ts, reason, raw_event_id, created_at)
                    VALUES (%(channel_id)s, %(message_ts)s, %(reason)s, %(raw_event_id)s, %(created_at)s)
                    """,
                    {
                        "channel_id": ev.channel_id,
                        "message_ts": ev.message_ts,
                        "reason": ev.reason,
                        "raw_event_id": ev.raw_event_id,
                        "created_at": _epoch_to_ts(ev.created_at),
                    },
                )

    def human_events(self) -> list[HumanFeedbackEvent]:
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT registry_id, schema_version, label_id, tool_call_id, checkpoint_id,
                           run_id, thread_id, feedback_source, agent_id, dedupe_key,
                           EXTRACT(EPOCH FROM created_at) AS created_epoch
                    FROM hosted_agents.human_feedback
                    ORDER BY id DESC
                    LIMIT 5000
                    """
                )
                rows = cur.fetchall()
        out: list[HumanFeedbackEvent] = []
        for row in rows:
            out.append(
                HumanFeedbackEvent(
                    registry_id=str(row["registry_id"]),
                    schema_version=str(row["schema_version"]),
                    label_id=str(row["label_id"]),
                    tool_call_id=str(row["tool_call_id"]),
                    checkpoint_id=str(row["checkpoint_id"])
                    if row["checkpoint_id"]
                    else None,
                    run_id=str(row["run_id"]),
                    thread_id=str(row["thread_id"]),
                    feedback_source=str(row["feedback_source"]),
                    agent_id=str(row["agent_id"]) if row["agent_id"] else None,
                    dedupe_key=str(row["dedupe_key"]) if row["dedupe_key"] else None,
                    created_at=float(row["created_epoch"]),
                )
            )
        return out

    def operational_events(self) -> list[RunOperationalEvent]:
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT kind, run_id, thread_id, payload,
                           EXTRACT(EPOCH FROM created_at) AS created_epoch
                    FROM hosted_agents.run_operational_event
                    ORDER BY id DESC
                    LIMIT 5000
                    """
                )
                rows = cur.fetchall()
        return [
            RunOperationalEvent(
                kind=str(r["kind"]),
                run_id=str(r["run_id"]),
                thread_id=str(r["thread_id"]),
                payload=dict(r["payload"]) if isinstance(r["payload"], dict) else {},
                created_at=float(r["created_epoch"]),
            )
            for r in rows
        ]

    def orphans(self) -> list[OrphanReactionEvent]:
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT channel_id, message_ts, reason, raw_event_id,
                           EXTRACT(EPOCH FROM created_at) AS created_epoch
                    FROM hosted_agents.orphan_reaction
                    ORDER BY id DESC
                    LIMIT 2000
                    """
                )
                rows = cur.fetchall()
        return [
            OrphanReactionEvent(
                channel_id=str(r["channel_id"]),
                message_ts=str(r["message_ts"]),
                reason=str(r["reason"]),
                raw_event_id=str(r["raw_event_id"]) if r["raw_event_id"] else None,
                created_at=float(r["created_epoch"]),
            )
            for r in rows
        ]


class PostgresSideEffectStore:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def add(self, rec: SideEffectCheckpoint) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO hosted_agents.side_effect_checkpoint (
                      checkpoint_id, run_id, thread_id, tool_call_id, tool_name, external_ref, created_at
                    ) VALUES (
                      %(checkpoint_id)s, %(run_id)s, %(thread_id)s, %(tool_call_id)s,
                      %(tool_name)s, %(external_ref)s, %(created_at)s
                    )
                    """,
                    {
                        "checkpoint_id": rec.checkpoint_id,
                        "run_id": rec.run_id,
                        "thread_id": rec.thread_id,
                        "tool_call_id": rec.tool_call_id,
                        "tool_name": rec.tool_name,
                        "external_ref": Json(rec.external_ref),
                        "created_at": rec.created_at,
                    },
                )

    def by_thread(self, thread_id: str) -> list[SideEffectCheckpoint]:
        with self._pool.connection() as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute(
                    """
                    SELECT checkpoint_id, run_id, thread_id, tool_call_id, tool_name, external_ref, created_at
                    FROM hosted_agents.side_effect_checkpoint
                    WHERE thread_id = %s
                    ORDER BY id ASC
                    """,
                    (thread_id,),
                )
                rows = cur.fetchall()
        out: list[SideEffectCheckpoint] = []
        for r in rows:
            er = r["external_ref"]
            if not isinstance(er, dict):
                er = {}
            out.append(
                SideEffectCheckpoint(
                    checkpoint_id=str(r["checkpoint_id"]),
                    run_id=str(r["run_id"]),
                    thread_id=str(r["thread_id"]),
                    tool_call_id=str(r["tool_call_id"]),
                    tool_name=str(r["tool_name"]),
                    external_ref={str(k): str(v) for k, v in er.items()},
                    created_at=float(r["created_at"]),
                )
            )
        return out


class PostgresSpanSummaryStore:
    def __init__(self, pool: ConnectionPool) -> None:
        self._pool = pool

    def record(self, row: ToolSpanSummary) -> None:
        with self._pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO hosted_agents.tool_span_summary (
                      tool_call_id, run_id, thread_id, tool_name, duration_ms, outcome, args_hash
                    ) VALUES (
                      %(tool_call_id)s, %(run_id)s, %(thread_id)s, %(tool_name)s,
                      %(duration_ms)s, %(outcome)s, %(args_hash)s
                    )
                    """,
                    {
                        "tool_call_id": row.tool_call_id,
                        "run_id": row.run_id,
                        "thread_id": row.thread_id,
                        "tool_name": row.tool_name,
                        "duration_ms": row.duration_ms,
                        "outcome": row.outcome,
                        "args_hash": row.args_hash,
                    },
                )


def create_observability_pool(
    conninfo: str,
    *,
    min_size: int = 1,
    max_size: int = 5,
) -> ConnectionPool:
    return ConnectionPool(
        conninfo=conninfo,
        min_size=min_size,
        max_size=max_size,
        kwargs={"autocommit": True, "prepare_threshold": 0, "row_factory": dict_row},
    )


def ensure_observability_schema(pool: ConnectionPool) -> None:
    """Create application tables once per process (idempotent DDL)."""

    with pool.connection() as conn:
        apply_observability_schema(conn)
