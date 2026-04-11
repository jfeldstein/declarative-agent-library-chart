# Grafana dashboards (CFHA)

## `cfha-agent-overview.json`

Starter dashboard for the **config-first-hosted-agents** runtime (import one dashboard):

- **Agent** (port 8088): rate of `agent_runtime_http_trigger_requests_total` by `result`; p95 latency from `agent_runtime_http_trigger_duration_seconds`
- **RAG** (port **8090** by default when the chart deploys RAG — i.e. at least one enabled `scrapers.jobs` entry): rate of `agent_runtime_rag_embed_requests_total` and `agent_runtime_rag_query_requests_total` by `result`

Prometheus must scrape **both** targets (e.g. dual `ServiceMonitor` from `examples/with-observability/` or two static scrape jobs as in `runtime/tests/scripts/prometheus-kind-o11y-values.yaml`).

### Import

1. Grafana → **Dashboards** → **New** → **Import** → upload `cfha-agent-overview.json`.
2. Select a **Prometheus** data source when prompted (the JSON uses placeholder uid **`prometheus`**; edit panel queries if your datasource uid differs).

### Related metrics (other scrape targets)

- **Scraper CronJob pods** (`agent_runtime_scraper_*`): add panels when those metrics ship; scrape CronJob endpoints or pushgateway per your design.

The agent pod exposes MCP / subagent / skill metrics on the same `/metrics` as **`POST /api/v1/trigger`** when those features run through the trigger pipeline. RAG metrics live on the **RAG** Service (`*-rag`, path `/metrics`).
