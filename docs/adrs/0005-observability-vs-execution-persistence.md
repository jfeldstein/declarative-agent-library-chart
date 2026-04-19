# ADR 0005: Observability metrics vs execution persistence

## Status

Accepted

## Context

The repository uses the word "observability" in multiple places:

- Kubernetes/Prometheus integration (`observability.*` Helm values, `prometheus.io/*`, `ServiceMonitor`, `/metrics`).
- Durable run-state capabilities (LangGraph checkpoints, Slack correlation, human feedback events, and optional tool/run summaries in Postgres).

When both are called "observability data" without qualification, requirement text becomes ambiguous: metrics guidance can be misread as persistence requirements, and persistence requirements can be misread as scrape/alerting requirements.

A related axis is **optional observability integrations** (for example Langfuse, Grafana Cloud, log shipping) configured under a **single Helm tree** — **`agent.observability.plugins`** — and fed by the **lifecycle event bus** ([ADR 0014](0014-observability-plugin-architecture.md)). Those integrations are neither **Prometheus observability metrics** nor **execution persistence data** by default; they are **exporters/adapters** that MAY subscribe to events or read redacted logs. Checkpoint stores, W&B run records, and Postgres correlation tables remain **execution persistence** even if a plugin also reads them.

This ambiguity appears in OpenSpec and docs discussions around `agent-checkpointing-wandb-feedback`, `postgres-agent-persistence`, `observability-lifecycle-events`, and dashboard/scrape changes.

## Decision

Use the following explicit categories in specs, ADRs, docs, and review comments:

1. **Prometheus observability metrics**  
   Time-series telemetry exposed for monitoring and alerting (for example `/metrics`, Prometheus annotations, `ServiceMonitor`, Grafana panels based on PromQL).

2. **Execution persistence data**  
   Durable run-state records used for resume, audit, and correlation (for example checkpoint history, `(channel_id, message_ts)` correlation rows, feedback events, side-effect metadata, and optional tool/run span summaries).

3. **Observability plugins (integrations)**  
   Optional chart/runtime modules (see **`agent.observability.plugins`**) that wire **third-party or cluster-level** telemetry paths—distinct from raw **metrics** emission and distinct from durable **execution** state unless a specific integration explicitly persists data. Naming: prefer **“observability plugin”** or **“integration”** in design text; avoid overloading **“tool”** (reserved for agent-invoked tools).

Terminology rules:

- The unqualified phrase **"observability data"** SHOULD be avoided in normative or design text.
- Requirements about Prometheus scraping, dashboards, alerts, and metric names SHALL use **"Prometheus observability metrics"** (or simply **"metrics"** when context is unambiguous).
- Requirements about durable run/thread/tool records SHALL use **"execution persistence data"**.
- Requirements about optional **third-party telemetry integrations** wired from the lifecycle bus or chart (Langfuse, log shippers, and similar) SHALL use **"observability plugin(s)"** or name the vendor integration; do not call them **"tools"** ([ADR 0014](0014-observability-plugin-architecture.md)).
- Weights & Biases tracing remains a **trace product** surface (configured today via **`wandb.*`** and env vars); it does not replace the categories above, and **`observability.plugins.wandb`** is reserved for future chart-level alignment with that product.

## Consequences

**Positive:**

- Reduces ambiguity in OpenSpec requirements and acceptance criteria.
- Prevents false coupling between scrape configuration and database durability work.
- Improves onboarding by making monitoring concerns distinct from replay/audit concerns.

**Negative / trade-offs:**

- Existing docs may require wording updates over time to align terminology.
- Authors must choose terms deliberately instead of using the generic "observability" shorthand.

**Follow-ups:**

- Keep `docs/observability.md` aligned with this split and with [ADR 0014](0014-observability-plugin-architecture.md) as plugins gain Helm wiring.
- Prefer these terms in future OpenSpec changes involving checkpoints, feedback, tracing, Prometheus dashboards, or optional telemetry integrations.
