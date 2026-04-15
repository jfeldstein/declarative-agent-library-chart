# Step 9: slack-scraper

`````
# Downstream LLM implementation brief: finish `slack-scraper`

## 0. Context (read first)

- **Linear checklist:** Step **9** in `docs/openspec-implementation-order.md` — complete remaining OpenSpec work for **`slack-scraper`** after **`jira-scraper`** (step **8**) and before **`scraper-cursors-durable-store`** (step **10**); DAG shows **`slack-scraper` → `scraper-cursors-durable-store`** (finish scraper code paths before generalizing cursors).
- **Prior implementation specs:** [`01-dedupe-helm-values-observability-spec.md`](01-dedupe-helm-values-observability-spec.md) through [`08-jira-scraper-spec.md`](08-jira-scraper-spec.md) — especially **dedupe** / **postgres** for shared DSN and values layout; **jira-scraper** brief for parallel **job.json** + **watermark-on-filesystem** patterns (`JIRA_WATERMARK_DIR` ↔ `SLACK_STATE_DIR`).
- **Authoritative change bundle:** `openspec/changes/slack-scraper/` — `proposal.md`, `design.md`, `tasks.md`, normative delta **`specs/slack-scraper/spec.md`** (`[DALC-REQ-SLACK-SCRAPER-001]` … **`[DALC-REQ-SLACK-SCRAPER-005]`**).
- **OpenSpec `tasks.md` status:** **all sections checked** except **5.3** (conditional): promotion of normative **`SHALL`** rows into **`openspec/specs/`** → **DALC-VER-005** matrix + test citations + **`python3 scripts/check_spec_traceability.py`**.
- **Spec vs shipped code (planner must reconcile):** The change **`design.md`** describes an ordered list via **`SLACK_SCRAPER_SEARCHES_JSON` / `…_FILE`**. The **merged runtime** uses a **single mounted `job.json`** (**`SCRAPER_JOB_CONFIG`**, default `/config/job.json`) with **`source`**: **`slack_search`** | **`slack_channel`**, Helm **`scrapers.slack.jobs[]`** merged into ConfigMap data (see **`helm/chart/templates/scraper-job-configmaps.yaml`**). Treat the delta spec’s “search list” language as **product intent**; either **update the change-local spec prose** on archive, **promote** SHALLs with wording that matches **`hosted_agents.scrapers.slack_job`**, or document **explicit waivers** — do not assume **`SLACK_SCRAPER_SEARCHES_JSON`** exists in tree.

## 1. Goal (“finish”)

1. **Close the change:** Confirm **`slack-scraper`** is ready to **archive** in OpenSpec, or land minimal remaining work.
2. **Spec promotion (conditional — task 5.3):** If maintainers **promote** Slack scraper SHALLs into **`openspec/specs/dalc-*/spec.md`**, then: stable **`[DALC-REQ-…]`** IDs on promoted `### Requirement:` lines, matrix rows in **`docs/spec-test-traceability.md`**, pytest / helm-unittest comments citing those IDs, and **`python3 scripts/check_spec_traceability.py`** passing.
3. **Optional contract audit:** If promoted SHALLs still describe **`search.messages`** / multi-step JSON env vars only, **either** amend specs to match **`assistant.search.context`** + **`conversations.replies`** / **`conversations.history`** (**`slack_search`**) and **`conversations.history`** + **`watermark_ts`** file under **`SLACK_STATE_DIR`** (**`slack_channel`**), **or** extend implementation — **TDD** if behavior changes.

## 2. Entities and interfaces (maximum leverage)

### 2.1 Mounted job contract (`SCRAPER_JOB_CONFIG` → JSON object)

```python
# Pseudotype: SlackScraperJobConfig (JSON file; path from env)
class SlackScraperJobConfig:
    source: Literal["slack_search", "slack_channel"]
    # slack_search — requires SLACK_USER_TOKEN (xoxp-); optional SLACK_BOT_TOKEN for history/replies
    query: str | None
    contextBeforeMinutes: float | None
    contextAfterMinutes: float | None
    rtsLimit: int | None  # capped (e.g. <= 50)
    # slack_channel — requires SLACK_BOT_TOKEN; incremental watermark in SLACK_STATE_DIR
    conversationId: str | None
```

### 2.2 Environment surface (CronJob → container)

| Variable | Role |
|----------|------|
| `SCRAPER_JOB_CONFIG` | Path to **`job.json`** (chart: `/config/job.json`) |
| `RAG_SERVICE_URL` | Base URL for **`POST /v1/embed`** |
| `SCRAPER_SCOPE` | RAG **scope** + filesystem-safe stem for **`slack_channel`** state file |
| `SCRAPER_INTEGRATION` | Metrics label (default **`slack`**) |
| `SLACK_BOT_TOKEN` / `SLACK_USER_TOKEN` | From **`secretKeyRef`** via **`scrapers.slack.auth`** in values |
| `SLACK_STATE_DIR` | Directory for **`{safe_scope}-{conversationId}.json`** watermark (**`slack_channel`**) |
| `SCRAPER_METRICS_*` | Scraper metrics HTTP per **`metrics.py`** |

### 2.3 Helm values (`scrapers.slack`)

**`scrapers.slack.enabled`**, **`jobs[]`** (each job: **`schedule`**, **`enabled`**, **`source`**, type-specific fields), **`defaults`**, **`auth.*`**, optional **`stateDir`**. **Scraper CronJob CPU/memory:** use shared **`scrapers.resources`** (library **`values.yaml`** / **`values.schema.json`**) — there is **no** per-integration **`scrapers.slack.resources`** today; RAG workload limits are **`scrapers.ragService.resources`**. **Do not** add top-level **`rag`** (align **`[DALC-REQ-RAG-SCRAPERS-001]`** / chart schema).

### 2.4 Runtime module (`hosted_agents.scrapers.slack_job`)

```python
def _load_job_config() -> dict[str, Any]: ...
def _build_items_from_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]: ...
def _embed_payload(scope: str, items: list[dict[str, Any]]) -> dict[str, Any]: ...
def _post_embed(client: httpx.Client, base: str, payload: dict[str, Any], integration: str) -> None: ...
def _run_slack_search(
    user_client: WebClient,
    bot_client: WebClient | None,
    job: dict[str, Any],
    scope: str,
    rag_base: str,
    integration: str,
) -> None: ...
def _run_slack_channel(
    bot: WebClient,
    job: dict[str, Any],
    scope: str,
    rag_base: str,
    integration: str,
) -> None: ...
def run() -> None: ...
```

**RAG payload:** `scope`, `entities`, `relationships`, `items[]` with **`entity_id`** `slack:{team}:{channel}:{ts}`, **`metadata`** (`source`, `slack_channel`, `slack_ts`).

**Metrics:** `observe_rag_embed_attempt`, `observe_scraper_run` with bounded **`integration`** (**`[DALC-REQ-SLACK-SCRAPER-004]`**, **`[DALC-REQ-SLACK-SCRAPER-005]`**).

### 2.5 Helm template routing

**`helm/chart/templates/scraper-cronjobs.yaml`**: Slack CronJob **`command`** ends with **`hosted_agents.scrapers.slack_job`** (not stub). ConfigMap per job: **`scraper-job-configmaps.yaml`**.

## 3. Tests to keep green / extend (TDD)

**Implement or adjust tests first** for any behavior change; then code.

### 3.1 Pytest (`helm/src/tests/test_slack_job.py`)

| Test | Assertions / intent |
|------|----------------------|
| `test_ts_window` | Slack ts float window for context band |
| `test_build_items_from_messages_dedupes` | Same `(channel, ts)` → single item |
| `test_rts_messages_parses_results` | **`assistant.search.context`**-shaped page → hit list |
| `test_run_slack_channel_posts_embed` | Mock **`WebClient`** + **`httpx`**: **`conversations_history`**, **`POST /v1/embed`** |
| `test_run_slack_search_posts_embed` | Mock **`api_call`**, **`conversations_replies`**, **`conversations_history`**, embed |

**Suggested additions (if hardening 003 / rate limits):** RAG 5xx → metric result taxonomy + non-success path; **`Retry-After`** / **`SlackApiError`** handling per **`design.md`**.

### 3.2 Helm unittest (`helm/tests/with_scrapers_test.yaml`)

| `it:` block | Key asserts |
|-------------|-------------|
| `slack_search CronJob runs slack_job module…` | `command` contains **`hosted_agents.scrapers.slack_job`** |
| `slack-only single CronJob runs slack_job module` | Same for slack-only values fixture |

### 3.3 Commands (evidence before “done”)

Canonical snippets: [`README.md`](README.md).

```bash
uv sync --all-groups --project helm/src
cd helm/src && uv run pytest tests/test_slack_job.py -v --tb=short
(cd examples/with-scrapers && helm dependency build --skip-refresh && helm unittest -f "../../helm/tests/with_scrapers_test.yaml" .)
python3 scripts/check_spec_traceability.py   # after any promoted SHALL / matrix edit
```

## 4. Stages (optional; tests ride each stage)

- **Stage A — Traceability only:** Promote SHALLs → matrix + pytest/helm **`[DALC-REQ-SLACK-SCRAPER-00N]`** comments + checker (**task 5.3**).
- **Stage B — Spec/code alignment:** Resolve **`SLACK_SCRAPER_SEARCHES_JSON`** vs **`job.json`** narrative; update **`openspec/changes/slack-scraper/spec.md`** or root specs so scenarios match **`slack_job.py`**.

## 5. Normative IDs (change delta; cite in tests if promoted)

| ID | One-line intent |
|----|-----------------|
| `[DALC-REQ-SLACK-SCRAPER-001]` | Execute operator-defined **fetch plan** each run (list order / completeness as specified) |
| `[DALC-REQ-SLACK-SCRAPER-002]` | **`slack_sdk`** + **`slack-bolt`** in dependency set; public Web API only |
| `[DALC-REQ-SLACK-SCRAPER-003]` | **`/v1/embed`** for selected messages; metadata ids; RAG error taxonomy |
| `[DALC-REQ-SLACK-SCRAPER-004]` | Bounded **`integration`** on scraper metrics |
| `[DALC-REQ-SLACK-SCRAPER-005]` | No secrets in logs or metric labels |

## 6. Out of scope here

- **`scraper-cursors-durable-store`** (step **10**) — refactors watermark/cursor I/O for **`jira_job`** / **`slack_job`**.
- **`slack-trigger`**, **`slack-tools`** — interactive / LLM-time Slack; separate changes.

## 7. Clarifying questions (human / planner)

1. Will **`openspec/changes/slack-scraper/specs/slack-scraper/spec.md`** be **promoted** to **`openspec/specs/`** before archive, or stay change-local with **5.3** N/A?
2. Should normative text describe **`job.json` + `source`** (current) **or** require migrating to **`SLACK_SCRAPER_SEARCHES_JSON`** (original design)?
`````
