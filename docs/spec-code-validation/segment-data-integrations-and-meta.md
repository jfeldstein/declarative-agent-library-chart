# Spec vs codebase validation: data integrations and meta (Jira, RAG/scrapers, cursor store, requirement verification)

**Date:** 2026-04-19  
**Worktree:** `wt/agent-n9p1`  
**Scope:** Promoted OpenSpec capabilities: `dalc-jira-tools`, `dalc-jira-trigger`, `dalc-postgres-agent-persistence`, `dalc-rag-from-scrapers`, `dalc-scraper-cursor-store`, `dalc-requirement-verification` (with emphasis on **VER** rows and sampled **REQ**).

## Method

- **Authoritative map:** `docs/spec-test-traceability.md` (matrix rows for each `[DALC-REQ-*]` / `[DALC-VER-*]` ID).  
- **Mechanical gate:** `python3 scripts/check_spec_traceability.py` (strict) — **pass** in this worktree: 83 promoted requirements, matrix aligned.  
- **Evidence existence:** All matrix “Evidence” paths for the six capabilities were present on disk.  
- **Code/review spot checks:** Read spec text, key tests, and selected implementation files to flag **gaps** (test does not fully prove the English SHALL) and **operational / untestable in CI** clauses (cluster behavior, operator procedure, production-only semantics).

---

## Summary GAP table

| Capability | Mechanical traceability | Main residual gaps |
|------------|-------------------------|---------------------|
| `dalc-jira-tools` | OK | “Invocable only during agent run” is architectural, not asserted by tests; REQ-001 uses static `/v1/embed` absence in `tools/jira/*.py`. |
| `dalc-jira-trigger` | OK | Parity with `POST /api/v1/trigger` is integration-level; webhook verification is covered for secret + invalid JSON paths. |
| `dalc-postgres-agent-persistence` | OK | Applying migrations and live DB upgrades are operator/runbook workflows; pytest uses in-process / test doubles. |
| `dalc-rag-from-scrapers` | OK | Chart RAG deployment gates are Helm unittest–level; full cluster wiring not exercised in default PR pytest. |
| `dalc-scraper-cursor-store` | OK | Postgres DSN delivery is validated in rendered manifests + store tests; live CronJob execution is operational. |
| `dalc-requirement-verification` | OK | VER rows are meta; VER-002 matrix evidence is **illustrative sample files**, while enforcement is repo-wide via the traceability script. |

---

## `dalc-jira-tools`

**Matrix:** `[DALC-REQ-JIRA-TOOLS-001]` … `[DALC-REQ-JIRA-TOOLS-006]` → `helm/src/tests/test_jira_tools.py`, `helm/tests/hello_world_test.yaml`, chart values/schema, `helm/src/hosted_agents/tools/README.md`, `helm/src/pyproject.toml`.

| ID | Alignment | Notes |
|----|-----------|--------|
| JIRA-TOOLS-001 | Partial | `test_jira_tools_python_sources_avoid_embed_route` forbids `/v1/embed` in `hosted_agents/tools/jira/*.py`. **Operational / not fully proven:** “only during an active agent run” depends on dispatch/trigger design; README states tools do not call embed by default. |
| JIRA-TOOLS-002 | Strong | README documents non-overlapping env/chart keys vs scraper (`scrapers.jira.auth`) and trigger (`HOSTED_AGENT_JIRA_TRIGGER_*`). Helm evidence ties `jiraTools` in values/schema. |
| JIRA-TOOLS-003 | Strong | Simulated + real-path tests cover search, comment, transition, create, update where scopes allow. |
| JIRA-TOOLS-004 | Strong | JQL required, length cap, bounded search results in tests. |
| JIRA-TOOLS-005 | Strong | `pyproject.toml` declares `httpx`; tests exercise real search via httpx and transport errors. |
| JIRA-TOOLS-006 | Strong | HTTP error mapping and redaction tests; no token in error payload. |

**Operational / CI limits:** Real Atlassian Cloud behavior (permissions, OAuth vs token) is environment-specific; tests use mocks or simulated mode.

---

## `dalc-jira-trigger`

**Matrix:** `[DALC-REQ-JIRA-TRIGGER-001]` … `[DALC-REQ-JIRA-TRIGGER-005]` → `helm/src/tests/test_jira_trigger.py`, chart values/schema, `helm/src/hosted_agents/jira_trigger/README.md`, `helm/src/hosted_agents/metrics.py`.

| ID | Alignment | Notes |
|----|-----------|--------|
| JIRA-TRIGGER-001 | Strong | Issue-updated webhook invokes `run_trigger_graph` (mocked) with captured context. **Opt-in:** `RUN_JIRA_TRIGGER_HTTP_PARITY=1` runs `test_optional_jira_webhook_trigger_context_message_matches_direct_trigger` — full `TestClient` stack (`run_trigger_graph` wrapped only to record contexts) compares `TriggerBody.message` vs an equivalent **`POST /api/v1/trigger`** body built from **`build_jira_trigger_message`**. |
| JIRA-TRIGGER-002 | Strong | Tests assert sources avoid embed route; quick scan: no `/v1/embed` under `hosted_agents/jira_trigger/`. **Operational:** managed RAG disabled unless separately configured — not a live webhook+RAG integration test in default PR. |
| JIRA-TRIGGER-003 | Strong | Bad secret → 401 without graph; invalid JSON → 400 without graph. **Not exhaustively proven:** every future validation branch (e.g. alternate webhook types) would need matching tests if added to code. |
| JIRA-TRIGGER-004 | Strong | README + chart surface distinct keys from scraper batch/watermark settings. |
| JIRA-TRIGGER-005 | Strong | Metrics label test + metrics module patterns; malformed body path rejects without echoing secrets (aligned with handler design). |

---

## `dalc-postgres-agent-persistence`

**Matrix:** `[DALC-REQ-POSTGRES-AGENT-PERSISTENCE-001]` … `[005]` → `helm/src/tests/test_postgres_checkpointer.py`, `test_postgres_observability_repos.py`, `test_migrations_schema.py`, `001_hosted_agents_observability.sql`, `docs/runbook-checkpointing-wandb.md`, `test_postgres_env.py`, `helm/tests/hello_world_test.yaml`, `helm/chart/values.yaml`.

| ID | Alignment | Notes |
|----|-----------|--------|
| POSTGRES-001 | Strong | Constructs Postgres checkpointer when URL valid; fails fast when missing; validates scheme. |
| POSTGRES-002 | Strong | Correlation, feedback, side effects exercised against Postgres test setup. |
| POSTGRES-003 | Strong | Span summary persistence test present. |
| POSTGRES-004 | Strong | Migration SQL + schema tests + runbook on applying migrations. **Operational:** operator must run migrations on real clusters; CI validates artifacts and SQL shape, not a production rollout. |
| POSTGRES-005 | Strong | Memory defaults when Postgres unset; app starts without DB credentials. |

---

## `dalc-rag-from-scrapers`

**Matrix:** `[DALC-REQ-RAG-SCRAPERS-001]`–`004`, `[DALC-REQ-SLACK-SCRAPER-001]`–`005]` → `values.schema.json`, templates, `helm/tests/*`, `helm/src/tests/test_runtime_config.py`, Slack job/metrics tests, `helm/src/pyproject.toml`.

| ID | Alignment | Notes |
|----|-----------|--------|
| RAG-SCRAPERS-001 | Strong | Root `values.schema.json` properties include no top-level `rag` (verified via JSON load). |
| RAG-SCRAPERS-002 | Strong | Helm unittest asserts RAG workload presence/absence vs scraper job gates. |
| RAG-SCRAPERS-003 | Strong | `scrapers.ragService` tunables rendered under enabled scrapers. |
| RAG-SCRAPERS-004 | Strong | Runtime config / template tests tie internal RAG URL to deployment gate. |
| SLACK-SCRAPER-001–005 | Strong | Search list execution, `slack_sdk`/bolt stack in `pyproject.toml`, embed + metrics + redaction tests. **Operational:** live Slack API and cluster networking are outside default PR. |

---

## `dalc-scraper-cursor-store`

**Matrix:** `[DALC-REQ-SCRAPER-CURSOR-001]` … `[004]` → `helm/src/tests/test_cursor_store.py`, `cursor_store.py`, `helm/tests/with_scrapers_test.yaml`, cronjob templates, chart values/schema.

| ID | Alignment | Notes |
|----|-----------|--------|
| SCRAPER-CURSOR-001 | Strong | File store round-trip + Postgres path exercised in tests. |
| SCRAPER-CURSOR-002 | Strong | Postgres DDL/upsert and bounded key behavior tested. |
| SCRAPER-CURSOR-003 | Strong | Helm asserts Postgres env not injected for scrapers when cursor backend is file-only; wired when Postgres cursor selected. |
| SCRAPER-CURSOR-004 | Strong | Manifest tests keep DSN out of non-secret ConfigMap JSON. |

**Operational:** Long-running watermark semantics under load are inferred from tests + docs, not load-tested in CI.

---

## `dalc-requirement-verification` (focus **VER**)

**Matrix:** `[DALC-VER-001]` … `[DALC-VER-005]` — evidence: `scripts/check_spec_traceability.py`; `helm/src/tests/test_o11y_metrics.py` + `helm/tests/hello_world_test.yaml`; `docs/spec-test-traceability.md` + ADR 0003; `.github/workflows/ci.yml` + scheduled workflow + matrix doc; `docs/AGENTS.md` + `.cursor/rules/spec-traceability.mdc`.

| ID | Alignment | Notes |
|----|-----------|--------|
| VER-001 | Strong | Script requires bracketed IDs on `### Requirement:` lines in promoted specs (`ID_PATTERN`, file walk). |
| VER-002 | Strong (meta) | CI validates that **listed** pytest/Helm evidence contains requirement ID strings per matrix paths. Matrix row citing sample tests is **not** a claim that those files alone prove every requirement—only exemplars for reviewers. Full enforcement is **`check_spec_traceability.py`** + matrix updates. |
| VER-003 | Strong | Single-row-per-ID table; waiver rules encoded in script + ADR. |
| VER-004 | Strong | `.github/workflows/ci.yml` runs `python3 scripts/check_spec_traceability.py`; `docs/spec-test-traceability.md` defines CI tiers; scheduled workflow referenced for opt-in integration tier. |
| VER-005 | Strong | `docs/AGENTS.md` documents same-change updates; `.cursor/rules/spec-traceability.mdc` repeats obligation. Root **`AGENTS.md`** also references OpenSpec workflow for contributors using that entry point. |

**Sampled REQ (timeboxed):** `[DALC-REQ-RAG-SCRAPERS-001]` (no root `rag` key) matches schema inspection; `[DALC-REQ-JIRA-TOOLS-006]` matches redaction tests in `test_jira_tools.py`. No contradiction found vs promoted text.

---

## Test evidence (this validation)

- `python3 scripts/check_spec_traceability.py` — exit 0.  
- `cd helm/src && uv run pytest tests/ -q` — **200 passed**, coverage ≥ 85% (full suite per project gate).
