## Context

The hosted-agents chart deploys **scraper CronJobs** (`jira_job`, `slack_job`) that need **incremental state**: Jira **JQL watermarks** (`updated >= …`) and Slack **`conversations.history`** **watermark_ts** (and similar keys). Today that state lives on **ephemeral filesystem paths** (`JIRA_WATERMARK_DIR`, `SLACK_STATE_DIR`), which is operationally weak unless every scraper pod mounts a **PVC** and operators manage retention/locking themselves.

The same chart already surfaces **`observability.postgresUrl`** as **`HOSTED_AGENT_POSTGRES_URL`** on the **agent** Deployment for checkpointing and related features. Reusing that DSN for scrapers avoids a second secret distribution path when operators already run a shared Postgres.

## Goals / Non-Goals

**Goals:**

- Define a **small cursor-store abstraction** in the runtime (`read_state` / `write_state` keyed by scraper identity + logical key) with pluggable backends.
- Ship a **Postgres** implementation as the first durable backend, using a **single table** (or two: one per integration) with a clear primary key and `updated_at`.
- **Helm**: optional wiring so scraper CronJob pods receive **`HOSTED_AGENT_POSTGRES_URL`** (or a scraper-specific alias **only if** we need isolation—prefer reuse to reduce secret sprawl) when `cursorStore.backend: postgres` (or equivalent) is set.
- Preserve **file** backend as **default** so existing examples and tests keep working without Postgres.
- Document **migration** from file → Postgres (one-time copy or “cold start” re-backfill).

**Non-Goals:**

- Changing **RAG’s** internal vector store or adding a **new RAG HTTP endpoint** in v1 of this change (RAG-as-store remains a **documented follow-up** or optional v2 if we add a minimal `GET`/`PUT` cursor contract).
- **Distributed locking** across concurrent scraper replicas beyond DB **row-level** semantics (operators SHOULD use `concurrencyPolicy: Forbid` on CronJobs, which the chart already supports).
- **Hosted multi-tenant** isolation beyond “key includes `SCRAPER_SCOPE` + integration + stable job id”.

## Decisions

1. **Postgres first, RAG later**  
   **Rationale:** DSN and driver patterns already exist in-repo for the agent; RAG-as-cursor-store needs API design (`/v1/query` vs dedicated resource) and rate limits. **Alternative:** only PVC—rejected as harder to operate than SQL for many clusters.

2. **Reuse `HOSTED_AGENT_POSTGRES_URL` on scraper pods when enabled**  
   **Rationale:** one Secret, one chart knob (`observability.postgresUrl`). **Alternative:** `scrapers.cursorStore.postgresUrl`—allow only if we need scraper-only DB; design leaves room for **override** values key that wins over the shared URL.

3. **Schema: table `scraper_cursor_state`** (name TBD in implementation) with columns roughly `(integration, scope, key_hash or key, value_jsonb, updated_at)` and **primary key** `(integration, scope, key)` with key length cap to avoid oversized PKs—store **hash of key** if raw keys (e.g. JQL) exceed limit.  
   **Rationale:** simple upsert (`INSERT … ON CONFLICT DO UPDATE`). **Alternative:** per-integration tables—rejected as unnecessary churn.

4. **Runtime selection via env** (e.g. `SCRAPER_CURSOR_BACKEND=file|postgres`) set by Helm when backend enabled.  
   **Rationale:** keeps CronJob command static; ConfigMap already carries non-secret job JSON.

5. **Migrations**  
   **Rationale:** document **idempotent `CREATE TABLE IF NOT EXISTS`** run by scraper on first use **or** ship a Job/chart hook—**Open Question** which is acceptable for this repo’s operator posture.

## Risks / Trade-offs

- **[Risk] Short-lived job opens many connections** → **Mitigation:** single connection per run, `statement_timeout`, small pool or direct `psycopg`/`asyncpg` not needed for sync cron.

- **[Risk] Schema drift across chart versions** → **Mitigation:** version column or `schema_migrations` table; document upgrade path.

- **[Risk] Accidental cross-environment state** → **Mitigation:** keys always include `SCRAPER_SCOPE` + release-derived scope from Helm; document operator responsibility for distinct scopes per env.

- **[Risk] RAG “cursor” without new API encourages misuse of `/v1/query`** → **Mitigation:** keep RAG path out of v1 implementation; mention only in proposal/spec as future capability.

## Migration Plan

1. Ship with **default file** backend—no operator action.
2. Enable Postgres backend in staging: set `observability.postgresUrl` (if not already), flip `cursorStore` Helm values, run scraper once; expect **re-fetch overlap** window (same as today’s watermark overlap) or operator-tuned JQL.
3. Rollback: flip backend to `file` and restore PVC or accept re-bootstrap.

## Open Questions

- Should the chart run a **one-shot migration Job** for `CREATE TABLE`, or is **lazy DDL in scraper** acceptable for this project?
- Do we require **`sslmode`** / connection params beyond URL string (reuse agent patterns)?
- Exact env name for override: **`SCRAPER_POSTGRES_URL`** vs only **`HOSTED_AGENT_POSTGRES_URL`**?
