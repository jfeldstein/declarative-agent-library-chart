## Architecture

- **Tools** implement business logic only; they do not import `agent.observability.*`. Metrics for MCP tool calls and Slack Web API usage are recorded when `run_tool_json` publishes `tool.call.*` events (with optional `slack_web_api_method` derived from tool id).
- **Middleware** (`agent.observability.middleware`) is the only supported publisher for lifecycle events from HTTP triggers, LLM callbacks, RAG HTTP middleware, scrapers, subagents, and skill loads.
- **Legacy bridge** (`agent.observability.legacy_agent_metrics` / `legacy_scraper_metrics`) subscribes synchronously and calls existing `observe_*` functions so Prometheus series remain aligned with **`dalc_*`** names emitted from `metrics.py` / scraper registry code paths.

### Per-process buses

- **Agent pod:** `ensure_agent_observability()` registers legacy subscribers on the agent singleton bus (FastAPI `create_app`, RAG `create_app`).
- **Scraper CronJob:** `ensure_scraper_observability()` before `run_scraper_main` body; scraper RAG embed attempts and run duration use the scraper bus.

### `dalc_*` Prometheus prefix (parallel chart + dashboards work)

Runtime counters/histograms use the **`dalc_*` prefix** with stable suffix structure (for example `dalc_http_trigger_requests_total`, `dalc_mcp_tool_calls_total`, `dalc_rag_embed_requests_total`, `dalc_scraper_runs_total`). See **ADR 0011** and **`docs/observability.md`**.

Optional follow-up (**Phase 2**) may consolidate certain families behind shared names with extra labels (for example merging inbound bridge counters); any such consolidation SHALL be tracked as its own OpenSpec change with migration notes for dashboards.

### Helm: `observability.plugins`

Single subtree shared by agent Deployment and scraper CronJobs; each process constructs its own bus + plugin instances from the same values tree (`plugins_config.py` stub reads defaults until env wiring lands).
