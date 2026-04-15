## 1. Dependencies and module skeleton

- [x] 1.1 Add **`slack_sdk`** and **`slack-bolt`** to the runtime **`pyproject.toml`** (with version constraints consistent with repo policy) and refresh the lockfile if the repo uses one for scraper images.
- [x] 1.2 Create **`hosted_agents.scrapers.slack_job`** (module + `run()` entrypoint) following the same patterns as **`jira_job`**: **`RAG_SERVICE_URL`**, **`httpx`** embed client, scraper metrics HTTP lifecycle, **`observe_*`** hooks, non-zero exit on misconfiguration. *(The old **`reference_job`** entrypoint was removed from the chart; do not reintroduce it here.)*

## 2. Configuration and Slack fetch

- [ ] 2.1 Implement parsing + validation for scraper job config: chart mounts **`job.json`**; runtime reads **`SCRAPER_JOB_CONFIG`** (default **`/config/job.json`**). *(Original design text mentioned **`SLACK_SCRAPER_SEARCHES_JSON`**; the shipped integration uses the shared ConfigMap **`job.json`** pattern like Jira.)* Reject invalid config with actionable stderr.
- [ ] 2.2 Implement **`WebClient`**-based Slack fetches per job shape: **`slack_search`** uses Real-time Search **`assistant.search.context`** plus **`conversations.replies`** / **`conversations.history`** for context (not legacy **`search.messages`**). **`slack_channel`** uses incremental **`conversations.history`** with caps and cursor paging. Document per-run limits (**`rtsLimit`**, history page size).
- [ ] 2.3 Normalize selected Slack messages into RAG **`items[]`** with deterministic **`entity_id`** and **`metadata`** (`source`, `slack_channel`, `slack_ts`, etc.). **`relationships`** may remain **`[]`** until thread/permalink fields are modeled explicitly; add **permalink** / thread-root metadata when spec requires it.

## 3. RAG ingest, dedupe, and metrics

- [ ] 3.1 Post **`POST {RAG_SERVICE_URL}/v1/embed`** with the run’s **`items`** (single request per scraper run today; **chunked** multi-POST batching deferred if payload limits require it). Wire **`observe_rag_embed_attempt`** / **`observe_scraper_run`** with bounded **`SCRAPER_INTEGRATION`** (default **`slack`**).
- [x] 3.2 Implement documented **“new or updated”** selection for v1 (minimum: deterministic ids + documented re-embed/upsert behavior); if cross-run persistence is required after RAG inspection, add the smallest durable watermark store and document operator RBAC needs.
- [ ] 3.3 Ensure **no secrets** in logs or metric labels; add unit tests for redaction / label boundedness where applicable.

## 4. Helm and operator docs

- [x] 4.1 Update **`scraper-cronjobs.yaml`** to select **`slack_job`** when the job’s Slack source (**`slack_search`** / **`slack_channel`**) sets **`SCRAPER_INTEGRATION`** to **`slack`**. *(**`reference`** / stub entrypoints were removed from the chart.)*
- [x] 4.2 Extend **`values.schema.json`** (under **`scrapers.slack`**) with documented optional fields for Slack jobs (token secret refs, **`jobs[]`**, RTS/history caps) while preserving **[DALC-REQ-RAG-SCRAPERS-001]** (no top-level **`rag`** key).
- [x] 4.3 Add an **`examples/`** fragment or README section showing a Slack scraper CronJob values block (schedule, **`scrapers.slack`**, secretKeyRef, **`jobs[]`** with **`source`**, and merged **`job.json`** via ConfigMap—not env JSON **`SLACK_SCRAPER_SEARCHES_JSON`**).

## 5. Verification

- [x] 5.1 Add unit tests for JSON parsing, message normalization, and embed payload construction (mock **`WebClient`** / HTTP).
- [x] 5.2 Run **`uv run pytest`** for the runtime test suite and fix failures.
- [ ] 5.3 If new normative **`SHALL`** rows are promoted into **`openspec/specs/`**, update **`docs/spec-test-traceability.md`** and test docstrings per **[DALC-VER-005]**; run **`python3 scripts/check_spec_traceability.py`**.
