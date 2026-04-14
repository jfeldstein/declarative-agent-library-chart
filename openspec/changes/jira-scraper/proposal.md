## Why

Operators need **project-scoped Jira context** (issues, workflow state, ownership, discussion, and issue links) in the shared **RAG** index so hosted agents can answer accurately about delivery status and history. The chart already supports **CronJob scrapers** and the managed **RAG** service, but there is **no first-party Jira scraper** and no **structured `Values.scrapers.jira`** surface—only generic `scrapers.jobs[].extraEnv`, which pushes site URLs, tokens, and field lists into opaque env blobs and duplicates concepts that belong next to other scraper tuning.

## What Changes

- Add a **Jira scraper** entrypoint (Python) that on each run **discovers changed issues** for configured project(s), **fetches issue fields, comments, and links**, normalizes them into the existing **RAG `POST /v1/embed`** contract (deterministic **`entity_id`** per issue, bounded metadata), and records a **durable incremental watermark** so runs stay efficient.
- Introduce **`scrapers.jira`** in **`values.yaml`** / **`values.schema.json`**: shared Jira Cloud settings (site base URL, auth via **Secret** references, default field sets, optional JQL overrides per project) **without** a top-level **`rag`** key and **without** duplicating **agent `observability.*`** keys—Jira scrape config stays under **`scrapers`** only.
- Extend **Helm** (`scraper-cronjobs.yaml` or equivalent) so a job with **`SCRAPER_INTEGRATION=jira`** runs **`hosted_agents.scrapers.jira_job`** (mirroring the **Slack** design direction: integration-based routing rather than hard-coding job names).
- Add **dependencies** (HTTP client already present via **`httpx`**; optional thin **`atlassian-python-api`** only if design/tasks justify it vs direct REST), **examples**, **unit tests** for JQL/watermark/payload shaping, and **bounded** Prometheus **`integration`** labels per **`metrics.py`** checklist.

## Capabilities

### New Capabilities

- `jira-scraper`: Scheduled **Jira Cloud → RAG** ingestion for one or more projects; structured Helm **`scrapers.jira`**; incremental sync via JQL + per-issue comment/link enrichment; documented auth and rate-limit behavior.

### Modified Capabilities

- _(none: existing published **`cfha-rag-from-scrapers`** SHALL rows are unchanged; this change adds behavior under the same `scrapers` umbrella without altering those requirements.)_

## Impact

- **Runtime**: new module under **`hosted_agents.scrapers`**, optional small internal package for Jira REST calls and watermark I/O.
- **Helm**: **`values.yaml`**, **`values.schema.json`**, scraper CronJob template; example values under **`examples/`**.
- **Security**: Jira **API token** or OAuth app credentials via Kubernetes **Secrets**; document required OAuth scopes / classic permissions.
- **CI**: **`uv run pytest`**; if new normative SHALLs are promoted into **`openspec/specs/`** later, follow **[CFHA-VER-005]** traceability (`scripts/check_spec_traceability.py`).
