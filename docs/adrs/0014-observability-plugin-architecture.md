# ADR 0014: Observability plugin architecture (lifecycle event bus)

## Status

Accepted

## Context

**Phase 1** of the observability work introduced a **synchronous lifecycle event bus** (`SyncEventBus`, named `EventName` events) and thin **middleware** helpers so HTTP trigger handling, tool execution, LLM usage callbacks, RAG HTTP, scraper runs, and inbound Slack/Jira trigger paths emit **structured domain events** instead of calling Prometheus (or future sinks) ad hoc from many modules. That decoupling is documented in OpenSpec change **`openspec/changes/observability-lifecycle-events/`**.

Operators still need a **single, predictable Helm surface** for turning optional observability **integrations** on or off as the chart wires env, Secrets, and sidecars. Without an ADR, “plugin” could be confused with **MCP tools**, **LangChain tools**, or **execution persistence** (checkpoints, correlation rows)—which [ADR 0005](0005-observability-vs-execution-persistence.md) already separates from **Prometheus observability metrics** ([ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md)).

## Decision

1. **Single Helm tree — `agent.observability.plugins`**  
   Optional provider-style integrations **SHALL** be grouped under **`observability.plugins`** with one boolean **`enabled`** (default **false**) per known key: **`prometheus`**, **`langfuse`**, **`wandb`**, **`grafana`**, **`logShipping`**. Additional keys **MAY** be added by future ADRs. This tree is the **canonical** place to discover which integrations the release intends to support; Phase 1 **scaffolds** flags; later phases connect templates and env.

2. **Opt-in semantics**  
   A plugin being **disabled** means the chart/runtime **SHALL NOT** require that integration’s credentials, sidecars, or network paths for a minimal deploy. **Enabling** a plugin is an explicit operator choice and **MAY** imply extra containers, Secrets, or outbound traffic.

3. **Prometheus path**  
   The process **`GET /metrics`** endpoint and existing **`agent_runtime_*`** naming remain the default **Prometheus observability metrics** surface ([ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md)). Phase 1 preserves prior series via bus subscribers; the **`observability.plugins.prometheus`** flag is reserved for future gating or secondary registries if we ever split surfaces—**today** scraping does not require flipping this flag.

4. **Tool boundary**  
   **User-invoked tools** (MCP / LangChain tools, Slack Web API helpers, Jira REST helpers) **SHALL** emit observability through the **trigger / runtime** instrumentation paths (event bus → subscribers), not by importing metric helpers directly from arbitrary tool modules. Tools remain **capabilities of the agent**; observability remains **platform instrumentation** around those calls.

5. **Explicitly out of scope for this ADR**  
   - **Alerting rules** and **SLO** policy (PrometheusRule, Alertmanager/on-call routing): product/ops choices, not bus shape.  
   - **Checkpointing**, **Postgres correlation**, **W&B run content**, and other **execution persistence data** ([ADR 0005](0005-observability-vs-execution-persistence.md)): they may *consume* the same trace ids in logs, but their durability model is not defined by the plugin tree.

## Consequences

**Positive:**

- One place in `values.yaml` explains “which optional observability integrations exist” without spelunking env prefixes.
- Clear separation from tools and from execution persistence reduces spec and code review ambiguity.
- The bus allows adding Langfuse/Grafana/log-shipping subscribers without rewriting business modules.

**Negative / trade-offs:**

- **Two** W&B-related surfaces may exist temporarily: top-level **`wandb.*`** (current tracing project/entity wiring) and **`observability.plugins.wandb`** (future alignment); release notes **SHALL** call out migration when template behavior changes.
- Contributors must route new metrics through shared instrumentation patterns to avoid cardinality leaks ([ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md)).

**Follow-ups:**

- Wire **`observability.plugins.*`** to env/templates per integration in phased OpenSpec changes.
- Update `docs/observability.md` plugin stubs when each integration ships.

## Related

- [ADR 0015: Integration-agnostic observability plugins](0015-integration-agnostic-observability-plugins.md) — shared Prometheus code **SHALL NOT** encode vendor-specific metric families or helper names.
