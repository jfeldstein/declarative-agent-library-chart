## Context

The runtime already exposes env-driven checkpointing (`MemorySaver`) and in-process stores for correlation and feedback. `build_checkpointer` raises when `postgres` is selected because the image does not yet bundle a Postgres saver or application schema. Production users expect **durable** checkpoints and **durable** feedback/correlation for Slack and training exports.

## Goals / Non-Goals

**Goals:**

- **LangGraph checkpoints** persisted in Postgres using a **supported** LangGraph checkpointer implementation (pin exact package and version in `pyproject.toml`).
- **Application tables** for correlation (`slack channel_id + ts → tool_call_id, run_id, thread_id, checkpoint_id`), `HumanFeedbackEvent`, `RunOperationalEvent`, and side-effect checkpoint rows—behind **interfaces** so Memory and Postgres can coexist.
- **Clear migration story**: versioned SQL or migration tool; documented apply order for Helm.
- **Safe defaults**: if Postgres URL unset, behavior matches today (memory / no durable app store).

**Non-Goals:**

- Replacing **W&B** as the primary rich-trace product UI; Postgres stores **summaries** and **join keys** for operators and export, not a full W&B clone.
- **Multi-region active-active** replication design (document single-primary assumptions).
- **Redis** implementation (separate change).

## Decisions

1. **Checkpointer library**  
   - **Decision**: Pin the official/extra LangGraph Postgres checkpointer package recommended for the repo’s `langgraph` version (e.g. `langgraph-checkpoint-postgres` or successor).  
   - **Rationale**: Avoid bespoke checkpoint serialization; stay compatible with `get_state` / `get_state_history`.  
   - **Alternatives**: Custom tables mirroring checkpoint blobs (high maintenance).

2. **DB driver**  
   - **Decision**: Prefer **`psycopg` v3** (sync) for simplicity with FastAPI sync call sites unless the team standardizes on async pools—document pool sizing for Gunicorn/Uvicorn workers.  
   - **Alternatives**: `asyncpg` + async repositories (more refactor).

3. **Schema ownership**  
   - **Decision**: Namespaced tables under a dedicated schema (e.g. `hosted_agents`) or `cfha_` prefix to avoid collisions in shared clusters.  
   - **Rationale**: Many teams share Postgres with other services.

4. **Repository pattern**  
   - **Decision**: Define protocols/ABCs (`CorrelationRepository`, `FeedbackRepository`, `RunSpanRepository`) with `Memory*` and `Postgres*` implementations; select via env `HOSTED_AGENT_OBSERVABILITY_STORE=memory|postgres`.  
   - **Rationale**: Tests stay fast with memory; production uses Postgres.

5. **Traces in Postgres**  
   - **Decision**: Store **structured span summaries** per tool call (tool_call_id, run_id, thread_id, duration_ms, outcome, redacted args hash)—not full raw payloads by default.  
   - **Rationale**: Supports operator queries and ATIF staging without huge row growth; raw payloads stay redacted or in object storage if added later.

6. **Migrations**  
   - **Decision**: Ship **SQL files** in-repo (`runtime/migrations/` or `helm/files/`) plus a small `migrate` CLI or document `psql -f` for v1; revisit Alembic if churn grows.  
   - **Alternatives**: Alembic from day one (heavier).

## Risks / Trade-offs

- **[Risk] Connection storms** from many workers → **Mitigation**: pooler (PgBouncer), max connections doc, singleton pool per process.  
- **[Risk] Large checkpoint blobs** → **Mitigation**: monitor table size, retention TTL job, optional compression policy.  
- **[Risk] PII in feedback/tool args** → **Mitigation**: redaction at write boundary; column-level policies in runbook.  
- **[Trade-off] Operational complexity** vs MemorySaver → Accept for production path only.

## Migration Plan

1. Land dependency + `build_checkpointer` Postgres path + integration test (containerized or mocked).  
2. Land SQL migrations + Postgres repositories behind feature flag env.  
3. Helm: optional Secret + env; optional pre-install Job applying SQL.  
4. Rollout: enable in staging → production; rollback = flip env to memory + drain.

## Open Questions

- Whether to use **Neon/Cloud SQL IAM** auth vs URL-only (Helm shape).  
- Whether **trajectory** full export buffers live in Postgres **JSONB** or remain ephemeral with ATIF written to object storage (future).
