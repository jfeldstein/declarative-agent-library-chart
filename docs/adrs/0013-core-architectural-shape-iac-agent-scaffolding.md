# ADR 0013: Core architectural shape — IaC, agent runtime, and non-agentic scaffolding

## Purpose

Give operators and contributors a **stable mental model** for how the Declarative Agent Library Chart decomposes: what is **infrastructure**, what is the **agent** (reasoning + tools + learning loop), and what is **non-agentic scaffolding** (context pipelines and trigger surfaces). This ADR is **taxonomy and boundaries**, not a full implementation map.

## Status

**Accepted** (2026-04-15)

## Context

The project ships a **Helm library chart**, a **Python hosted runtime**, **scheduled scrapers** (ETL into RAG), **inbound trigger bridges**, **Prometheus observability**, and optional **execution persistence** (checkpoints, correlation, feedback). Without an explicit split, docs, tests, and `values.yaml` comments drift into ambiguous terms (“observability,” “integration,” “tooling”) and teams conflate **ingress to a run** with **LLM-time actions** or **batch ingestion**.

Forces:

- **Separation of concerns:** batch ETL, HTTP trigger entry, and tool calls during a graph are different failure modes and credential surfaces.
- **First-class operations:** metrics and dashboards should be **on by default in spirit** (wired in chart design and examples), not an afterthought—even when individual clusters toggle scrape objects off.
- **Extensibility:** parent charts must add **their own** tools and jobs without forking core agent behavior.
- **Teaching cost:** every new feature needs a **named home** in the taxonomy to keep ADRs and OpenSpec changes aligned.

## Decision

### 1. Three-way split (conceptual)

| Pillar | Role |
|--------|------|
| **IaC / hosting** | Kubernetes manifests, chart defaults, dependencies, resource naming, optional ServiceMonitors, examples—**how** the stack is installed and observed as infrastructure. |
| **Agent** | The **declarative** supervisor graph: system prompt, config, **recursive subagents**, **tools** (including RAG retrieval when context sources exist), and **RLHF / feedback** capture (with a path toward richer “experience library” and SFT/RLHF-style loops later). |
| **Non-agentic scaffolding** | Everything that **feeds** the agent or **invokes** it without being part of the LLM loop: **sources of context** (scrapers / ETL into embeddings and entity/relationship stores) and **workflow triggers** (webhooks, cron-to-HTTP, standard app surfaces) that normalize to a **single programmatic entry** for starting a run. |

**Observability** (metrics exporters, log shape, Grafana dashboards, naming/cardinality rules) is a **first-class feature** of the chart: it is **part of the IaC pillar** in this taxonomy (deploy-time hooks and operator-facing assets), while remaining **semantically distinct** from **execution persistence** data ([ADR 0005](0005-observability-vs-execution-persistence.md), [ADR 0008](0008-persistence-backend-strategy.md)).

### 2. Agent internals (summary)

1. **Agent core** — Declarative definition under the library chart values (in a **parent** chart: nested under the dependency key, e.g. `declarative-agent-library:` per chart naming conventions; see `examples/*/values.yaml` and [`openspec/changes/declarative-agent-library-chart/specs/declarative-agent-library-chart/spec.md`](../../openspec/changes/declarative-agent-library-chart/specs/declarative-agent-library-chart/spec.md)). Maps to env/ConfigMap: system prompt, chat model, `subagents`, `skills`, checkpoints, W&B, etc.
2. **Tools** — Structured into:
   - **RAG** — Retrieval against chart-managed (or configured) vector / RAG HTTP surface when **sources of context** are enabled.
   - **Built-in** — Curated integrations shipped with the library/runtime (e.g. Jira, Slack patterns where promoted).
   - **Extendable** — Parent chart or image adds tools; library documents hooks and allowlists (e.g. MCP-style enabled tool lists).
3. **RLHF** — Human or product **feedback** captured in the persistence/telemetry story; future work may add **experience libraries** (archival/curated trajectories) and **SFT/RLHF** pipelines **out of the box** in the product sense—without collapsing them into “just another scraper.”

### 3. Non-agentic scaffolding (summary)

1. **Sources of context** — **Scrapers** / ETL jobs: scheduled or batch pipelines that **embed** text and structured **entities/relationships** for RAG; contract [ADR 0009](0009-scraper-job-contract-standard.md).
2. **Workflow triggers** — **Non-agentic** HTTP/app plumbing: ingress, verification, adapters that forward into the **single** runtime entry for starting a run ([ADR 0010](0010-trigger-contract-standard.md): `POST /api/v1/trigger` and equivalent internal calls). Not LLM tools and not RAG ingestion.

### 4. Diagram — high level (IaC band + agentic vs non-agentic)

Proportions: **upper ~2/3** = product surface (agentic | non-agentic); **lower ~1/3** = IaC/hosting.

```
**Declarative-Agent-Library-Chart gives you:**

+-----------------------------------------------------------------------------+
|                                        |                                    |
|      NON-AGENTIC SCAFFOLDING           |              THE AGENT             |
|   (HTTP triggers, sources of context)  |  (harness, tools, RLHF / feedback) |
|                                        |                                    |
+-----------------------------------------------------------------------------+
|                                                                             |
|                                       IaC                                   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### 5. Diagram — subcomponents (aligned columns; tools subdivided)

```
+-------------------------------------------------------------------+
| NON-AGENTIC SCAFFOLDING         | AGENTIC                         |
|  + Sources of context           |  + Agent (system prompt,        |
|    (scrapers / ETL -> RAG,      |    config, subagents, skills,   |
|    entities/relationships)      |    chat model, checkpoints,     |
|                                 |    W&B, etc.)                   |
|  + Workflow triggers (webhooks, |  + Tools:                       |
|    bridges, cron->HTTP) ->      |    | RAG (zero-config)          |
|    single programmatic entry    |    | Built-in (Jira, Slack, …)  |
|                                 |    | Extendable (in your chart) |
|                                 |  + RLHF / feedback (persistence |
|                                 |    & telemetry, future:         |
|                                 |    experience library, SFT/RLHF |
+----------------------------------+--------------------------------+
| IaC                                                               |
| + K8s Resources                                                   |
| + Observability (everything exports metrics, dashboards OOTB)     |
+-------------------------------------------------------------------+

## Consequences

**Positives**

- Clear **lanes** for ADRs and OpenSpec: scraper vs trigger vs tool vs observability vs persistence.
- Easier **Helm values** organization: blocks map to named pillars.
- **Onboarding** can point to one ADR before diving into [ADR 0009](0009-scraper-job-contract-standard.md), [ADR 0010](0010-trigger-contract-standard.md), [ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md).

**Trade-offs**

- Some components **touch two pillars** (e.g. scraper **metrics** are IaC/observability; scraper **logic** is non-agentic). Readers must use **“primary ownership”** for classification.
- **Documentation and tests** must repeatedly state which pillar they evidence, or drift returns.
- **Parent vs library values** naming (`declarative-agent-library:` nesting) adds indirection for newcomers ([ADR 0006](0006-config-surface-alpha-breaking-changes.md) alpha posture).

**What becomes harder**

- Drawing **hard lines** in prose when a feature is split (feedback from Slack reactions vs Slack **trigger** vs Slack **tools**).
- Keeping **“single /trigger surface”** true as new transports appear—each must normalize to the same pipeline ([ADR 0010](0010-trigger-contract-standard.md)).

## Alternatives considered

1. **One undifferentiated chart** — Single blob of values and templates without lanes; rejected: operational and security boundaries blur (credentials, review scope).
2. **Three separate charts** (agent / scrapers / observability) — Strong isolation; rejected for now: higher install and versioning friction for a library meant to compose as one product.
3. **Observability as optional add-on only** — Metrics and dashboards treated as non-core; rejected: operating agents without metrics is a poor default story; chart keeps observability **first-class** even when flags disable specific resources.
4. **Triggers implemented as “just tools”** — Rejected: tools run **inside** an existing graph; triggers **start** runs and carry different auth and idempotency expectations ([ADR 0010](0010-trigger-contract-standard.md)).

## Boundaries / non-goals

**Not “the agent” (in this taxonomy’s primary sense)**

- Scraper CronJobs, RAG deployment, job ConfigMaps, watermark volumes.
- Ingress, trigger Deployments, webhook verification at the edge.
- Prometheus Operator CRs, Grafana JSON **as shipped artifacts** (IaC), though the agent **emits** metrics consumed by them.

**Is “the agent”**

- LangGraph (or successor) **supervisor** run triggered via [ADR 0010](0010-trigger-contract-standard.md) entrypoints.
- **Subagents** and **skills** resolved during that run.
- **Tool** invocations (RAG, built-in, extendable) **during** the run.
- **Feedback** capture that attributes signals to runs/threads (RLHF lane).

This ADR does **not** mandate a particular folder layout in the repo beyond what existing ADRs already state; it **names** the shape for docs and reviews.

## Related decisions

| Topic | ADR |
|-------|-----|
| Observability metrics vs execution persistence | [ADR 0005](0005-observability-vs-execution-persistence.md) |
| Alpha Helm/env breaking changes | [ADR 0006](0006-config-surface-alpha-breaking-changes.md) |
| Durable execution persistence | [ADR 0008](0008-persistence-backend-strategy.md) |
| Scraper job contract | [ADR 0009](0009-scraper-job-contract-standard.md) |
| Trigger contract, single pipeline entry | [ADR 0010](0010-trigger-contract-standard.md) |
| Prometheus metric naming and cardinality | [ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md) |

## Implications for config

**Library chart `values.yaml` (direct consumers)** — Logical groupings (keys evolve per [ADR 0006](0006-config-surface-alpha-breaking-changes.md)):

- **Agent / declarative core** — `systemPrompt`, `chatModel`, `subagents`, `skills`, `mcp`, `checkpoints`, `wandb`, `service`, `resources`, `extraEnv`, etc.
- **Non-agentic: sources of context** — `scrapers.*` (per-source jobs, auth secret refs, `scrapers.ragService`, shared scraper `resources`).
- **IaC: observability** — `observability.prometheusAnnotations`, `observability.serviceMonitor`, `observability.structuredLogs`, plus RAG/scraper ServiceMonitor templates tied to scrape registry ([ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md)).

**Parent application charts** — Values typically nest under the dependency name (e.g. `declarative-agent-library:`). Triggers may appear as sibling OpenSpec-driven templates or future `triggers.*` blocks; they remain **architecturally non-agentic** even when keys sit beside agent values for ergonomics.

**Mental map:** `declarative-agent-library` subtree ≈ agent + shared chart resources; `scrapers` ≈ context sources + RAG service; `observability` ≈ IaC operator surface; trigger wiring ≈ ingress/bridge charts + runtime route `POST /api/v1/trigger`.

## Glossary

| Term | Meaning |
|------|---------|
| **Scaffolding** | Non-agentic **plumbing** that **invokes** the agent or **prepares** context (triggers, scrapers, ingress), as opposed to the LLM graph itself. |
| **Source of context** | A **batch or scheduled** pipeline (scraper, ETL) that writes **embeddings and/or structured artifacts** into RAG (or successor stores) for **retrieval during** runs. |
| **Trigger** | An **external event or schedule** normalized to start a run via the **single trigger entry** ([ADR 0010](0010-trigger-contract-standard.md)); **not** a tool call. |
| **Tool** | A capability **invoked by the agent** during a run (RAG query, Jira API, user-defined action), with a distinct config/credential surface from triggers and scrapers. |
