## Why

Hosted agents need a **consistent runtime surface** for data ingestion, retrieval, tool exposure, and multi-agent composition. Today those concerns are implicit or ad hoc; defining **scrapers, tools (MCP), subagents, a shared RAG HTTP service, and skills** as first-class, config-driven components lets each agent enable only what it needs while reusing the same platform building blocks.

## What Changes

- Introduce a **managed RAG HTTP service** with **`POST /embed`** and **`POST /query`** (or equivalent REST contract) so any runtime component can index content and search without owning vector storage details. The RAG store SHALL support **entities and relationships between them** (declarative at ingest, usable in retrieval: neighbors, typed edges, documented hop limits). **RBAC and multi-tenant auth for RAG are explicitly out of scope** for this change.
- Define **scheduled scrapers** (e.g. cron) that run **per configured integration** (examples: Slack channels, Google Doc freshness, JIRA project preload). **Which scrapers exist and which are enabled** is driven by configuration so not every agent ships every scraper.
- Define **tools** as **functions implemented in modules**, exposed to agents as **MCP servers/tools**; **enablement is config-driven** so agents opt into subsets.
- Define **subagents** as additional **values/config objects** (e.g. system prompt, enabled scrapers, tools, and related fields), aligned with the LangChain **subagents** pattern (supervisor invokes subagents as tools, isolated context). See [LangChain Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents).
- Define **skills** as **progressive-disclosure** specializations (e.g. load-on-demand prompts and optional extra tools), aligned with the LangChain **skills** pattern. See [LangChain Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills).

## Capabilities

### New Capabilities

- `runtime-rag-http`: Shared RAG service over HTTP (`/embed`, `/query`), fully managed for producers and consumers; **entity–relationship** model at ingest and query (not flat-only chunks). RBAC deferred.
- `runtime-scrapers`: Cron-driven scrapers with per-integration configuration (Slack, Google Docs, JIRA, etc.); enable/disable via config per agent or deployment.
- `runtime-tools-mcp`: Tool implementations in modules, surfaced as MCP servers/tools; enable/disable via config.
- `runtime-subagents`: Declarative subagent definitions in values (system prompt, scrapers, tools, and related knobs) consistent with LangChain subagent architecture.
- `runtime-skills`: Skills pattern for on-demand specialization (prompts and optional dynamic tooling), consistent with LangChain skills documentation.

### Modified Capabilities

- (none — no published requirement specs under `openspec/specs/` today that this change amends.)

## Impact

- **Python coverage (ADR 0002)**: first-party runtime packages under `src/hosted_agents/`, including **`hosted_agents/observability/`**, are measured by **`pytest-cov`** with **no** broad `omit` that hides whole subtrees; landing observability or checkpoint helpers requires accompanying tests like any other runtime code.
- **Helm/values and application config** for config-first hosted agents (or successor charts) gain structured sections for RAG endpoint usage, scraper schedules, MCP tool sets, subagents, and skills.
- **New or extended services**: at minimum a RAG HTTP API and scraper jobs; MCP tool processes or sidecars as designed in `design.md`.
- **Dependencies**: vector DB / embedding stack behind RAG (implementation detail in design); integration SDKs or credentials for each scraper type.
- **Documentation**: links to LangChain subagents and skills docs for behavioral alignment, without requiring LangChain as the only implementation language.
