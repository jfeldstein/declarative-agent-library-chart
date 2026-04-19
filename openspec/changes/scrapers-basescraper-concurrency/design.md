## Context

Scraper entrypoints (**`jira_job`**, **`slack_job`**) share env parsing, **`httpx`** clients, **RAG** **`POST /v1/embed`**, **Prometheus** registry on a side port, **cursor/watermark** persistence, and exit codes on misconfiguration. Integration-specific code should stay limited to **remote API calls**, **pagination**, and **mapping remote JSON → normalized embed items** (plus relationships metadata). Helm renders one **CronJob** per job; **`concurrencyPolicy: Forbid`** is hard-coded in **`_manifest_scraper_cronjobs.tpl`**.

## Goals / Non-Goals

**Goals:**

- Define a **`BaseScraper`** (prefer **`typing.Protocol`** + structural subtyping for testability, or an **ABC** if explicit `super()` workflow is clearer) so **`run()`** lives in one place.
- Keep **public metrics names**, **exit codes**, and **RAG payload shapes** stable unless a follow-up explicitly approves breaking changes.
- Allow operators to set **Kubernetes `concurrencyPolicy`** per scraper job via values, **defaulting to `Forbid`** to match today’s behavior.

**Non-Goals:**

- Changing the **managed RAG** deploy gate or **`scrapers.ragService`** layout.
- Replacing **file/postgres cursor** backends or **`job.json`** schema beyond optional new Helm-only keys (**`concurrencyPolicy`** stripped like **`schedule`**).
- Unifying Jira and Slack **remote** APIs into one client (they remain distinct).

## Decisions

1. **`Protocol` vs ABC**  
   Prefer **`typing.Protocol`** with a small **`ScraperIntegration`** protocol implemented by private modules or nested classes inside **`jira_job`** / **`slack_job`**, plus a **`ScraperRuntime`** helper that owns **`run()`**. **Rationale:** minimizes inheritance depth; keeps typing-friendly seams for tests. **Alternative:** ABC with concrete `JiraScraper(BaseScraper)` — slightly heavier but familiar; choose ABC if **`Protocol`** complicates **`mypy`** config.

2. **Hook shape**  
   **`fetch_work_units()` → list or iterator** of **`NormalizedChunk`** dataclasses (text, **`entity_id`**, **metadata**, optional **relationships**) rather than callbacks from the base into httpx. **Rationale:** easier to test mapping in isolation. **Alternative:** template-method with abstract **`_run_query`** — acceptable if it matches existing control flow more closely.

3. **Concurrency policy values**  
   Expose **`concurrencyPolicy`** as optional string under each **`jobs[]`** entry; allowed set **`Forbid`**, **`Allow`**, **`Replace`** (Kubernetes v1 batch). Strip from **`job.json`** in ConfigMap merge (Helm-only, like **`schedule`**). Default when omitted: **`Forbid`** in templates. **Rationale:** matches **`batch/v1 CronJob`** API surface without inventing enums.

4. **Ordering refactor**  
   Extract shared code to **`hosted_agents/scrapers/runtime.py`** or **`base.py`**; keep **`jira_job.run`** and **`slack_job.run`** as thin **`if __name__ == "__main__"`** wrappers calling **`ScraperRuntime.main(JiraIntegration())`** for stable **`python -m`** entrypoints.

## Risks / Trade-offs

- **[Risk] Behavior drift during refactor** → Mitigation: run full **`test_jira_job.py`**, **`test_slack_job.py`**, **`test_scraper_metrics.py`**, and Helm unittest suites before merge; prefer mechanical moves before renames.
- **[Risk] `Allow` overlaps cause duplicate embeds or API pressure** → Mitigation: document in **`examples/with-scrapers/README.md`**; default remains **`Forbid`**.
- **[Risk] Protocol typing gaps** → Mitigation: match existing **`pyproject`** typing discipline; add focused unit tests on the runtime.

## Migration Plan

1. Land **`BaseScraper` / runtime** with **`jira_job`** migrated (no Helm change).
2. Migrate **`slack_job`**.
3. Add Helm **`concurrencyPolicy`** + schema + unittest assertions.
4. Promote specs + matrix + **`check_spec_traceability.py`**.

Rollback: revert commits; chart defaults preserve **`Forbid`**.

## Open Questions

- Whether **`startingDeadlineSeconds`** or **`successfulJobsHistoryLimit`** should be exposed in the same change (defer unless an operator asks).
- Exact name for the runtime module (**`runtime.py`** vs **`base.py`**) — resolve during implementation for import clarity.
