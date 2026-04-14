# Step 8: jira-scraper

`````
# Downstream LLM implementation brief: finish `jira-scraper`

## 0. Context (read first)

- **Linear checklist:** Step **8** in `docs/openspec-implementation-order.md` — complete remaining OpenSpec work for **`jira-scraper`** before **`slack-scraper`** (step **9**) and **`scraper-cursors-durable-store`** (step **10**); DAG shows **`jira-scraper` → `scraper-cursors-durable-store`** (finish scraper code paths first).
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) through [`07-postgres-agent-persistence-spec.md`](07-postgres-agent-persistence-spec.md) — especially **dedupe** (scraper/env + o11y paths charts still reference) and **postgres** (future cursor store DSN story).
- **Authoritative change bundle:** `openspec/changes/jira-scraper/` — `proposal.md`, `design.md`, `tasks.md`, normative delta **`specs/jira-scraper/spec.md`** (`[DALC-REQ-JIRA-SCRAPER-001]` … **`[DALC-REQ-JIRA-SCRAPER-005]`**).
- **OpenSpec `tasks.md` status:** **13/14 checked**; the only **unchecked** item is **4.4** (promotion + **DALC-VER-005** traceability **if** SHALLs move to `openspec/specs/` root).

## 1. Goal (“finish”)

1. **Close the change:** Either confirm **`jira-scraper`** is ready to **archive** in OpenSpec (`openspec archive` workflow per project skill), or land the minimal remaining work below.
2. **Spec promotion (conditional):** If maintainers **promote** Jira scraper SHALLs from the change delta into **`openspec/specs/dalc-*/spec.md`**, then **must** complete **task 4.4**: stable **`[DALC-REQ-…]`** IDs on promoted `### Requirement:` lines, matrix rows in **`docs/spec-test-traceability.md`**, pytest / helm-unittest comments citing those IDs, and **`python3 scripts/check_spec_traceability.py`** passing in CI.
3. **Contract audit (recommended):** Reconcile runtime behavior with **`[DALC-REQ-JIRA-SCRAPER-003]`** (watermark advanced only after durable RAG success / documented atomicity) and **`design.md`** (429 backoff, caps). **TDD:** extend failing tests first, then implementation.

## 2. Entities and interfaces (maximum leverage)

### 2.1 Mounted job contract (`SCRAPER_JOB_CONFIG` → JSON object)

```python
# Pseudotype: JiraScraperJobConfig (JSON file)
class JiraScraperJobConfig:
    source: str  # SHALL be "jira" (case-insensitive)
    query: str  # base JQL; watermark clause appended by runtime
    maxIssuesPerRun: int
    maxCommentsPerIssue: int
    overlapMinutes: int
    extraFields: list[str] | None  # merged after built-in default field list
```

### 2.2 Environment surface (CronJob → container)

| Variable | Role |
|----------|------|
| `JIRA_SITE_URL` | `https://…atlassian.net` base (no path) |
| `JIRA_EMAIL`, `JIRA_API_TOKEN` | Basic auth to Jira Cloud |
| `JIRA_WATERMARK_DIR` | Directory for per-scope/query-hash watermark JSON |
| `SCRAPER_JOB_CONFIG` | Path to job JSON (chart: `/config/job.json`) |
| `RAG_SERVICE_URL` | Base URL for `POST /v1/embed` |
| `SCRAPER_SCOPE` | Namespace for watermark filename |
| `SCRAPER_INTEGRATION` | Metrics label source (default `jira`) |
| `SCRAPER_METRICS_*` | Inherited scraper metrics HTTP per `metrics.py` |

### 2.3 Helm values (`scrapers.jira`)

Chart today uses a dedicated subtree (see **`values.yaml`** / **`values.schema.json`**): e.g. **`scrapers.jira.enabled`**, **`siteUrl`**, **`auth.*` Secret refs**, **`jobs[]`** (schedule, scope, query, caps), optional **`watermarkDir`**. **Do not** introduce top-level **`rag`** or duplicate agent **`observability.*`** keys under **`scrapers.jira`** (`[DALC-REQ-JIRA-SCRAPER-001]`).

### 2.4 Runtime module (`hosted_agents.scrapers.jira_job`)

```python
def search_issues(
    client: httpx.Client,
    base: str,
    jql: str,
    fields: list[str],
    max_results: int,
) -> list[dict[str, Any]]: ...

def _build_jql(base_query: str, watermark_iso: str | None) -> str: ...

def _fetch_comments(
    client: httpx.Client,
    base: str,
    issue_key: str,
    cap: int,
) -> list[dict[str, Any]]: ...

def _embed_for_issue(scope: str, issue: dict[str, Any], text: str) -> dict[str, Any]: ...

def run() -> None: ...
```

**RAG payload:** `reference_job`-compatible dict with deterministic **`entity_id`** (e.g. `jira:{KEY}`), **`items[]`**, optional **`relationships`** when links are modeled (`[DALC-REQ-JIRA-SCRAPER-004]`).

**Metrics:** `observe_rag_embed_attempt`, `observe_scraper_run` with bounded **`integration`** (`[DALC-REQ-JIRA-SCRAPER-005]`).

### 2.5 Helm template routing (`[DALC-REQ-JIRA-SCRAPER-002]`)

CronJob container **`command`** SHALL end with **`hosted_agents.scrapers.jira_job`** (not `stub_job`) for Jira scraper jobs — see **`helm/chart/templates/scraper-cronjobs.yaml`**.

## 3. Tests to keep green / extend (TDD)

**Implement or adjust tests first** for any behavior change; then code.

### 3.1 Pytest (`helm/src/tests/test_jira_job.py`)

| Test | Assertions / intent |
|------|---------------------|
| `test_search_issues_single_page` | POST `/rest/api/3/search/jql`, JQL echo, single-page issues |
| `test_search_issues_next_page_token` | Second request carries `nextPageToken`; merged issue keys |
| `test_build_jql_with_watermark` | `updated >=` clause composited with base query |
| `test_watermark_roundtrip` | `_write_watermark` / `_read_watermark` + overlap shift |
| `test_fetch_comments_empty` | GET `…/comment` path, empty list |
| `test_run_jira_end_to_end_mocked` | Full `run()` with MockTransport: search + comments + `/v1/embed` |
| `test_issue_text_builds` | Normalized text includes key, summary, status, assignee |

**Suggested new tests (if fixing 003 / 429):** partial RAG failure does not advance watermark; 429 on search/comments triggers retry/backoff per `design.md`.

### 3.2 Helm unittest (`helm/tests/with_scrapers_test.yaml`)

| `it:` block | Key asserts |
|-------------|-------------|
| `jira CronJob runs jira_job module…` | `command[2] == hosted_agents.scrapers.jira_job`, `SCRAPER_JOB_CONFIG` |
| `jira-only single CronJob runs jira_job module` | Same for `values.jira-only.yaml` |

### 3.3 Commands (evidence before “done”)

```bash
cd helm && uv run pytest src/tests/test_jira_job.py -v --tb=short
helm unittest -f tests/with_scrapers_test.yaml .
python3 scripts/check_spec_traceability.py   # required after any promoted SHALL / matrix edit
```

## 4. Stages (optional; tests ride each stage)

- **Stage A — Traceability only:** If promoting specs → matrix + comments + checker only (no runtime change).
- **Stage B — Contract hardening:** Watermark vs embed ordering, 429 behavior, byte caps — **each** lands with new/updated pytest + helm tests as above.

## 5. Out of scope here

- **`jira-bot`**, **`jira-tools`**, **`slack-scraper`** completion — separate OpenSpec changes.
- **Data Center / Server** Jira URL shapes — `design.md` non-goal unless trivially supported.

## 6. Clarifying questions (human / planner)

1. Will **`openspec/changes/jira-scraper/specs/jira-scraper/spec.md`** be **promoted** into **`openspec/specs/`** before archive, or remain change-local?
2. Should watermark advancement be **strictly after** all embeds succeed (batch), or per-issue with idempotent RAG — which atomicity story do maintainers want documented?
`````
