# Grafana dashboards (DALC)

<!-- Traceability: [DALC-REQ-O11Y-LOGS-003] [DALC-REQ-O11Y-LOGS-005] [DALC-REQ-O11Y-LOGS-006] -->

## `cfha-token-metrics.json`

Additional dashboard for **LLM token economics and streaming health** on the agent **`/metrics`** endpoint (same scrape path as `dalc-overview.json`):

- Output token **rate**, **TTFT** quantiles (by `streaming` label), **trigger request/response payload** p95, **estimated cost** rate (panel title marks **estimate**).

### Import

1. Grafana → **Dashboards** → **New** → **Import** → upload `cfha-token-metrics.json`.
2. Select a **Prometheus** data source (placeholder uid **`prometheus`**, same as `dalc-overview.json`).

Metric names and label semantics: **`docs/observability.md`** (LLM token metrics section).

## `dalc-overview.json`

Starter dashboard for the **Declarative Agent Library** runtime (import one dashboard):

- **Agent** (port 8088): rate of `agent_runtime_http_trigger_requests_total` by `result`; p95 latency from `agent_runtime_http_trigger_duration_seconds`
- **Optional rows** (see section titles in the JSON): when the chart deploys additional metrics endpoints, matching panels apply—for example **managed RAG HTTP** (embed/query rates on the RAG Service port, default **8090** when scraper jobs enable RAG) and **scraper CronJob** metrics (`agent_runtime_scraper_*` on port **9091** when `observability.prometheusAnnotations.enabled`)

The dashboard groups optional workloads under **row** headings so agent-only deployments stay readable; empty series for absent components are expected.

### Prometheus scrape alignment

Configure Prometheus (or the Prometheus Operator) so **every `Service` / workload that exports `/metrics` in your release** is scraped—for example by installing the chart’s optional **`ServiceMonitor`** resources under `observability.serviceMonitor`, or by adding **static scrape jobs** that mirror those endpoints. The number of targets **depends on values**: at minimum the agent; additional targets appear when optional components (RAG, annotated scraper pods, etc.) are enabled and deployed. Do **not** assume a fixed count of targets across all installs.

See **`docs/observability.md`**, **`examples/with-observability/`** (RAG + scraper enabled), and **`examples/with-observability/values-observability-no-rag.yaml`** (Kubernetes observability without RAG) for concrete value shapes.

### Import

1. Grafana → **Dashboards** → **New** → **Import** → upload `dalc-overview.json`.
2. Select a **Prometheus** data source when prompted (the JSON uses placeholder uid **`prometheus`**; edit panel queries if your datasource uid differs).

### Related metrics

The agent pod exposes MCP / subagent / skill metrics on the same `/metrics` as **`POST /api/v1/trigger`** when those features run through the trigger pipeline. RAG metrics, when deployed, live on the **RAG** Service (`*-rag`, path `/metrics`). Scraper metrics use the **`integration`** label (from `SCRAPER_INTEGRATION` or job name); extend **`dalc-overview.json`** when you add a scraper that emits new series — and update **`examples/with-scrapers/`** so the chart values stay the canonical sample (see **`hosted_agents.scrapers`** package docstring).
