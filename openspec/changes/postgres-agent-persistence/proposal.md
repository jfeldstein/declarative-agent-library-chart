## Why

Today observability data that operators need for resume, audit, and training pipelines is largely **process-local** (in-memory correlation, feedback, trajectory builders) or **delegated to vendors** (Weights & Biases for traces). That is fine for dev and single-replica pilots, but production needs **durable, queryable** storage so checkpoints survive restarts, feedback and Slack correlation survive pod churn, and internal “trace-like” records (tool spans, run metadata) can be joined to checkpoints **without** assuming W&B is the system of record. **PostgreSQL** is the natural first durable backend for this chart: operators already run it for many workloads, it supports ACID, migrations, and backup/restore. Wiring Postgres for LangGraph checkpoints **and** first-party tables for feedback/correlation closes the gap between the OpenSpec intent and what the default image can actually persist.

## What Changes

- Add an optional **Postgres-backed LangGraph checkpointer** path when `HOSTED_AGENT_CHECKPOINT_BACKEND=postgres` and `HOSTED_AGENT_CHECKPOINT_POSTGRES_URL` (or connection-from-secret) is set—replacing the current **runtime error** stub with a working integration and pinned dependency.
- Introduce **relational persistence** (schema + repository layer) for **Slack/tool correlation**, **human feedback events**, **operational run signals**, and **side-effect checkpoint metadata**, with **in-memory implementations** remaining the default when Postgres is not configured.
- Optionally persist **run/tool span summaries** (latency, tool_call_id, outcome) to Postgres for operator APIs and ATIF export staging, without replacing W&B for rich trace UI.
- **Helm**: values and templates for Postgres URL/secret refs, migration job or init documentation, connection pooling notes.
- **Docs/runbook**: secrets, migration, retention, failover, and how this relates to ADR-level durability expectations.

## Capabilities

### New Capabilities

- `cfha-postgres-agent-persistence`: Durable PostgreSQL storage for LangGraph checkpoints and first-party observability records (correlation, feedback, operational events, side-effects; optional internal span/run summaries).

### Modified Capabilities

- _(none in `openspec/specs/` today for this exact surface; runtime-langgraph-checkpoints lives under an archived change path—treat as new repo-level capability here.)_

## Impact

- **`runtime/pyproject.toml`**: new dependency (LangGraph Postgres checkpointer + `psycopg` or `asyncpg` per design).
- **`hosted_agents/observability/`**: repository interfaces, Postgres adapters, migration SQL or Alembic (if adopted).
- **`helm/chart`**: optional Postgres subchart wiring or external URL; Secret mounts.
- **CI**: integration tests with **testcontainers** or `docker run postgres` (optional marker) vs mocked DB unit tests for default PR path.
- **Operators**: must provision DB, run migrations, manage retention and PII.
