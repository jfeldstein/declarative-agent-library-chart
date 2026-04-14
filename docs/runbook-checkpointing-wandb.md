# Runbook: checkpoints, Slack feedback, W&B, ATIF export, shadow

This runbook covers the **runtime** feature flags added for OpenSpec change `agent-checkpointing-wandb-feedback`: durable LangGraph checkpoints, Slack reaction correlation, optional Weights & Biases traces, ATIF-shaped exports, and shadow rollout hooks.

## Thread and checkpoint identifiers

- **`thread_id`**: stable per conversation or operator session. Clients may send `thread_id` in the trigger JSON body or `X-Agent-Thread-Id` on `POST /api/v1/trigger`. If omitted, the runtime falls back to a new UUID for the HTTP request’s `run_id` (less ideal for resume semantics).
- **`checkpoint_id`**: assigned by the LangGraph checkpointer (and additional **side-effect** records for tools such as `slack.post_message`). Side-effect metadata is listed under `GET /api/v1/runtime/threads/{thread_id}/side-effects`.
- **`run_id`**: UUID generated per trigger invocation (distinct from `X-Request-Id`).

## Checkpointer backends

| `HOSTED_AGENT_CHECKPOINT_BACKEND` | Behavior |
|-----------------------------------|----------|
| `memory` (default) | In-process `MemorySaver`; suitable for dev / single replica. |
| `postgres` | **Bundled** in the published image (`langgraph-checkpoint-postgres` + `psycopg` v3). Set `HOSTED_AGENT_POSTGRES_URL` (`postgres://` or `postgresql://`). On first use the runtime runs LangGraph’s checkpoint `setup()` (creates checkpoint tables). Size the shared pool with `HOSTED_AGENT_POSTGRES_POOL_MAX` (default `5` per process). Prefer a session pooler (PgBouncer) in front of Postgres for multi-worker deployments. |
| `redis` | Reserved until a Redis saver is pinned for this chart. |

When `HOSTED_AGENT_CHECKPOINTS_ENABLED` is **false** (Helm default), the runtime uses the original single-node graph without persistence.

**Ephemeral runs:** JSON field `ephemeral: true` opts out of checkpoint persistence even when checkpointing is enabled globally.

### Embedded PostgreSQL (PGlite) for local dev

Set **`HOSTED_AGENT_USE_PGLITE=1`** to start an embedded [PGlite](https://pglite.dev/) instance (via optional Python package **`py-pglite`**) and set **`HOSTED_AGENT_POSTGRES_URL`** when it is unset. Install: **`uv sync --extra pglite`**. First run may install Node dependencies (PGlite is WASM/Node-backed).

- Uses **TCP** mode on **`127.0.0.1`** with a free port (or **`HOSTED_AGENT_PGLITE_TCP_PORT`** / **`HOSTED_AGENT_PGLITE_TCP_HOST`** to pin).
- Checkpoint and shared Postgres consumers read **`HOSTED_AGENT_POSTGRES_URL`** only.
- **Single process only** (e.g. one Uvicorn worker). Do not rely on one embedded DB across multiple Gunicorn workers.
- CI and minimal images: omit the **`pglite`** extra; use a real Postgres service or stay on **`memory`**.

## Operator HTTP APIs

- `GET /api/v1/runtime/threads/{thread_id}/state` — latest checkpoint snapshot (LangGraph `get_state` semantics).
- `GET /api/v1/runtime/threads/{thread_id}/checkpoints` — history (`get_state_history`).
- `GET /api/v1/runtime/threads/{thread_id}/side-effects` — logical checkpoints around visible side effects (Slack posts).
- `POST /api/v1/integrations/slack/reactions` — normalized reaction payload (`channel_id`, `message_ts`, `reaction`, `event_id`, `user_id`).
- `GET /api/v1/runtime/feedback/human` — recorded human feedback events (`HOSTED_AGENT_OBSERVABILITY_STORE=memory` default; `postgres` reads from the same DB tables when configured).
- `GET /api/v1/runtime/exports/atif?run_id=...` — **ATIF v1.4** trajectory JSON (Harbor Agent Trajectory Format; see [ADR 0004](adrs/0004-pin-atif-v1-4-trajectory-export.md) and [Harbor ATIF docs](https://www.harborframework.com/docs/agents/trajectory-format)); requires `HOSTED_AGENT_ATIF_EXPORT_ENABLED`. Optional env: `HOSTED_AGENT_ATIF_AGENT_NAME`, `HOSTED_AGENT_ATIF_AGENT_VERSION`, `HOSTED_AGENT_ATIF_MODEL_NAME`.

## Secrets, retention, rollback, PII

- **Secrets:** store `WANDB_API_KEY`, Slack tokens, and database URLs in Kubernetes Secrets; reference them from the Deployment (not committed to values).
- **Retention:** checkpoint and trajectory retention are deployment-specific; the default in-memory stores reset on restart.
- **Rollback:** disable feature flags (`HOSTED_AGENT_CHECKPOINTS_ENABLED`, `HOSTED_AGENT_WANDB_ENABLED`, `HOSTED_AGENT_SLACK_FEEDBACK_ENABLED`, etc.) via Helm values; the runtime remains compatible with older clients.
- **PII:** enable redaction in export paths (`export_atif_batch` redacts common secret key names); extend blocklists before sending data to W&B or external training stores.

## Application observability store (correlation, feedback, side-effects, span summaries)

| `HOSTED_AGENT_OBSERVABILITY_STORE` | Behavior |
|------------------------------------|----------|
| `memory` (default) | In-process stores (same as pre-Postgres behavior). |
| `postgres` | Persist Slack correlation, human feedback, operational events, orphan reactions, side-effect checkpoints, and per-tool span summaries under the `hosted_agents` schema. Requires `HOSTED_AGENT_POSTGRES_URL` (same DSN as checkpoint Postgres when both are enabled). |

The runtime applies bundled DDL from `hosted_agents/migrations/001_hosted_agents_observability.sql` on first pool use (idempotent `CREATE … IF NOT EXISTS`). For GitOps-only clusters, operators may instead apply the same file with `psql` or enable the optional Helm hook Job (`observability.postgres.migrations.enabled`), which requires `observability.postgresUrlSecret` (or legacy `observability.postgres.urlSecret`) so the Job can read `DATABASE_URL`.

**Rollback:** take a logical or physical snapshot before upgrades; to roll back behavior flip `HOSTED_AGENT_OBSERVABILITY_STORE` to `memory` and `HOSTED_AGENT_CHECKPOINT_BACKEND` to `memory`, then redeploy (data remains in Postgres until explicitly removed).

## Helm values (short)

See `helm/chart/values.yaml` → `observability.*` for toggles that map to the env vars above. **`observability.postgresUrl`** or **`observability.postgresUrlSecret`** sets **`HOSTED_AGENT_POSTGRES_URL`**; **`observability.postgres.url`** / **`urlSecret`** are optional aliases coalesced in templates. **`observability.postgres.poolMax`** maps to **`HOSTED_AGENT_POSTGRES_POOL_MAX`**. Optional `observability.labelRegistry` overrides the default global label registry JSON.

## Manual smoke (Postgres in kind)

1. Build/push an image from this repo (`Dockerfile` syncs `--extra wandb --extra postgres`).
2. Install Postgres in the cluster (operator or single-instance chart) and create a Secret with a `postgres://…` URL.
3. Set `observability.store: postgres`, `observability.checkpoints.enabled: true`, `observability.checkpoints.backend: postgres`, and set `observability.postgresUrl` or `observability.postgresUrlSecret` (one DSN for checkpoints + observability tables).
4. Apply migrations (runtime auto-apply on first connect, or Helm migration hook, or `psql -f` on the SQL file under `helm/chart/files/observability/`).
5. Trigger a run, delete the agent pod, and confirm `GET …/feedback/human` and checkpoint routes still return prior data.
