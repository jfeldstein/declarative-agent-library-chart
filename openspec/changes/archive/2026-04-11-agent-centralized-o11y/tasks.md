## 1. Runtime: metrics and logging

- [x] 1.1 Add `prometheus_client` (or equivalent) to `runtime` and mount ASGI `/metrics` on the FastAPI app per design
- [x] 1.2 Register **`agent_runtime_http_trigger_requests_total`** and **`agent_runtime_http_trigger_duration_seconds`** for `POST /api/v1/trigger` with tests asserting `/metrics` contains expected series; when MCP/subagents/skills ship, add **`agent_runtime_mcp_tool_*`**, **`agent_runtime_subagent_*`**, and **`agent_runtime_skill_*`** per **`agent-runtime-components`** specs
- [x] 1.3 Add structured JSON logging (e.g. `structlog` or JSON formatter) with `level`, `message`, `service`, and per-request correlation id middleware; verify stdout in tests or integration script
- [x] 1.4 Document any env vars (e.g. dev plain-text vs prod JSON) in README or `docs/observability.md`

## 2. Helm: discovery and ServiceMonitor

- [x] 2.1 Extend `helm/chart/values.yaml` and `values.schema.json` with opt-in `o11y` (or equivalent) flags for Prometheus annotations (default off)
- [x] 2.2 Template Pod and/or Service annotations when enabled; ensure port and path match `/metrics` on the HTTP port
- [x] 2.3 Add optional `ServiceMonitor` template gated by values (default off); document CRD prerequisite
- [x] 2.4 Extend chart tests or `helm template` golden checks to cover enabled vs disabled o11y values

## 3. Dashboards and operator documentation

- [x] 3.1 Add Grafana dashboard JSON under `this repository` (path per design) with panels for **`agent_runtime_http_trigger_*`** and (as features land) rows or linked dashboards for **`agent_runtime_mcp_tool_*`**, **`agent_runtime_subagent_*`**, **`agent_runtime_skill_*`**, plus documentation pointers for RAG and scraper targets (**`agent_runtime_rag_*`**, **`agent_runtime_scraper_*`**)
- [x] 3.2 Add short README for dashboard import and datasource assumptions
- [x] 3.3 Update main README (or `docs/observability.md`) with scrape target setup, log shipping hints (Fluent Bit / Promtail / Vector), and link to dashboard artifact

## 4. CI and verification

- [x] 4.1 Update `ci.sh` (or project test command) if new steps are required (e.g. runtime tests, `helm template` with o11y flags)
- [x] 4.2 Run full CI locally and fix failures before merge
