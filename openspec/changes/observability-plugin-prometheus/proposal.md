# Prometheus observability plugin (`dalc-plugin-prometheus-metrics`)

## Summary

Ship Phase 2 metrics: register a Prometheus plugin against `SyncEventBus`, emit **`dalc_*`** counters/histograms aligned with **`openspec/changes/observability-lifecycle-events/design.md`**, gate **`GET /metrics`** behind **`observability.plugins.prometheus.enabled`** (Helm) / **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED`**, update scrape templates and promoted specs/traceability accordingly.

## Motivation

- Consolidate lifecycle instrumentation onto the bus-backed plugin rather than duplicated `observe_*` shims.
- Replace legacy `agent_runtime_*` metric names where superseded by **`dalc_*`** mapping.
- Let operators disable Prometheus exposition without disabling unrelated observability stores.

## Non-goals

- Langfuse / OTLP exporters (remain future plugin slots).
- Changing Slack/Jira trigger functional behavior beyond metric label schema.
