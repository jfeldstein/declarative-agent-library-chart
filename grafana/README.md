# Grafana dashboards (DALC)

<!-- Traceability: [DALC-REQ-O11Y-LOGS-003] -->

## `dalc-agent-overview.json`

Starter dashboard for the **config-first-hosted-agents** runtime (import one dashboard):

- **Agent** (port 8088): rate of `agent_runtime_http_trigger_requests_total` by `result`; p95 latency from `agent_runtime_http_trigger_duration_seconds`
- **RAG** (port **8090** by default when the chart deploys RAG — i.e. at least one enabled `scrapers.jobs` entry): rate of `agent_runtime_rag_embed_requests_total` and `agent_runtime_rag_query_requests_total` by `result`
- **Scraper CronJob pods** (port **9091**, path `/metrics` when `o11y.prometheusAnnotations.enabled`): `agent_runtime_scraper_runs_total`, `agent_runtime_scraper_run_duration_seconds`, and `agent_runtime_scraper_rag_submissions_total` (reference scraper only for embed attempts)

Prometheus must scrape **agent, RAG, and scraper** targets as applicable (e.g. `ServiceMonitor` from `examples/with-observability/` or static scrape jobs; CronJobs may need a scrape path appropriate to your cluster — see `docs/observability.md`).

### Import

1. Grafana → **Dashboards** → **New** → **Import** → upload `dalc-agent-overview.json`.
2. Select a **Prometheus** data source when prompted (the JSON uses placeholder uid **`prometheus`**; edit panel queries if your datasource uid differs).

### Related metrics

The agent pod exposes MCP / subagent / skill metrics on the same `/metrics` as **`POST /api/v1/trigger`** when those features run through the trigger pipeline. RAG metrics live on the **RAG** Service (`*-rag`, path `/metrics`). Scraper metrics use the **`integration`** label (from `SCRAPER_INTEGRATION` or job name); extend **`dalc-agent-overview.json`** when you add a scraper that emits new series — and update **`examples/with-scrapers/`** so the chart values stay the canonical sample (see **`hosted_agents.scrapers`** package docstring).
