## 1. API client and watermark

- [ ] 1.1 Implement a small **Jira Cloud REST v3** client (prefer **`httpx`**) with **Basic auth** (email + API token), timeouts, and **429** backoff.
- [ ] 1.2 Implement **watermark** read/write for **`last_successful_updated`** per **(site host, scope, project key)** using the store chosen in **`design.md`** Open Questions (default: file on **PVC** or **ConfigMap** after confirming chart RBAC and size limits).
- [ ] 1.3 Add unit tests for JQL construction (**watermark + overlap**), pagination loop handling (mocked **`nextPageToken`**), and **no secret** logging.

## 2. Fetch and normalize

- [ ] 2.1 Implement **`POST /rest/api/3/search/jql`** driver with explicit **`fields`** list (include **`summary`**, **`description`**, **`status`**, **`assignee`**, **`issuelinks`**, **`updated`**, **`project`**, **`issuetype`**; merge **`scrapers.jira` defaults** and per-project **`extraFields`**).
- [ ] 2.2 For each issue key returned, implement **`GET /rest/api/3/issue/{issueIdOrKey}/comment`** pagination with **`maxCommentsPerIssue`** cap and explicit truncation note in text when capped.
- [ ] 2.3 Normalize into **`reference_job`-compatible** embed payloads: deterministic **`entity_id`**, **`metadata`** (issue key, project, url, `updated`), optional **`relationships`** for **`issuelinks`**.
- [ ] 2.4 Batch **`POST {RAG_SERVICE_URL}/v1/embed`** and wire **`observe_rag_embed_attempt`** / **`observe_scraper_run`** with **`integration=jira`**.

## 3. Helm and values

- [ ] 3.1 Add **`scrapers.jira`** to **`values.yaml`** and **`values.schema.json`** per **[CFHA-REQ-JIRA-SCRAPER-001]** (no top-level **`rag`**; no duplicate **`observability`** keys).
- [ ] 3.2 Update **`scraper-cronjobs.yaml`** to run **`hosted_agents.scrapers.jira_job`** when **`SCRAPER_INTEGRATION`** is **`jira`** per **[CFHA-REQ-JIRA-SCRAPER-002]**.
- [ ] 3.3 Render **env** (and optional **projected file**) from merged **`scrapers.jira`** + job overrides: **`JIRA_SITE_URL`**, secret-derived email/token, **`JIRA_PROJECT_KEYS`** or JSON project list, caps, overlap minutes, optional per-project JQL.

## 4. Examples and verification

- [ ] 4.1 Add **`examples/`** fragment documenting **`scrapers.jira`** + one enabled **`scrapers.jobs`** entry (`SCRAPER_INTEGRATION=jira`, schedule, scope).
- [ ] 4.2 Extend **Helm unittest** (if present) for template command selection for **`jira`** integration.
- [ ] 4.3 Run **`uv run pytest`** for runtime tests; fix failures.
- [ ] 4.4 If any new SHALL is **promoted** into **`openspec/specs/`** root specs, update **`docs/spec-test-traceability.md`** and test citations per **[CFHA-VER-005]**; run **`python3 scripts/check_spec_traceability.py`**.
