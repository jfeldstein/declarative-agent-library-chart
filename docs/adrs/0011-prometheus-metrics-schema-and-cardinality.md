# ADR 0011: Prometheus metrics schema and cardinality

## Status

Accepted

## Context

This project exposes **Prometheus observability metrics** (see [ADR 0005](0005-observability-vs-execution-persistence.md)) from the hosted agent HTTP runtime, the optional RAG HTTP service, and scheduled scraper CronJobs. Without shared naming and label rules, series proliferate, cardinality grows, and dashboards or alerts accidentally capture secrets or unbounded dimensions.

Implementation today lives in `helm/src/agent/metrics.py`, `helm/src/agent/rag/metrics.py`, and `helm/src/agent/scrapers/metrics.py`.

## Decision

### Naming conventions

- **Hosted agent runtime (default registry):** metric names **SHALL** use the prefix `agent_runtime_` for counters and histograms that describe trigger handling, MCP-style tools, subagents, and skill loads (for example `agent_runtime_http_trigger_requests_total`, `agent_runtime_mcp_tool_calls_total`).
- **RAG HTTP service:** metric names **SHALL** use the prefix `agent_runtime_rag_` so RAG request/latency series are distinct from the main trigger path (for example `agent_runtime_rag_embed_requests_total`, `agent_runtime_rag_query_duration_seconds`).
- **Scraper jobs:** metric names **SHALL** use the prefix `agent_runtime_scraper_` so batch/ingestion work is not confused with interactive runtime paths (for example `agent_runtime_scraper_runs_total`, `agent_runtime_scraper_rag_submissions_total`).
- Histograms **SHALL** use the `_seconds` suffix and document wall-time or processing latency in the help string; counters **SHALL** use `_total` where they are cumulative counts.

### Label rules and cardinality

- Labels **SHALL** be **low-cardinality and bounded**: prefer small fixed enums (for example `result` in `success` / `client_error` / `server_error` or binary success/error where that is the contract).
- Dimensions such as `tool`, `subagent`, `skill`, and scraper `integration` **SHALL** refer to **catalog identifiers** known from configuration or code, not raw user input, channel IDs, issue keys, or free-form strings. If a dimension would grow without bound or encode business identifiers, it **SHALL NOT** be a label; record it in structured **logs** or execution persistence instead.
- Label values **MUST NOT** contain secrets, credentials, tokens, or **PII**. Never put message bodies, URLs with query secrets, or customer identifiers into metric labels.
- When classifying HTTP outcomes for labels, reuse the same coarse buckets as existing series (for example mapping status codes to `success` / `client_error` / `server_error`) so scraper-to-RAG and RAG service metrics stay comparable.

### Registries: scrapers vs main application

- The main agent and RAG processes **MAY** use the **default** `prometheus_client` registry for `/metrics` on their workloads.
- Scraper CronJob pods **SHALL** register scraper metrics on a **dedicated** `CollectorRegistry` (`SCRAPER_REGISTRY` in `scrapers/metrics.py`) and expose them via that registry only, so short-lived jobs do not emit or merge unrelated agent/RAG series and operators scrape a coherent scraper surface.

### Grafana and dashboards (high level)

- Dashboards **SHOULD** use the prefixes above in PromQL to select the right tier (`agent_runtime_*` vs `agent_runtime_rag_*` vs `agent_runtime_scraper_*`).
- New metrics or labels **SHOULD** be accompanied by panel or row updates in the repository Grafana JSON (for example `grafana/dalc-overview.json`) and brief operator notes where scrape paths differ (agent Deployment vs RAG vs scraper metrics listener).
- Authors **SHOULD** assume alerting and SLO panels aggregate by **result** and **integration** / **role**, not by high-cardinality dimensions; drill-down belongs in logs or traces, not in every panel’s `group by`.

## Consequences

**Positive:**

- Consistent names make cross-service dashboards and on-call runbooks easier to write.
- Strict label rules keep Prometheus memory and scrape cost predictable.
- A separate scraper registry avoids misleading or empty series on job pods and keeps cardinality scoped to ingestion workloads.

**Negative / trade-offs:**

- Some operational questions that need per-entity detail will not be answerable from metrics alone; logs or persistence must carry those fields.
- Adding a new scraper or tool name increases label values only within the intended catalog; contributors must keep that catalog deliberate.

**Follow-ups:**

- When adding new metric families, extend the checklist in `scrapers/metrics.py` (Helm, examples, tests, dashboard, registry) in parallel so schema and documentation stay aligned.
