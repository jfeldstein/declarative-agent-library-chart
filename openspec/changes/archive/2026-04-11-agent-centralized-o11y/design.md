## Context

The CFHA runtime is a FastAPI app on container port **8088** with a single business route (`POST /api/v1/trigger`). The Helm library renders a `Service` named after the release with port **http** → **8088**. There is no metrics exposition today, so Prometheus (or any pull-based scraper) cannot target agents without sidecars or opaque blackbox checks. Centralized observability teams typically expect either **annotation-based** discovery (static Prometheus or `prometheus-operator` `PodMonitor` relabel from annotations) or **first-class `ServiceMonitor` resources** aligned with their RBAC and `ServiceMonitor` selectors.

## Goals / Non-Goals

**Goals:**

- Agents become **valid Prometheus scrape targets** on the same HTTP server (one listen socket) unless a future spec explicitly splits ports.
- Chart operators can **opt in** to standard scrape annotations and/or render optional **`ServiceMonitor`** / **`PodMonitor`** manifests controlled by values (off by default to avoid surprising CRD requirements).
- Application logs are **structured** (machine-parseable) with stable field names for `service`, `level`, and `message` at minimum.
- Repository ships **importable Grafana dashboard JSON** (or equivalent documented bundle) that charts the new metrics and documents log query hints for Loki-style backends.

**Non-Goals:**

- Choosing or deploying a specific vendor stack (GKE managed Prometheus, Datadog agent, etc.); we only publish contracts and artifacts that interoperate with common OSS patterns.
- Distributed tracing (OpenTelemetry traces) as a mandatory part of this change—may be noted as a follow-up in Open Questions.
- High-cardinality per-request labels on metrics (e.g. unbounded route or user labels).

## Decisions

1. **Metrics library**: Use the **`prometheus_client`** Python package with the recommended **ASGI / FastAPI integration** (e.g. `make_asgi_app()` mounted at `/metrics`, or equivalent starlette routing) so exposition follows Prometheus text format 0.0.4. **Rationale**: De facto standard, minimal code, works with any Prometheus-compatible scraper. **Alternatives**: OpenTelemetry Metrics SDK (heavier, exporter config); raw manual text (error-prone).

2. **Single port for app + metrics**: Serve `/metrics` on **8088** alongside API routes. **Rationale**: Matches current Service and deployment shape; simplest scrape target (`target: pod:8088`, path `/metrics`). **Alternatives**: Separate metrics port (cleaner for network policies, more Helm churn).

3. **Metric names and components**: Use the shared **`agent_runtime_*`** prefix across services. **HTTP trigger** uses **`agent_runtime_http_trigger_requests_total`** and **`agent_runtime_http_trigger_duration_seconds`** with **`result`** ∈ {`success`, `client_error`, `server_error`}. **RAG**, **scrapers**, **MCP tools**, **subagents**, and **skills** each expose the counters and histograms defined in the corresponding **`agent-runtime-components`** specs (`runtime-rag-http`, `runtime-scrapers`, `runtime-tools-mcp`, `runtime-subagents`, `runtime-skills`). **Rationale**: One naming scheme for Grafana and alerts; bounded labels (`integration`, `tool`, `subagent`, `skill` from config only). **Alternatives**: Per-service ad hoc names — harder to reuse dashboards.

4. **Helm discovery**: Default **off**; when `o11y.metrics.enabled` (name TBD in implementation) is true, add **`prometheus.io/scrape: "true"`**, **`prometheus.io/port`**, **`prometheus.io/path`** on the **Pod template** and/or **Service** as documented. Optionally, if `o11y.serviceMonitor.enabled`, render a **`monitoring.coreos.com/v1` `ServiceMonitor`** with labels/namespace selectors driven by values so cluster Prometheus Operator picks it up. **Rationale**: Covers both legacy annotation scrapers and kube-prometheus-stack. **Alternatives**: Only annotations (fails teams that forbid annotations); only ServiceMonitor (fails non-operator Prometheus).

5. **Structured logging**: Use **`structlog`** or JSON formatter on the root logger so stdout is one JSON object per line in production; keep human-readable option for local dev via env flag. **Rationale**: Works with Fluent Bit, Promtail, Vector, OTel Collector without custom multiline rules. **Alternatives**: Plain text only (harder for centralized Loki).

6. **Dashboards**: Check in **`grafana/`** (or `docs/grafana/`) a **`cfha-agent-overview.json`** plus a short README for import / provisioning. **Rationale**: Central Grafana instances can Git-sync or copy JSON; no runtime coupling.

## Risks / Trade-offs

- **[Risk] `/metrics` exposes internal counters** → Mitigation: document that metrics are non-secret; if clusters require isolation, operators use NetworkPolicy; future optional auth or separate internal port.
- **[Risk] `ServiceMonitor` CRD absent** → Mitigation: template gated by values; `helm template` tests with flag off by default; document that enabling requires Prometheus Operator.
- **[Risk] Cardinality growth** → Mitigation: spec limits labels; code review for new metrics.
- **[Trade-off] Same port as API** → Simpler ops; some orgs prefer dedicated metrics ports for policy.

## Migration Plan

1. Ship runtime + chart changes behind **values defaults** that preserve today’s behavior (metrics and annotations off) **or** enable metrics endpoint always but scrape annotations off—**product choice**: spec will require endpoint availability when o11y is enabled; minimal breaking change if endpoint is always on but unscraped.
2. Document upgrade: set values to enable scrape annotations / ServiceMonitor for environments with central Prometheus.
3. Rollback: revert values or previous chart version; no data migration.

## Open Questions

- Should `/metrics` be **always on** (operational simplicity) vs **env-gated** (minimal attack surface)? Proposal leans toward always-on with no sensitive data, subject to spec wording.
- Whether to add **`/health`/`/ready`** in the same change for kube-probes and blackbox checks, or defer to a separate change.
