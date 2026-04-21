# ADR 0009: Standard scraper job contract

## Status

Accepted

## Context

Scheduled **scrapers** ingest third-party data into the chart-managed RAG HTTP service. Operators need a single, repeatable contract: how Helm renders workloads, how non-secret job shape is supplied to Python, how integration-specific settings and secrets are injected, and how Prometheus can scrape scraper metrics—without conflating this lane with the **HTTP trigger** path (see ADR 0010).

## Decision

1. **Helm workload shape**  
   For each enabled entry under **`scrapers.jira.jobs`** or **`scrapers.slack.jobs`**, the chart **SHALL** render a **`CronJob`** whose pod mounts a **`ConfigMap`** volume at **`/config`** (read-only) containing **`job.json`**. The scraper container **SHALL** set **`SCRAPER_JOB_CONFIG=/config/job.json`** (path is explicit env; default in code may match this). The chart **SHALL** set **`SCRAPER_INTEGRATION`** to **`jira`** or **`slack`** and run **`python -m agent.scrapers.jira_job`** or **`python -m agent.scrapers.slack_job`** respectively—see **`helm/chart/templates/_manifest_scraper_cronjobs.tpl`** (defines **`declarative-agent-library-chart.manifest.scraperCronjobs`**, included from **`helm/chart/templates/_system_bundled.tpl`**).

2. **`job.json` from values**  
   **`helm/chart/templates/_manifest_scraper_job_configmaps.tpl`** **SHALL** build **`job.json`** as JSON merged from **`scrapers.<integration>.defaults`** and the per-job map, after stripping Helm-only keys **`enabled`**, **`schedule`**, and **`concurrencyPolicy`** (those control rendering only, not the payload; see **`[DALC-REQ-RAG-SCRAPERS-005]`**). Later keys in the job entry win over defaults (**`mergeOverwrite`** semantics).

3. **Per-integration environment (non-secret)**  
   Integration settings that are not part of **`job.json`** **SHALL** continue to be injected as env vars on the scraper container as implemented: e.g. **`JIRA_SITE_URL`**, **`JIRA_WATERMARK_DIR`** from **`scrapers.jira`**; **`SLACK_STATE_DIR`** from **`scrapers.slack.stateDir`**; **`SCRAPER_SCOPE`** from the job’s **`scope`** or a release-derived default; **`SCRAPER_NAME`** as a stable **`jira-<index>`** / **`slack-<index>`** identifier. Credentials **SHALL** use **`secretKeyRef`** (Jira email/token; Slack bot/user tokens)—never placed in **`job.json`**.

4. **RAG embed**  
   Scrapers **SHALL** submit normalized items to the RAG service with **`POST {RAG_SERVICE_URL}/v1/embed`**, where **`RAG_SERVICE_URL`** is the cluster-internal base URL computed when RAG is deployed: **`http://<release-fullname>-rag:<scrapers.ragService.service.port>`** via **`declarative-agent-library-chart.ragInternalBaseUrl`** in **`helm/chart/templates/_helpers.tpl`**. RAG service tunables live under **`scrapers.ragService`** in **`values.yaml`** (no separate top-level **`rag`** key). Runtime composition **SHALL** follow promoted **`[DALC-REQ-SCRAPER-BASE-*]`**: **`hosted_agents/scrapers/base.py`** performs HTTP **`POST /v1/embed`** and post-success cursor commits; **`jira_job`** / **`slack_job`** integrations return **`ScrapedEmbeds`** via **`ScraperIntegration`** only.

5. **Metrics port and scrape pattern**  
   The scraper container **SHALL** expose a TCP port (named **`metrics`**, **`9091`** in the chart) aligned with **`SCRAPER_METRICS_ADDR`** (e.g. **`0.0.0.0:9091`**). Prometheus scrape hints **SHALL** be optional pod annotations when **`observability.prometheusAnnotations.enabled`**: **`prometheus.io/scrape`**, **`prometheus.io/port`**, **`prometheus.io/path=/metrics`**. The **`/metrics`** endpoint is served **in-process** by the scraper (background **`HTTPServer`** on **`SCRAPER_REGISTRY`**), not by a separate sidecar container—see **`helm/src/agent/scrapers/metrics.py`**. Starting that listener **SHALL** be gated on **`observability.plugins.prometheus.enabled`** in Helm (runtime: **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED`**) **and** a non-empty **`SCRAPER_METRICS_ADDR`**; if Prometheus is disabled in the observability plugins config, the scraper **SHALL NOT** bind the metrics port even when **`SCRAPER_METRICS_ADDR`** is set. **`SCRAPER_METRICS_GRACE_SECONDS`** controls shutdown delay so short-lived CronJob pods remain scrapeable briefly after work completes.

6. **CronJob concurrency**  
   Optional per-job **`concurrencyPolicy`** (**`Forbid`**, **`Allow`**, **`Replace`**) **SHALL** be rendered on scraper **`CronJob`** specs from **`scrapers.*.jobs[]`**, defaulting to **`Forbid`** when omitted (**`[DALC-REQ-RAG-SCRAPERS-005]`**). It **SHALL NOT** appear in mounted **`job.json`** (stripped like **`schedule`**).

7. **Non-goals**  
   This contract **SHALL NOT** define the **trigger** HTTP API, **`TriggerBody`**, or inbound **`*-trigger`** bridges (ADR 0010). Enabling the agent trigger deployment **SHALL NOT** by itself deploy RAG; **`declarative-agent-library-chart.ragDeployed`** is true only when at least one scraper job is enabled under **`scrapers.jira`** or **`scrapers.slack`**, matching the comment on **`scrapers.ragService`** in **`values.yaml`**.

## Consequences

- New scraper integrations **SHOULD** extend **`_manifest_scraper_job_configmaps.tpl`** + **`_manifest_scraper_cronjobs.tpl`** (wired into the bundled manifest via **`_system_bundled.tpl`**) with the same ConfigMap mount, **`SCRAPER_JOB_CONFIG`**, **`SCRAPER_INTEGRATION`**, **`RAG_SERVICE_URL`**, and metrics env/port conventions.
- OpenSpec task lists under **`openspec/changes/jira-scraper/`** and **`openspec/changes/slack-scraper/`** remain the working checklist for behavioral completeness; this ADR captures the **Helm/runtime boundary** those tasks assume.
- Operators can rely on one mental model: **CronJob + mounted `job.json` + integration env + secrets**, RAG URL derived from **`scrapers.ragService`**, and metrics on **`9091`** with optional annotation-based scraping.
