## Context

Scraper entrypoints (**`jira_job`**, **`slack_job`**) share env parsing, **RAG** **`POST /v1/embed`**, **Prometheus** registry on a side port, **cursor/watermark** persistence, and exit codes on misconfiguration. Today those concerns are interleaved with integration code.

The intended split:

- **`base.py`** (shared runtime): loads **`job.json`**, validates env, runs metrics HTTP, **performs all RAG ingest** (**`POST /v1/embed`**), **persists** incremental state via **`cursor_store`**, records scraper metrics, exits non-zero on fatal misconfiguration.
- **Source-specific modules**: **return** normalized in-memory payloads (and optional **proposed** watermark/cursor updates as **data**); talk to **Slack/Jira/…** APIs only; **never** call RAG embed or write cursor storage themselves.

Helm renders one **CronJob** per job; **`concurrencyPolicy: Forbid`** is hard-coded in **`_manifest_scraper_cronjobs.tpl`**.

## Goals / Non-Goals

**Goals:**

- Implement the split above with a **`BaseScraper`** / **`ScraperRuntime`** coordinator in **`hosted_agents/scrapers/base.py`** (name fixed for this change; avoids lingering **`runtime.py`** vs **`base.py`** ambiguity).
- Keep **public metrics names**, **exit codes**, and **RAG payload shapes** stable unless a follow-up explicitly approves breaking changes.
- Allow operators to set **Kubernetes `concurrencyPolicy`** per scraper job via values, **defaulting to `Forbid`** to match today’s behavior.

**Non-Goals:**

- Changing the **managed RAG** deploy gate or **`scrapers.ragService`** layout.
- Replacing **file/postgres cursor** backends or **`job.json`** schema beyond optional new Helm-only keys (**`concurrencyPolicy`** stripped like **`schedule`**).
- Unifying Jira and Slack **remote** APIs into one client (they remain distinct).

## Decisions

1. **`Protocol` vs ABC**  
   Prefer **`typing.Protocol`** with a small **`ScraperIntegration`** protocol implemented inside **`jira_job`** / **`slack_job`**, plus a **`ScraperRuntime`** (or class in **`base.py`**) that owns **`run()`**. **Rationale:** minimizes inheritance depth; integrations are “data providers” only. **Alternative:** ABC **`BaseScraper`** — acceptable if **`Protocol`** complicates **`mypy`** config.

2. **Hook shape: return data, base ingests**  
   Integration methods return **iterables or batches** of structures the runtime can translate into **`POST /v1/embed`** bodies (or pre-built embed payloads **without** sending them). The runtime loop: **fetch returned payloads → embed via shared httpx/RAG client → on success persist watermark/cursor per existing semantics**. Integrations **must not** import or call the embed client. **Rationale:** single ingest path; tests can mock at the runtime boundary. **Alternative:** callbacks from integration into runtime — rejected to keep integrations free of ingest side effects.

3. **Concurrency policy values**  
   Expose **`concurrencyPolicy`** as optional string under each **`jobs[]`** entry; allowed set **`Forbid`**, **`Allow`**, **`Replace`** (Kubernetes v1 batch). Strip from **`job.json`** in ConfigMap merge (Helm-only, like **`schedule`**). Default when omitted: **`Forbid`** in templates. **Rationale:** matches **`batch/v1 CronJob`** API surface without inventing enums.

4. **Module layout**  
   Shared coordinator and **`Protocol`** definitions live in **`hosted_agents/scrapers/base.py`**. **`jira_job.run`** / **`slack_job.run`** remain thin entrypoints calling **`run_scraper(...)`** (name TBD) in **`base.py`**.

## Risks / Trade-offs

- **[Risk] Watermark coupling** — Integrations still need current watermark **inputs** to build JQL or channel cursors; runtime reads **`cursor_store`**, passes values into the integration, integration returns **new candidates** as return values, runtime persists after successful embed. **Mitigation:** document this handoff in **`base.py`** docstring and ADR 0009 pointer.
- **[Risk] Behavior drift during refactor** → Mitigation: run full **`test_jira_job.py`**, **`test_slack_job.py`**, **`test_scraper_metrics.py`**, and Helm unittest suites before merge; prefer mechanical moves before renames.
- **[Risk] `Allow` overlaps cause duplicate embeds or API pressure** → Mitigation: document in **`examples/with-scrapers/README.md`**; default remains **`Forbid`**.

## Migration Plan

1. Land **`base.py`** runtime (**RAG + cursor persistence** centralized) + tests (no Helm change).
2. Migrate **`jira_job`** to **return-data-only** integration + tests.
3. Migrate **`slack_job`** the same way + tests.
4. Add Helm **`concurrencyPolicy`** + schema + tests.
5. Promote specs + matrix + **`check_spec_traceability.py`** + CI.

Rollback: revert commits; chart defaults preserve **`Forbid`**.

## Open Questions

- Whether **`startingDeadlineSeconds`** or **`successfulJobsHistoryLimit`** should be exposed in the same change (defer unless an operator asks).
