# Step 10: scraper-cursors-durable-store

`````
# Downstream LLM implementation brief: `scraper-cursors-durable-store`

## 0. Context (read first)

- **Linear checklist:** Step **10** in `docs/openspec-implementation-order.md` — **after** `dedupe-helm-values-observability` (step **1**) for shared DSN / values paths, **`postgres-agent-persistence`** (step **7**) for operational Postgres posture, and **finishing** **`jira-scraper`** (step **8**) / **`slack-scraper`** (step **9**) so watermark/cursor call sites are stable before abstraction.
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) through [`09-slack-scraper-spec.md`](09-slack-scraper-spec.md) — especially **dedupe** + **postgres** for `observability.postgresUrl` → **`HOSTED_AGENT_POSTGRES_URL`** reuse; **08** / **09** for current **`SCRAPER_JOB_CONFIG`**, metrics, and filesystem state layout.
- **Authoritative change bundle:** `openspec/changes/scraper-cursors-durable-store/` — `proposal.md`, `design.md`, `tasks.md`, normative delta **`specs/dalc-scraper-cursor-store/spec.md`** (`[DALC-REQ-SCRAPER-CURSOR-001]` … **`[DALC-REQ-SCRAPER-CURSOR-004]`**).
- **Naming / traceability:** On promotion to `openspec/specs/`, use **`dalc-*`** slug conventions; assign stable **`[DALC-REQ-…]`** on `### Requirement:` lines; wire **ADR 0003** / **DALC-VER-005** (`docs/spec-test-traceability.md`, pytest / helm unittest comments, `python3 scripts/check_spec_traceability.py`).

## 1. Goal

1. **Pluggable cursor store:** Introduce a small runtime abstraction for **opaque** incremental state keyed by **`(integration, scope, logical_key)`** with backends **`file`** (default, backward compatible) and **`postgres`** (durable); **RAG-as-store** stays out of v1 per `design.md`.
2. **Refactor scrapers:** `hosted_agents.scrapers.jira_job` and `hosted_agents.scrapers.slack_job` **SHALL** read/write incremental state only through the abstraction for the paths this change targets (Jira watermark; Slack **`slack_channel`** state / **`watermark_ts`**). Preserve existing RAG payloads, metrics labels, and env names for auth/RAG unless this change explicitly documents a new contract.
3. **Helm:** Optional values (e.g. `scrapers.cursorStore`) such that **`HOSTED_AGENT_POSTGRES_URL`** (or documented override) is injected **only** when Postgres backend is selected — **`[DALC-REQ-SCRAPER-CURSOR-003]`**; ConfigMap **`job.json`** remains non-secret — **`[DALC-REQ-SCRAPER-CURSOR-004]`**.
4. **Relational model:** Documented table + upsert semantics + bounded PK / hashed key for long JQL — **`[DALC-REQ-SCRAPER-CURSOR-002]`**.

## 2. Current watermark / cursor code paths (refactor targets)

### 2.1 Jira (`hosted_agents.scrapers.jira_job`)

- **Path derivation + filesystem root:** `_watermark_path` uses **`JIRA_WATERMARK_DIR`** (default `/tmp/jira-scraper-watermark`), safe scope, SHA-256 prefix of base JQL → JSON filename.
- **Read path:** `_read_watermark(path, overlap_minutes)` loads `last_updated`, applies overlap window, returns JQL watermark string or `None`.
- **Write path:** `_write_watermark(path, iso)` writes `{"last_updated": iso}`.
- **`run()` wiring:** Computes `wm_path` / `wm` / `jql`; after `search_issues`, updates **`max_upd`** and calls **`_write_watermark(wm_path, max_upd)`** before the RAG **`/v1/embed`** loop. **Do not** silently change watermark-vs-embed ordering unless explicitly tasked and covered by new tests (known tension with **`[DALC-REQ-JIRA-SCRAPER-003]`** — treat as product decision).

### 2.2 Slack (`hosted_agents.scrapers.slack_job`)

- **`slack_search`:** No filesystem cursor in current code path — **out of scope** unless a future source adds one.
- **`slack_channel` — `_run_slack_channel`:** State file under **`SLACK_STATE_DIR`** (default `/tmp/slack-scraper-state`), filename `{safe_scope}-{conversationId}.json`; reads **`watermark_ts`**, passes to **`conversations_history`** as **`oldest`** / **`inclusive=False`**; paginates with Slack **`cursor`**; persists **`watermark_ts`** from **`max_seen`** after the history loop and **before** **`/v1/embed`**.

## 3. Entities and interfaces (maximum leverage)

### 3.1 Logical keys (must map 1:1 to today’s files for file backend)

```python
# Conceptual — choose stable string keys for Postgres PK derivation
def jira_cursor_key(base_jql: str) -> str: ...
def slack_channel_cursor_key(conversation_id: str) -> str: ...
```

**Contract:** For **`file`** backend, serialized state **SHALL** round-trip identical to current on-disk JSON for the same inputs (aids migration and regression tests).

### 3.2 Store protocol (new module e.g. `hosted_agents/scrapers/cursor_store.py`)

```python
from typing import Protocol, runtime_checkable

@runtime_checkable
class ScraperCursorStore(Protocol):
    def get_json(self, *, integration: str, scope: str, key: str) -> dict | None: ...
    def put_json(self, *, integration: str, scope: str, key: str, value: dict) -> None: ...
```

**Alternative signatures** (acceptable if documented): `get_state` / `set_state` returning **`str | None`** — then Jira/Slack adapters own JSON encoding. **Pick one** style and use consistently.

```python
def build_cursor_store_from_env() -> ScraperCursorStore: ...
```

**Contract:** **`build_cursor_store_from_env`** reads backend from env (e.g. **`SCRAPER_CURSOR_BACKEND=file|postgres`** per `design.md` / tasks), validates DSN when **`postgres`**, fails fast with operator-actionable errors.

### 3.3 Postgres adapter

```python
class PostgresScraperCursorStore:
    def __init__(self, dsn: str, *, table_name: str = ...) -> None: ...
    def get_json(self, *, integration: str, scope: str, key: str) -> dict | None: ...
    def put_json(self, *, integration: str, scope: str, key: str, value: dict) -> None: ...
```

**Contract ([DALC-REQ-SCRAPER-CURSOR-002]):** PK includes **integration**, **scope**, **bounded key** (hash raw key when over limit); writes are **UPSERT**-safe; value column holds **JSON** (e.g. JSONB). **DDL strategy:** resolve `design.md` open question — lazy **`CREATE TABLE IF NOT EXISTS`** on first use **or** chart one-shot Job — **document** chosen approach in runbook/chart notes.

### 3.4 File adapter (default)

```python
class FileScraperCursorStore:
    """Delegates to JIRA_WATERMARK_DIR / SLACK_STATE_DIR semantics via integration-specific path rules."""
```

### 3.5 Helm ↔ runtime

| Concern | Intent |
|--------|--------|
| DSN on scraper pods | Only when **`cursorStore.backend: postgres`** — **`[DALC-REQ-SCRAPER-CURSOR-003]`** |
| Precedence | Shared **`observability.postgresUrl`** → **`HOSTED_AGENT_POSTGRES_URL`** when override absent; optional scraper-only override if values add it — match `proposal.md` / `design.md` |
| Secrets | DSN only via **`secretKeyRef`** / env — never in ConfigMap — **`[DALC-REQ-SCRAPER-CURSOR-004]`** |

```yaml
# Illustrative values shape (exact keys follow tasks.md + schema work)
scrapers:
  cursorStore:
    backend: file   # | postgres
    # postgresUrlSecretRef: ...  # optional override only if implemented
```

## 4. Spec ↔ tests (TDD; write/adjust tests first)

**Normative source:** `openspec/changes/scraper-cursors-durable-store/specs/dalc-scraper-cursor-store/spec.md`

| ID | Scenario / intent | Evidence |
|----|-------------------|----------|
| `[DALC-REQ-SCRAPER-CURSOR-001]` | Default **file** unchanged | pytest: existing `test_jira_job.py` / `test_slack_job.py` behaviors; add store-level tests that file paths match pre-refactor |
| `[DALC-REQ-SCRAPER-CURSOR-001]` | **Postgres** selected | pytest: `get_json` / `put_json` round-trip (mock connection or container per repo CI patterns) |
| `[DALC-REQ-SCRAPER-CURSOR-002]` | Upsert + bounded key | pytest: repeated `put_json` updates same row; very long JQL uses hash without collision with distinct queries (document cap) |
| `[DALC-REQ-SCRAPER-CURSOR-003]` | Helm conditional DSN | helm unittest: **no** `HOSTED_AGENT_POSTGRES_URL` on scraper pods when agent has Postgres URL but `backend: file`; **has** env when `backend: postgres` |
| `[DALC-REQ-SCRAPER-CURSOR-004]` | No DSN in ConfigMap | helm unittest: scraper ConfigMap `job.json` data keys unchanged; DSN only from Secret/env |

**Gate:**

Canonical commands: [`README.md`](README.md).

```bash
uv sync --all-groups --project helm/src
cd helm/src && uv run pytest tests/test_jira_job.py tests/test_slack_job.py -v --tb=short
# extend to full suite per CI / tasks.md
(cd examples/with-scrapers && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/with_scrapers_test.yaml" .)
python3 scripts/check_spec_traceability.py
```

## 5. Staged execution (tests ride each stage)

### Stage 1 — `cursor_store` module + file adapter

**Tests first:** protocol compliance + Jira/Slack key mapping + round-trip against `tmp_path` matching current JSON shapes.

**Implement:** `FileScraperCursorStore`, `build_cursor_store_from_env` defaulting to **`file`**.

**Green:** pytest above pass with **minimal** edits to `jira_job` / `slack_job` (thin wrapper calls).

### Stage 2 — Postgres adapter + DDL decision

**Tests first:** upsert + long-key hash + optional migration/DDL smoke (marker if needed).

**Implement:** `PostgresScraperCursorStore`, env wiring for DSN, idempotent DDL per resolved strategy.

**Green:** Postgres adapter tests green; file mode still green.

### Stage 3 — Wire jobs + Helm + examples

**Tests first:** extend `test_jira_job.py` / `test_slack_job.py` for **`SCRAPER_CURSOR_BACKEND=postgres`** with faked store or test DB; helm tests from §4.

**Implement:** refactor `_watermark_path` / `_read_watermark` / `_write_watermark` and `_run_slack_channel` state I/O to use store; chart `values.schema.json`, templates (`scraper-cronjobs.yaml` etc.), `examples/with-scrapers` commented snippet.

**Green:** pytest + helm unittest + `ct lint` as in `tasks.md`.

### Stage 4 — Docs + OpenSpec promotion

**Implement:** `docs/observability.md` or runbook section (DSN reuse, limits, file→Postgres migration); `docs/development-log.md` entry; promote delta spec → `openspec/specs/` + matrix + test citations.

**Green:** `python3 scripts/check_spec_traceability.py` exits **0**; CI parity.

## 6. Acceptance checklist

- [ ] Default **file** backend preserves existing operator behavior and tests.
- [ ] **Postgres** backend persists Jira + Slack **`slack_channel`** cursors; bounded keys + upserts per **`[DALC-REQ-SCRAPER-CURSOR-002]`**.
- [ ] Helm meets **`[DALC-REQ-SCRAPER-CURSOR-003]`** / **`[DALC-REQ-SCRAPER-CURSOR-004]`**.
- [ ] DDL / migration story documented; connection lifecycle safe for CronJob (single connection or minimal pool per `design.md`).
- [ ] **DALC-VER-005** complete if SHALLs promoted.
- [ ] No regression in scraper metrics or RAG payload shapes.

## 7. Clarifying questions (human / planner)

1. **DDL posture:** one-shot Helm **Job** vs **lazy `CREATE TABLE`** in scraper — which do maintainers accept?
2. **Watermark vs embed atomicity:** Should this change **fix** Jira/Slack ordering (write cursor only after successful embed) or **strictly** preserve current ordering with tests locked to today’s behavior?
3. **Override env name:** **`HOSTED_AGENT_POSTGRES_URL` only** vs additional **`SCRAPER_POSTGRES_URL`** — which is canonical if both appear?

## 8. Commands summary

```bash
uv sync --all-groups --project helm/src
cd helm/src && uv run pytest tests/test_jira_job.py tests/test_slack_job.py -v --tb=short
(cd examples/with-scrapers && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/with_scrapers_test.yaml" .)
python3 scripts/check_spec_traceability.py
```

See [`README.md`](README.md) for CI-aligned defaults.
`````
