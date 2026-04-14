## 1. Dependencies and module skeleton

- [x] 1.1 Add **`slack_sdk`** and **`slack-bolt`** to the runtime **`pyproject.toml`** (with version constraints consistent with repo policy) and refresh the lockfile if the repo uses one for scraper images.
- [x] 1.2 Create **`hosted_agents.scrapers.slack_job`** (module + `run()` entrypoint) mirroring **`reference_job`** patterns: **`RAG_SERVICE_URL`**, **`httpx`** embed client, metrics start/stop, non-zero exit on misconfiguration.

## 2. Configuration and Slack fetch

- [x] 2.1 Implement parsing + validation for **`SLACK_SCRAPER_SEARCHES_JSON`** (and optional file-based path if included) per **`design.md`**; reject invalid lists with actionable stderr messages.
- [x] 2.2 Implement **`WebClient`**-based executors for **`search.messages`** and **`conversations.history`** (as scoped for v1), including pagination caps and documented per-run limits.
- [x] 2.3 Normalize selected Slack messages into RAG **`items[]`** entries with deterministic **`entity_id`** / **`metadata`** keys (team, channel, `ts`, thread root, permalink) and optional **`relationships`** when thread parent is known.

## 3. RAG ingest, dedupe, and metrics

- [x] 3.1 Post **`POST {RAG_SERVICE_URL}/v1/embed`** batches (respecting documented payload size limits) and wire **`observe_rag_embed_attempt`** / **`observe_scraper_run`** with bounded **`SCRAPER_INTEGRATION`** (default **`slack`**).
- [x] 3.2 Implement documented **“new or updated”** selection for v1 (minimum: deterministic ids + documented re-embed/upsert behavior); if cross-run persistence is required after RAG inspection, add the smallest durable watermark store and document operator RBAC needs.
- [x] 3.3 Ensure **no secrets** in logs or metric labels; add unit tests for redaction / label boundedness where applicable.

## 4. Helm and operator docs

- [x] 4.1 Update **`scraper-cronjobs.yaml`** to select **`slack_job`** when **`SCRAPER_INTEGRATION`** is **`slack`** (per design), without breaking **`reference`** or the stub fallback.
- [x] 4.2 Extend **`values.schema.json`** (under **`scrapers`**) with documented optional fields or patterns for Slack jobs (token secret refs, searches JSON) while preserving **[DALC-REQ-RAG-SCRAPERS-001]** (no top-level **`rag`** key).
- [x] 4.3 Add an **`examples/`** fragment or README section showing a Slack scraper CronJob values block (schedule, env, secretKeyRef, example **`SLACK_SCRAPER_SEARCHES_JSON`**).

## 5. Verification

- [x] 5.1 Add unit tests for JSON parsing, message normalization, and embed payload construction (mock **`WebClient`** / HTTP).
- [x] 5.2 Run **`uv run pytest`** for the runtime test suite and fix failures.
- [ ] 5.3 If new normative **`SHALL`** rows are promoted into **`openspec/specs/`**, update **`docs/spec-test-traceability.md`** and test docstrings per **[DALC-VER-005]**; run **`python3 scripts/check_spec_traceability.py`**.
