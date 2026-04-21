## 1. API client and watermark

- [x] 1.1 Implement a small **Jira Cloud REST v3** client (prefer **`httpx`**) with **Basic auth** (email + API token) and timeouts. **429 / `Retry-After` backoff** is implemented via **`jira_request`** (timeouts via **`httpx.Timeout`** / optional **`JIRA_HTTP_TIMEOUT_SECONDS`**).
- [x] 1.2 Implement **watermark** read/write per **(site host, scope, query hash)** on disk under **`JIRA_WATERMARK_DIR`**. Persisted JSON uses field **`last_updated`** (overlap window uses this value; naming differs from an earlier **`last_successful_updated`** sketch in **`design.md`**).
- [x] 1.3 Unit tests in **`test_jira_job.py`** cover JQL (**watermark + overlap**) and **`nextPageToken`** pagination; assertions stderr does not contain secrets and **`bounded_integration_label`** keeps metric labels bounded.

## 2. Fetch and normalize

- [x] 2.1 Implement **`POST /rest/api/3/search/jql`** driver with explicit **`fields`** list (include **`summary`**, **`description`**, **`status`**, **`assignee`**, **`issuelinks`**, **`updated`**, **`project`**, **`issuetype`**; merge **`scrapers.jira` defaults** and per-project **`extraFields`**).
- [x] 2.2 For each issue key returned, implement **`GET /rest/api/3/issue/{issueIdOrKey}/comment`** pagination with **`maxCommentsPerIssue`** cap and explicit truncation note in text when capped.
- [x] 2.3 Normalize into RAG **`items[]`**: deterministic **`entity_id`**, **`metadata`** (issue key, project, url, `updated`). **`issuelinks`** remain in flattened **`text`**; structured **`relationships[]`** are populated from links (**`RelationshipDecl`** shape).
- [x] 2.4 Batch **`POST {RAG_SERVICE_URL}/v1/embed`** and wire **`observe_rag_embed_attempt`** / **`observe_scraper_run`** with **`integration=jira`**.

## 3. Helm and values

- [x] 3.1 Add **`scrapers.jira`** to **`values.yaml`** and **`values.schema.json`** per **[DALC-REQ-JIRA-SCRAPER-001]** (no top-level **`rag`**; no duplicate **`observability`** keys).
- [x] 3.2 Update **`scraper-cronjobs.yaml`** to run **`agent.scrapers.jira_job`** when **`SCRAPER_INTEGRATION`** is **`jira`** per **[DALC-REQ-JIRA-SCRAPER-002]**.
- [x] 3.3 Render **env** + mounted **`job.json`** from merged **`scrapers.jira`** + job overrides: **`JIRA_SITE_URL`**, **`JIRA_WATERMARK_DIR`**, **`SCRAPER_SCOPE`**, secret-derived email/token; **JQL**, **`extraFields`**, caps, and overlap come from **`job.json`** (not a separate **`JIRA_PROJECT_KEYS`** env—project scope is inside the job payload). Optional per-job **`siteUrl`** / **`watermarkDir`** override parents for env only (stripped from **`job.json`**).

## 4. Examples and verification

- [x] 4.1 Add **`examples/`** fragment documenting **`scrapers.jira`** + one enabled **`scrapers.jobs`** entry (`SCRAPER_INTEGRATION=jira`, schedule, scope).
- [x] 4.2 Extend **Helm unittest** (if present) for template command selection for **`jira`** integration.
- [x] 4.3 Run **`uv run pytest`** for runtime tests; fix failures.
- [x] 4.4 No new promoted SHALLs required traceability updates; **`python3 scripts/check_spec_traceability.py`** passes (strict).
