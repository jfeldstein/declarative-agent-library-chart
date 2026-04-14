## 1. Runtime cursor abstraction

- [ ] 1.1 Add `hosted_agents.scrapers.cursor_store` (or equivalent) with a narrow interface: `get_state(integration, scope, key) -> str | None`, `set_state(...)`, keyed by stable `(integration, scope, key)`; default **file** adapter delegates to existing Jira/Slack path logic.
- [ ] 1.2 Implement **Postgres** adapter using `HOSTED_AGENT_POSTGRES_URL` (or documented override env) with **idempotent DDL** strategy per design resolution (lazy `CREATE TABLE` vs chart Job—pick one and document).
- [ ] 1.3 Refactor `jira_job` and `slack_job` to use the adapter for watermark / channel cursor read/write; keep metrics and RAG payload shapes unchanged.

## 2. Helm and values

- [ ] 2.1 Add documented `scrapers.cursorStore` (or per-source) values: `backend: file|postgres`, optional **override** DSN secret refs; wire env into **scraper CronJobs only** when `backend: postgres`, reusing `observability.postgresUrl` mapping when override absent.
- [ ] 2.2 Extend `values.schema.json` and `examples/with-scrapers` with a **non-default** commented example for Postgres cursors.
- [ ] 2.3 Extend `helm/tests/with_scrapers_test.yaml` (or new suite) to assert env presence/absence per [DALC-REQ-SCRAPER-CURSOR-003] / [DALC-REQ-SCRAPER-CURSOR-004].

## 3. Verification and traceability

- [ ] 3.1 Add unit tests for Postgres adapter (mock DB or containerized Postgres if repo already patterns that) and regression tests for file mode.
- [ ] 3.2 Run `uv run pytest tests/`, all example `helm unittest -f` loops, `ct lint`, and `python3 scripts/check_spec_traceability.py`.
- [ ] 3.3 On promotion to `openspec/specs/`: assign stable IDs, update `docs/spec-test-traceability.md`, and cite IDs in pytest / helm unittest comments per [DALC-VER-005].

## 4. Documentation

- [ ] 4.1 Update `docs/observability.md` or a short runbook section: when scrapers reuse `HOSTED_AGENT_POSTGRES_URL`, RBAC, connection limits, and migration from file cursors.
- [ ] 4.2 Add `docs/development-log.md` entry when the change lands.
