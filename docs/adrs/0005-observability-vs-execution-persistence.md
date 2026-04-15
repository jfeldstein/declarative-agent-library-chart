# ADR 0005: Observability metrics vs execution persistence

## Status

Accepted

## Context

The repository uses the word "observability" in multiple places:

- Kubernetes/Prometheus integration (`observability.*` Helm values, `prometheus.io/*`, `ServiceMonitor`, `/metrics`).
- Durable run-state capabilities (LangGraph checkpoints, Slack correlation, human feedback events, and optional tool/run summaries in Postgres).

When both are called "observability data" without qualification, requirement text becomes ambiguous: metrics guidance can be misread as persistence requirements, and persistence requirements can be misread as scrape/alerting requirements.

This ambiguity appears in OpenSpec and docs discussions around `agent-checkpointing-wandb-feedback`, `postgres-agent-persistence`, and dashboard/scrape changes.

## Decision

Use two explicit categories in specs, ADRs, docs, and review comments:

1. **Prometheus observability metrics**  
   Time-series telemetry exposed for monitoring and alerting (for example `/metrics`, Prometheus annotations, `ServiceMonitor`, Grafana panels based on PromQL).

2. **Execution persistence data**  
   Durable run-state records used for resume, audit, and correlation (for example checkpoint history, `(channel_id, message_ts)` correlation rows, feedback events, side-effect metadata, and optional tool/run span summaries).

Terminology rules:

- The unqualified phrase **"observability data"** SHOULD be avoided in normative or design text.
- Requirements about Prometheus scraping, dashboards, alerts, and metric names SHALL use **"Prometheus observability metrics"** (or simply **"metrics"** when context is unambiguous).
- Requirements about durable run/thread/tool records SHALL use **"execution persistence data"**.
- Weights & Biases tracing remains a separate trace product surface; it does not redefine either category.

## Consequences

**Positive:**

- Reduces ambiguity in OpenSpec requirements and acceptance criteria.
- Prevents false coupling between scrape configuration and database durability work.
- Improves onboarding by making monitoring concerns distinct from replay/audit concerns.

**Negative / trade-offs:**

- Existing docs may require wording updates over time to align terminology.
- Authors must choose terms deliberately instead of using the generic "observability" shorthand.

**Follow-ups:**

- Update `docs/observability.md` glossary text to include both category names.
- Prefer these terms in future OpenSpec changes involving checkpoints, feedback, tracing, or Prometheus dashboards.
