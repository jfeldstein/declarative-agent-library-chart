## Context

The chart runs scraper **CronJobs** that call the managed RAG **`POST /v1/embed`** API using the same payload shape as **`reference_job`** (`scope`, `entities`, optional `relationships`, `items[]` with `text`, `metadata`, `entity_id`). Helm today branches on job **`name`** (`reference` vs **`stub_job`**). The **slack-scraper** change set establishes a precedent: route by **`SCRAPER_INTEGRATION`** to avoid name-based `if` sprawl. Operators want **`Values.scrapers.jira`** as the **single structured place** for Jira Cloud site URL, projects, field selection, and secret references—**not** duplicated under **`observability`** (which remains for agent checkpointing, W&B, Slack feedback, etc.).

**Jira Cloud** exposes **REST API v3** under `https://<site>.atlassian.net/rest/api/3` (see [Issue search](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/) and [Issues](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issues/)).

## Goals / Non-Goals

**Goals:**

- **Incremental sync**: each run processes issues **created or updated** since a persisted **watermark** (per scope: e.g. project key or job `scope`), with a small **time overlap** (recommended **5 minutes**) to tolerate clock skew and API ordering edge cases.
- **Rich issue slice**: for each candidate issue, material available to the model SHALL include at least **summary**, **description** (plain text where possible), **status** (workflow stage), **assignee** (display name / account id), **issue links** (outward/inward type + linked key + summary if returned), and **all comments** (author, created, body text), subject to operator caps.
- **Helm**: add **`scrapers.jira`** with documented defaults; render **env vars** (or a projected **JSON** file) for the Jira job container; keep **[DALC-REQ-RAG-SCRAPERS-001]** (no top-level **`rag`** key).
- **Metrics**: bounded **`SCRAPER_INTEGRATION`** / Prometheus **`integration`** label value **`jira`** (or operator override if still within the repo’s **bounded set** documented in **`metrics.py`**).

**Non-Goals:**

- **Jira Data Center / Server** variants with different URL shapes (document as follow-up unless trivially the same client with **`siteUrl`**).
- **Webhooks** or streaming **Forge** triggers (CronJob pull model only here).
- **Bi-directional** writes (create/transition issues) or **full changelog history** for every field on every run (optional later via `expand=changelog` on selective issues).

## Decisions

1. **Primary discovery API — enhanced JQL search**  
   - **Choice**: Use **`POST /rest/api/3/search/jql`** (Jira Cloud **enhanced search**) as the driver for “what changed,” with body fields: **`jql`**, **`maxResults`**, **`fields`** (explicit list), and pagination via **`nextPageToken`** (and/or documented continuation fields returned by the API).  
   - **Rationale**: Atlassian is deprecating legacy **`/rest/api/3/search`**; enhanced search is the supported path for Cloud and returns stable issue **ids/keys** plus requested **fields** for batching.  
   - **Alternatives considered**: (a) **`GET /rest/api/3/search/jql`** with long query strings — rejected for URL length and encoding pain; (b) only **`GET /rest/api/3/issue/{key}`** in a loop without JQL — rejected (no project-wide incremental set).

2. **JQL for “stay up to date”**  
   - **Choice**: Default JQL template: `project = "<KEY>" AND updated >= "<WATERMARK_ISO>" ORDER BY updated ASC` where **`<WATERMARK_ISO>`** is the stored checkpoint **minus overlap**. Operators MAY override with **`scrapers.jira.projects[].jql`** that **must** still be constrained to the intended project (validated or documented as operator responsibility).  
   - **Rationale**: **`updated`** is indexed and matches “anything touched” (fields, comments, links, transitions).  
   - **Alternatives considered**: changelog polling — heavier and more calls; **`ORDER BY key`** + key cursor — weaker for “updated” ordering across types.

3. **Comments and large fields**  
   - **Choice**: After search returns keys, call **`GET /rest/api/3/issue/{issueIdOrKey}/comment`** with pagination (`startAt` / `maxResults` per [Comments API](https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-comments/)) for each issue in the batch (respect a **max issues per run** and **max comments per issue** cap). Merge comment bodies into the normalized text or attach as separate **`items[]`** chunks sharing the same **`entity_id`** with `metadata.part=comments` (implementation picks one; prefer **single consolidated textual view** per issue for v1 if under embed size limits, else **split chunks** with stable ids in metadata).  
   - **Rationale**: Issue **`fields.comment`** in search responses is often **truncated**; dedicated comment pagination is reliable.  
   - **Alternative**: rely on `fields=comment` only — rejected for completeness.

4. **Linked issues**  
   - **Choice**: Request **`issuelinks`** in search/`GET issue` **fields** list; serialize outward/inward **`type`**, **`inwardIssue`/`outwardIssue` key + summary** into text and optional **`relationships`** edges in the embed payload (`source`/`target` issue keys, `relationship_type` string).  
   - **Rationale**: satisfies “linked issues” without a separate graph API.

5. **Stage / assignee**  
   - **Choice**: Always request **`status`** and **`assignee`**. Allow **`scrapers.jira.projects[].extraFields`** (array of field ids) for boards using custom **“Stage”** columns stored as custom fields.  
   - **Rationale**: “Stage” is not a single universal Jira field id; configurability avoids wrong assumptions.

6. **Authentication**  
   - **Choice**: **HTTP Basic** with **Atlassian account email + API token** from Kubernetes **Secrets** (env `JIRA_EMAIL` + `JIRA_API_TOKEN` or combined secret keys documented in values).  
   - **Rationale**: simplest for CronJobs.  
   - **Alternative**: OAuth 2.0 (3LO) — document as future if needed for enterprise policies.

7. **Watermark storage**  
   - **Choice**: Persist **`last_successful_updated`** (ISO-8601, UTC) per **(site, project key, scraper scope)** in a **small durable store**: preferred order after code audit—**(1)** if RAG supports idempotent **`entity_id`** upserts only, still keep watermark **outside** RAG to limit API calls; **(2)** **PVC** file or **ConfigMap** (if size < 1Mi and RBAC acceptable); **(3)** operator-injected **emptyDir** path for throwaway mode (full re-query each run — not default).  
   - **Rationale**: JQL `updated >=` needs a cursor independent of embed dedupe.

8. **Helm shape — `scrapers.jira`**  
   - **Choice**: Example structure (exact keys finalized in implementation):  
     - **`siteUrl`**: `https://your-domain.atlassian.net`  
     - **`auth`**: `emailFrom` / `apiToken` **secretKeyRef** (or `existingSecret` + key names)  
     - **`projects[]`**: `key`, optional `jql`, optional `extraFields[]`, optional `displayName` for docs only  
     - **`defaults`**: `maxIssuesPerRun`, `maxCommentsPerIssue`, `overlapMinutes`, `fields` (optional override of built-in default field list)  
   - **`scrapers.jobs[]`** entries set **`SCRAPER_INTEGRATION: jira`** and optionally **`scope`**; the template **merges** job-level overrides with **`scrapers.jira`** to build env.  
   - **Rationale**: answers **`Values.scrapers.jira.??`** with one documented object; avoids copying the same env into every job.

9. **Observability dedupe**  
   - **Choice**: Do **not** add Jira tokens, DSNs, or W&B knobs under **`scrapers.jira`** that duplicate **`observability.*`**. Scraper containers already inherit chart patterns for metrics (`SCRAPER_METRICS_*`); Jira-specific knobs are **API/rate/embed** only.

## Risks / Trade-offs

- **[Risk] Jira rate limits (429)** → Mitigation: exponential backoff, cap **`maxIssuesPerRun`**, sequential comment fetches with jitter.  
- **[Risk] Large issues (huge descriptions / comment threads)** → Mitigation: byte cap per issue; truncate with explicit marker in text; configurable caps.  
- **[Risk] `nextPageToken` / pagination quirks** → Mitigation: integration test against documented response shape; fallback logging + safe abort rather than silent partial sync.  
- **[Risk] Custom fields vary by project** → Mitigation: `extraFields[]` and documented discovery link for field ids.

## Migration Plan

1. Land Python **`jira_job`** + Helm **`scrapers.jira`** + template routing behind **`SCRAPER_INTEGRATION=jira`**.  
2. Operators add **`scrapers.jira`** + enabled job; first run establishes watermark after optional bootstrap window.  
3. Rollback: disable job; remove secrets; RAG chunks remain until purged manually (out of scope).

## Open Questions

- **Exact watermark store** for this repo’s deployment targets (ConfigMap vs PVC vs sidecar) — resolve during implementation when weighing RBAC and multi-replica scrapers (**CronJob** is typically single pod per run — file on PVC or S3-compatible optional backend).  
- Whether to add **`atlassian-python-api`** vs **raw `httpx`** only — default **raw REST** unless SDK measurably reduces maintenance.
