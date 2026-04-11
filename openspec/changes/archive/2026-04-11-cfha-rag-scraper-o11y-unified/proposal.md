## Why

Operators currently toggle the managed RAG workload and its Prometheus scrape metadata with a separate top-level `rag` values subtree (`rag.enabled`, `rag.prometheusAnnotations`). That duplicates decisions already implied by scrapers (RAG exists to back ingest jobs) and splits observability across `rag.*` and `o11y.*`, which is easy to misconfigure. Aligning RAG lifecycle with scrapers and making Prometheus annotations a single `o11y` switch reduces surface area and matches the mental model: **scrapers imply RAG; o11y implies scrape metadata everywhere the chart exposes metrics.**

## What Changes

- **BREAKING**: Remove the top-level Helm values key **`rag`** (including `rag.enabled` and `rag.prometheusAnnotations`). RAG Service/Deployment (and RAG `ServiceMonitor` when enabled) are rendered **only when at least one scraper job has `enabled: true`**.
- Move tunables that today live under `rag` (replica count, service shape, resources) under a **documented nested path** tied to the scraper subsystem (e.g. `scrapers.ragService` or equivalent — exact shape in `design.md`).
- **RAG Prometheus annotations** (Pod template and Service) and **RAG ServiceMonitor** selection use the **same** switches as the agent: **`o11y.prometheusAnnotations.enabled`** and **`o11y.serviceMonitor.enabled`** respectively — no separate `rag.prometheusAnnotations` flag.
- Update **`values.schema.json`**, default **`values.yaml`**, **examples** (`with-observability`, `with-scrapers`, `hello-world` as applicable), **`ci.sh`** assertions, **docs** (`README`, `docs/observability.md`), and **kind/Prometheus integration** fixtures so they no longer set or assume top-level `rag`.

## Capabilities

### New Capabilities

- `cfha-rag-from-scrapers`: Declarative Agent Library Chart requirements for **when** the managed RAG HTTP workload is deployed and **where** its tunables live in values (scraper-gated lifecycle, no top-level `rag`).

### Modified Capabilities

- `cfha-agent-o11y-scrape`: Extend scrape-discovery requirements so **all** chart-managed Prometheus targets (agent and RAG, when RAG is deployed) honor **`o11y.prometheusAnnotations.enabled`** and **`o11y.serviceMonitor.enabled`** as the single operator controls (no per-workload RAG-only scrape flag).

## Impact

- **Helm**: `templates/rag-*.yaml`, `_helpers.tpl`, `values.yaml`, `values.schema.json`, example charts, `ci.sh`.
- **Docs / artifacts**: Observability docs, Grafana README if it references `rag.prometheusAnnotations`, integration test values/scripts.
- **Consumers**: Any release or parent chart that set `rag.enabled` or `rag.prometheusAnnotations` must migrate to scraper-gated RAG + unified `o11y.*`.
