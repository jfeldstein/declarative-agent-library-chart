## Why

Scraper CronJobs today persist **Jira watermarks** and **Slack channel cursors** on the container filesystem (`JIRA_WATERMARK_DIR`, `SLACK_STATE_DIR`). That is fragile across restarts, evictions, and multi-replica patterns, and it duplicates data the platform may already have in **Postgres** (`HOSTED_AGENT_POSTGRES_URL` / chart `observability.postgresUrl`) or could anchor in **RAG** metadata if we define a stable contract. Operators need a **documented, optional durable store** so incremental scrapes survive pod lifecycle without ad-hoc PVC wiring.

## What Changes

- Introduce a **configurable cursor / watermark backend** for `jira_job` and `slack_channel` (and any future scrapers using the same pattern): at minimum **Postgres** (SQL table or advisory-compatible schema) and optionally **RAG-backed** persistence where the existing HTTP API can represent “last seen” without new infra.
- **Helm**: when a backend is enabled, inject the **same DSN pattern** the chart already uses for the agent (`observability.postgresUrl` → env on scraper pods), or explicit scraper-only overrides if we need isolation; document precedence (scraper override vs shared cluster DSN).
- **Runtime**: abstract read/write of `{scope, key} → opaque state` behind a small interface; default remains **file** for backward compatibility.
- **Verification**: unit tests for SQL store (mocked or embedded), Helm unittest for env wiring, and **spec–test traceability** rows for new SHALLs.
- **BREAKING**: none at the API level if file mode remains the default; any **new required** values key would be optional-only.

## Capabilities

### New Capabilities

- `dalc-scraper-cursor-store`: Durable persistence for scraper incremental state (Jira JQL watermarks, Slack `conversations.history` cursors), selectable backend (file default, Postgres, optional RAG), env + Helm wiring, failure modes, and security (no secrets in ConfigMap; DSN from Secret/env only).

### Modified Capabilities

- _(none at proposal time)_ — if implementation ties scraper pods to `observability.postgresUrl` in a normative way not already covered by existing specs, add a **delta** under `dalc-rag-from-scrapers` or `dalc-helm-unittest` in the design/spec phase.

## Impact

- **Runtime**: `hosted_agents.scrapers.jira_job`, `hosted_agents.scrapers.slack_job`, new small module e.g. `scrapers/cursor_store.py`.
- **Helm**: `scraper-cronjobs.yaml` (and possibly `values.yaml` / `values.schema.json`) for optional `scrapers.cursorStore` or per-source keys.
- **Docs / examples**: `examples/with-scrapers`, `docs/runbook-*` or observability docs for DSN reuse.
- **CI**: pytest, helm unittest, `scripts/check_spec_traceability.py` when new promoted SHALLs land.
