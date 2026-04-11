## Context

The Declarative Agent Library Helm chart today exposes a top-level **`rag`** subtree (`enabled`, `replicaCount`, `service`, `resources`, `prometheusAnnotations`). RAG Deployment/Service and scrape hints are toggled independently of **`o11y`**, even though operators who enable Prometheus annotations usually want **every** in-cluster metrics endpoint the chart owns to be discoverable the same way. RAG exists primarily to support **scraper CronJobs** that POST embeddings into the RAG API; keeping a separate `rag.enabled` forces operators to coordinate two knobs (`rag.enabled` and `scrapers.jobs`) for the common path.

## Goals / Non-Goals

**Goals:**

- Remove **`rag` as a top-level values key**; document a single scraper-driven rule for deploying the managed RAG workload.
- Define a **nested** values object for RAG **tuning only** (replicas, service port/type, resources) under the scraper subsystem.
- Apply **`o11y.prometheusAnnotations.enabled`** to **both** agent and RAG Pod/Services when RAG is deployed (same for **`o11y.serviceMonitor.enabled`** vs a separate RAG-only flag).
- Update schema, examples, CI, and integration fixtures to match.

**Non-Goals:**

- Changing RAG **application** HTTP API or metric names (`agent_runtime_rag_*`).
- Adding a new way to deploy RAG **without** any enabled scraper (explicitly out of scope per product decision: RAG follows scrapers).
- Merging agent and RAG into a single Deployment.

## Decisions

1. **RAG deploy gate**  
   **Decision:** Render RAG Deployment, RAG Service, and (when `o11y.serviceMonitor.enabled`) RAG `ServiceMonitor` **if and only if** `scrapers.jobs` contains **at least one job with `enabled: true`**.  
   **Rationale:** Matches “RAG is on when scrapers need it”; empty or all-disabled job lists imply no RAG.  
   **Alternatives considered:** (a) Separate `scrapers.rag.enabled` — rejected (second toggle); (b) RAG on if `jobs` non-empty regardless of `enabled` — rejected (would deploy RAG for disabled CronJobs).

2. **Where RAG tunables live**  
   **Decision:** Add **`scrapers.ragService`** (name aligns with “service backing scrapers”) with the same shape as today’s non-o11y `rag` fields: `replicaCount`, `service` (`type`, `port`), `resources`. Defaults mirror current `values.yaml` RAG defaults.  
   **Rationale:** Keeps scraper-adjacent config in one subtree; no top-level `rag`.  
   **Alternatives considered:** Flat `scrapers.replicaCount` for RAG — rejected (ambiguous vs future scraper pod sizing).

3. **Helm helper for the gate**  
   **Decision:** Implement a named template (e.g. `declarative-agent-library.ragFromScrapers`) that evaluates true when any scraper job is enabled; use it in `rag-deployment.yaml`, `rag-service.yaml`, `rag-servicemonitor.yaml`, and `ragInternalBaseUrl`.  
   **Rationale:** Single source of truth; avoids duplicating `range` logic.

4. **Prometheus annotations and ServiceMonitor**  
   **Decision:** Replace checks on `rag.prometheusAnnotations.enabled` with **`o11y.prometheusAnnotations.enabled`** for RAG Pod and Service. RAG `ServiceMonitor` renders when **`o11y.serviceMonitor.enabled`** and RAG is deployed (same as today’s `and` pattern, without `rag.enabled`).  
   **Rationale:** “O11y is all-or-nothing” for scrape discovery metadata on chart-managed targets.

5. **Reference scraper and empty RAG URL**  
   **Decision:** When no scraper is enabled, `ragInternalBaseUrl` stays empty and agent env remains as today; CronJobs for disabled jobs are not rendered (existing behavior). If someone enables a scraper but misconfigures URL, that remains an operational concern — RAG will exist by construction when any job is enabled.

## Risks / Trade-offs

- **[BREAKING] Values migration** → Document in `proposal.md` / README: move `rag.*` tunables to `scrapers.ragService.*`, remove `rag.enabled` / `rag.prometheusAnnotations`; enable RAG by enabling at least one scraper job.  
- **Helm `any enabled job` logic** → Implement with a small counter or accumulator pattern tested via `helm template` in `ci.sh`.  
- **Examples** (`with-observability`) → Must enable a scraper (or a minimal enabled job) if they need RAG for demos that hit RAG metrics — update example values accordingly.

## Migration Plan

1. Chart upgrade: remove `rag:` from parent values; add `scrapers.jobs` with at least one `enabled: true` job where RAG was previously on; move replica/service/resources under `scrapers.ragService`.  
2. Set `o11y.prometheusAnnotations.enabled` once for both agent and RAG scrape hints.  
3. Rollback: pin previous chart version and restore prior values.

## Open Questions

- Whether to ship a **dummy / no-op scraper** job type for rare “RAG API without scheduled ingest” — **deferred** (non-goal unless product asks).
