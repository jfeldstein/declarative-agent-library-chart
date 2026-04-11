## Why

Hosted agents deployed from the CFHA Helm library are invisible to cluster-wide observability stacks: there is no Prometheus-compatible metrics endpoint, no stable scrape contract, and no chart-level hooks for the Prometheus Operator or centralized logging pipelines. Operators running Grafana, Prometheus, Loki, or similar need every agent workload to be a **first-class scrape (and log) target** so SREs can alert, dashboard, and correlate without per-team custom wiring.

## What Changes

- Expose a **Prometheus text exposition** endpoint on the agent HTTP server (standard path and content type) with a small, versioned set of process/runtime metrics suitable for centralized scraping.
- Extend the **Helm library chart** so Services/Pods carry **opt-in** Prometheus discovery metadata (e.g. `prometheus.io/*` annotations and/or optional `ServiceMonitor` / `PodMonitor` templates gated by values) so centralized Prometheus or the Prometheus Operator can select agent targets consistently.
- Define **structured logging** expectations (JSON or key=value fields, severity, service name) so log agents (Fluent Bit, Promtail, OTel Collector, etc.) can parse and ship to Loki/Elastic without custom parsers per deployment.
- Provide **starter Grafana dashboard** definitions (JSON or documented import path) aligned with the new metrics and key log-derived panels where applicable—sufficient for a central Grafana instance to import or provision-as-code.

## Capabilities

### New Capabilities

- `cfha-agent-o11y-scrape`: Prometheus scrape target contract for the CFHA runtime (HTTP `/metrics` or documented path, exposition format, health/liveness compatibility with scraping, Helm values for scrape interval hints and discovery annotations or operator CRs).
- `cfha-agent-o11y-logs-dashboards`: Structured application logging contract for centralized log pipelines and starter Grafana dashboard artifacts tied to the new metrics (and optional log-based panels).

### Modified Capabilities

- (none — root `openspec/specs/` has no prior CFHA observability capability to delta.)

## Impact

- **Runtime** (`runtime`): ASGI app, dependencies (e.g. `prometheus_client` or equivalent), Dockerfile image behavior unchanged aside from serving metrics.
- **Helm library** (`helm/chart`): `values.yaml`, `values.schema.json`, templates for Service/Deployment annotations and optional `ServiceMonitor`/`PodMonitor`.
- **CI/tests**: Extend chart tests or integration checks to assert metrics endpoint reachability when o11y is enabled; document curl/`kubectl` verification for operators.
- **Centralized O11Y**: No mandate on a specific vendor; contracts must work with **Prometheus-compatible** scrapers and common log shippers.
