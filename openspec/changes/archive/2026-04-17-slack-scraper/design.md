## Context

The chart already runs scraper **CronJobs** that receive **`RAG_SERVICE_URL`**, **`SCRAPER_SCOPE`**, and **`SCRAPER_INTEGRATION`** and call the managed RAG **`POST /v1/embed`** with a JSON payload shaped like the **reference scraper** (`entities`, `relationships`, `items[]` with `text`, `metadata`, optional `entity_id`). The Helm template currently branches on job **name** (`reference` vs everything else → **`stub_job`**). Operators need a **real Slack integration** that executes a **declarative list of searches** each tick and ingests **new** Slack messages into RAG so agents can **`/v1/query`** them.

The user-selected implementation anchor is **[bolt-python](https://github.com/slackapi/bolt-python/)**, which is the Slack-maintained Python framework built on **`slack_sdk`**. Scheduled scraping is **pull-based** and **non-interactive**, so we **do not** need a long-lived Bolt HTTP or Socket Mode receiver in the CronJob path unless we later add optional event-driven ingestion.

## Goals / Non-Goals

**Goals:**

- Add a **Slack scraper** entrypoint invoked by an enabled **`scrapers.jobs[]`** CronJob when configured (via **`SCRAPER_INTEGRATION`** or an explicit Helm command branch—see Decisions).
- Accept a **structured list of search steps** (declarative, ordered) that the job executes **once per run** (for example: Slack **`search.messages`** queries and/or **`conversations.history`** fetches with explicit channel ids and time bounds).
- **Detect novelty** per Slack message (stable `(channel_id, ts)` or thread root) and embed **only new or updated** content since the last successful watermark, using the existing RAG embed contract and **bounded** Prometheus labels (`integration="slack"` or the operator’s **`SCRAPER_INTEGRATION`** value if it remains in the documented bounded set—implementation docs must list allowed values).
- Document **OAuth token** acquisition (bot token typical) and **least-privilege scopes** (`search:read`, `channels:history` / `groups:history`, etc., depending on chosen APIs).
- Declare **Python dependencies** from the Bolt ecosystem: at minimum **`slack_sdk`**, and add **`slack-bolt`** if we reuse Bolt’s **`AuthorizeResult`** / installation patterns for future expansion; the CronJob path uses **`WebClient`** for API calls.

**Non-Goals:**

- Building a full interactive Slack app (slash commands, interactivity, Events API server) **in this change**.
- Real-time ingestion via **Socket Mode** (could be a follow-up).
- Replacing or redesigning the **managed RAG service** itself.
- Unbounded metric cardinality (no channel ids in labels—follow **`metrics.py`** checklist).

## Decisions

1. **Helm routing for the Slack scraper**  
   - **Choice**: Prefer routing by **`SCRAPER_INTEGRATION`** (or a dedicated env) rather than hard-coding more job **names** in Helm. Concretely, extend `scraper-cronjobs.yaml` so **`command`** selects **`hosted_agents.scrapers.slack_job`** when integration is `slack` (exact string TBD but default **`slack`**), keeping **`reference`** on the reference module and **`stub_job`** as the fallback.  
   - **Rationale**: Avoids proliferating name-based `if eq .name` branches and matches how operators already pass **`SCRAPER_INTEGRATION`** for metrics.  
   - **Alternative considered**: Only allow `name: slack` → special-cased like `reference`; rejected as too brittle for multiple Slack jobs.

2. **Configuration shape for “list of searches”**  
   - **Choice**: Provide searches as **JSON** in a single env var (for example **`SLACK_SCRAPER_SEARCHES_JSON`**) validated at startup, **or** a **projected file** path (for example **`SLACK_SCRAPER_SEARCHES_FILE`**) for larger configs. Each element includes: stable **`id`**, **`type`** (`search_messages` | `conversations_history`), type-specific fields (`query`, `channel`, `cursor` policy), and optional **`limit`** / **`oldest`** overrides.  
   - **Rationale**: Keeps Helm values simple (`extraEnv` already exists); avoids CRD.  
   - **Alternative**: One env per search index (`SLACK_SEARCH_0_QUERY=...`); rejected as unwieldy for many searches.

3. **Novelty / dedupe**  
   - **Choice**: Persist a **per-search watermark** (latest `ts` seen) in a small **Kubernetes-friendly store**: simplest v1 is **ConfigMap** (if RBAC allows) **or** embed-only idempotency relying on RAG upsert semantics—**design default**: maintain **in-memory per-run** plus **document** that v1 may re-embed unless RAG dedupes by `metadata.slack_team_id+channel+ts`; **preferred** follow-up is operator-provided **PVC** or **object store**. For MVP in design: use **stable `entity_id`** per message in RAG payload so re-embed is an **upsert**, not duplicate rows, if the RAG service supports it; otherwise store last **`ts`** in a **sidecar file on emptyDir** (lost on reschedule) — **tasks** should pick the repo’s actual RAG behavior after code inspection.  
   - **Rationale**: User asked for “new results”; true cross-run dedupe needs persistence—call this out in **Open Questions** if product wants strict cross-run dedupe without RAG upsert.

   _Correction for clarity_: The design should recommend **deterministic `entity_id`** per Slack message for graph/RAG upsert and minimize duplicates; cross-run watermarks can be **phase 2** if not already supported.

4. **bolt-python vs raw `slack_sdk`**  
   - **Choice**: Add **`slack-bolt`** and **`slack_sdk`** dependencies; implement CronJob using **`WebClient(token=...)`** from **`slack_sdk`**. Optionally construct a **`App`** without starting a server if it helps share middleware for retries/logging—only if it reduces code.  
   - **Rationale**: Satisfies “use bolt-python” while keeping the CronJob simple.  
   - **Alternative**: `slack_sdk` only; rejected because the request explicitly names the Bolt project.

5. **Token injection**  
   - **Choice**: Read **`SLACK_BOT_TOKEN`** (or `xoxb-...`) from env populated by **`secretKeyRef`** in values example; never log token.  
   - **Rationale**: Matches Kubernetes patterns already implied by `extraEnv`.

## Risks / Trade-offs

- **[Risk] Slack API rate limits** → Mitigation: sequential searches with backoff; respect `Retry-After`; cap messages per run.  
- **[Risk] Re-embedding duplicates** if RAG lacks upsert-by-id → Mitigation: define **`entity_id`** = deterministic slack message uri; verify RAG storage semantics in implementation tasks.  
- **[Risk] Over-broad `search.messages`** returning noise → Mitigation: require explicit queries per search step; document tuning.  
- **[Risk] Bolt dependency weight** → Mitigation: pin minimal compatible versions; only import needed modules.

## Migration Plan

1. Ship new Python module + dependencies in the runtime image used by scrapers.  
2. Update Helm template + schema with **non-breaking** defaults (no Slack job until operator adds one).  
3. Operators add a **`scrapers.jobs`** entry with schedule, `SCRAPER_INTEGRATION=slack`, token secret, and searches JSON.  
4. Rollback: disable job or remove env; CronJob stops; RAG data remains (manual purge if needed—out of scope).

## Open Questions

- **Watermark persistence**: confirm whether the RAG service treats repeated **`entity_id`** as upsert; if not, pick **PVC** vs **ConfigMap** vs external store for `last_ts` per search `id`.  
- **Exact search types for v1**: confirm product wants **`search.messages` only**, **`conversations.history` only**, or **both** in the first release.
