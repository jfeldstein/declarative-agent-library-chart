## Context

The **config-first hosted agents** direction treats agent behavior as declarative configuration (Helm values and related config). This change specifies **five runtime component classes**—**RAG over HTTP**, **scheduled scrapers**, **MCP-exposed tools**, **subagents**, and **skills**—so operators can compose agents without each team re-solving ingestion, retrieval, tool wiring, and multi-agent structure.

Relevant external patterns:

- **Subagents**: central supervisor invokes specialized agents as tools; isolated context per invocation. See [LangChain Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents).
- **Skills**: progressive disclosure of specialized prompts (and optionally extra tools) via a loader tool. See [LangChain Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills).

## Goals / Non-Goals

**Goals:**

- Provide a **single managed RAG HTTP API** with **`/embed`** and **`/query`** so scrapers, agents, and other services **add** documents or chunks and **search** without embedding provider or vector store details leaking into every component.
- Model **entities and relationships** (typed edges, stable ids, scoped namespaces) so ingestion can express structure (e.g. JIRA issue → epic, Doc → folder, Slack message → thread) and retrieval can **expand or constrain** results using that graph, not only lexical/semantic similarity over isolated chunks.
- Run **scrapers on a schedule** (cron semantics) where each scraper type maps to **integration-specific configuration** (e.g. Slack channels, Doc IDs, JIRA project keys).
- Expose **tools** from **versioned modules** through **MCP** (servers and tool listings) with **per-agent or per-deployment enablement**.
- Model **subagents** as **repeatable config blocks** in values (system prompt, enabled scrapers/tools, model overrides where applicable), orchestrated consistently with the subagent pattern (supervisor calls subagent-as-tool).
- Support the **skills** pattern: named skills, discoverable list, on-demand load into context, optional registration of additional tools when a skill loads.

**Non-Goals:**

- **RBAC**, **row-level security**, or **per-tenant isolation** for RAG or scraper data (may be added later).
- Choosing a single orchestration framework: specs are **pattern-aligned** with LangChain docs; implementation may use LangGraph, custom code, or other stacks if behavior matches requirements.
- Defining every possible third-party integration in v1: specs require **extensibility** and **at least** the example classes the proposal names; concrete connector matrix can grow incrementally.

## Decisions

1. **RAG is a dedicated HTTP service**  
   **Rationale:** Clear contract (`/embed`, `/query`), one place to operate embeddings, indexing, and backing store.  
   **Alternatives:** Embed library linked into each pod — duplicates config and complicates upgrades.

2. **Vector retrieval plus an explicit entity–relationship layer**  
   **Rationale:** Pure chunk RAG loses structure that scrapers already know (parent/child, authorship, ticket links). Persisting **entities** and **typed relationships** allows **query expansion**, **graph filters**, and **explainable** context for agents.  
   **Alternatives:** Encode all structure only in chunk text — harder to query consistently; separate graph DB only — splits truth; hybrid or single service owning both vectors and edges keeps one integration point for callers.

3. **Scrapers are scheduled workloads independent of the interactive agent pod**  
   **Rationale:** Predictable load, failure isolation, and uniform cron semantics (Kubernetes `CronJob` or equivalent). Scrapers **call** RAG and integrations; they do not need user session state.  
   **Alternatives:** In-process loops inside the agent — harder to scale and reason about for long crawls.

4. **Tools ship as MCP servers backed by code modules**  
   **Rationale:** Matches ecosystem tooling and agent runtimes that already consume MCP; modules give testability and clear packaging boundaries.  
   **Alternatives:** Only in-process Python functions — narrower; MCP keeps a stable external contract for tooling.

5. **Subagent definitions live alongside main agent values**  
   **Rationale:** One chart or values file describes the whole “team”: main agent plus N subagents with their own prompts and capability flags. Runtime wraps each subagent as an invocable tool for the supervisor.  
   **Alternatives:** Separate charts per subagent — more operational overhead for a single logical application.

6. **Skills are data + optional hooks, not a second agent hierarchy**  
   **Rationale:** Aligns with LangChain’s lightweight pattern: load prompt (and optionally register tools) on demand; keeps subagents for **separate** model/tool contexts.  
   **Alternatives:** Treat every skill as a subagent — heavier and blurs isolation semantics.

7. **Prometheus metrics use the `agent_runtime_*` prefix per component**  
   **Rationale:** Each capability spec names concrete counters and histograms (`agent_runtime_rag_*`, `agent_runtime_scraper_*`, `agent_runtime_mcp_tool_*`, `agent_runtime_subagent_*`, `agent_runtime_skill_*`) so Grafana dashboards and alerts stay stable across implementations. Labels (`integration`, `tool`, `subagent`, `skill`) MUST come from **bounded configuration**, not runtime-unbounded strings.  
   **Alternatives:** Generic RED metrics without names — harder to document SLOs per component.

## Risks / Trade-offs

- **[Risk] RAG becomes a single point of failure** → **Mitigation:** Health checks, retries from scrapers and agents, documented SLOs; horizontal scaling of the RAG service behind a Service.
- **[Risk] Graph explosion or expensive traversals** → **Mitigation:** Per-query caps on hops and result size; optional relationship-type allowlists; index or materialization strategy documented for operators.
- **[Risk] Cron scrapers overload external APIs** → **Mitigation:** Rate limits, backoff, and configurable schedules per integration; optional concurrency limits per scraper type.
- **[Trade-off] No RBAC on RAG** → All clients that can reach the network endpoint can embed/query; mitigated later with auth or network policies, not in this change.
- **[Risk] MCP tool sprawl** → **Mitigation:** Explicit enable lists in values; generated tool manifests or schemas for review in CI.

## Migration Plan

1. Land **OpenSpec** requirements (`proposal`, `design`, `specs`, `tasks`) and review with stakeholders.
2. Implement **RAG service** and wire **service discovery** (URL/config) for agents and scrapers.
3. Add **values schema** sections for scrapers, tools, subagents, and skills; document examples.
4. Implement **one reference scraper** and **one reference MCP tool module** to prove end-to-end paths (ingest → RAG → query; MCP → agent).
5. Roll out additional scraper/tool types incrementally without changing the core HTTP contracts.

## Open Questions

- **Embedding model and vector store** choices (managed cloud vs self-hosted) and whether `/embed` accepts **precomputed vectors** from trusted callers.
- Whether **`/query`** returns only text snippets, structured citations, or **both**, and maximum payload limits for production.
- Default **hop depth** and **relationship-type** filters for expansion, and whether **undirected** interpretation is allowed for selected edge types.
- **Credential storage** for scrapers and tools (Kubernetes Secrets vs external secret store) — required for implementation but orthogonal to component taxonomy.

## Checklist §D — `runtime-*` delta specs vs `openspec/specs/`

The five **`runtime-*`** specs under **`openspec/changes/agent-runtime-components/specs/`** remain **draft deltas** for this umbrella change. There is **no** matching **`openspec/specs/runtime-<name>/`** directory yet.

**Explicit fold (DALC sync remediation):** shipping today is reflected in other **promoted** capabilities (for example **`dalc-rag-from-scrapers`**, **`dalc-chart-runtime-values`**, **`dalc-agent-o11y-*`**). Standalone promotion of **`openspec/specs/runtime-rag-http/`**, **`runtime-scrapers/`**, **`runtime-skills/`**, **`runtime-subagents/`**, and **`runtime-tools-mcp/`** is **deferred** to a future OpenSpec promotion pass that lifts these drafts into long-lived **`dalc-*`** slugs with IDs + matrix rows per **`openspec/AGENTS.md`** §4.
