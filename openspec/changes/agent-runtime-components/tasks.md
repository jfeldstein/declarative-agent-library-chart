## 1. RAG HTTP service

- [x] 1.1 Define request/response schemas for **`POST /v1/embed`** and **`POST /v1/query`** (including error shapes and limits) and document them beside the service (**`docs/rag-http-api.md`**; versioned paths, not unversioned **`/embed`** / **`/query`** only).
- [x] 1.2 Implement the RAG HTTP service with a backing embedding pipeline and vector store, deployable alongside existing agent charts.
- [x] 1.3 Add health checks and a minimal integration test or smoke script that embeds a fixture document and retrieves it via **`/v1/query`**.
- [x] 1.4 Specify **entity id**, **entity type**, and **edge** (source, target, relationship type) in the HTTP API (extensions to **`/embed`** and/or dedicated upsert endpoints) and document scopes/namespaces.
- [x] 1.5 Implement persistence and **relationship-aware** **`/query`** behavior (neighbor expansion and/or graph constrained retrieval) per **`runtime-rag-http`**.
- [x] 1.6 Extend the smoke test to ingest two linked entities and assert the query response exposes the **relationship** (ids and type) per spec.
- [x] 1.7 Expose **`/metrics`** on the RAG service and register **`agent_runtime_rag_embed_*`** and **`agent_runtime_rag_query_*`** per **`runtime-rag-http`**; assert series appear in smoke tests or CI.

## 2. Configuration schema and documentation

- [ ] 2.1 Extend Helm **`values.schema.json`** with tunables for **RAG** (under **`scrapers.ragService`** and related **`scrapers`/`scrapers.jobs`** shapes—**no** separate top-level **`rag:`** key), plus **`scrapers`**, **`tools`/`mcp`**, **`subagents`**, and **`skills`**. *(Checkbox stays open until a maintainer explicitly accepts “RAG under **`scrapers`**” as satisfying this task or promotes a spec rename.)*
- [x] 2.2 Document in README or operator docs how each section maps to the five runtime components and cross-link LangChain [Subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents) and [Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills) for behavioral alignment.

## 3. Scheduled scrapers

- [x] 3.1 Add Kubernetes **`CronJob`** (or equivalent) templates parameterized by values for enabled scrapers, schedules, and credentials references.
- [x] 3.2 Implement at least one scraper type end-to-end (fetch → normalize → **`POST /v1/embed`**) and additional integrations (**Jira**, **Slack**) per **`scrapers.jobs`**; there is **no** separate **`reference`** scraper type in the chart anymore.
- [ ] 3.3 **Helm:** assert disabled scrapers omit CronJobs; enabled scrapers render CronJobs with expected schedules (**`helm unittest`** / CI). **Runtime:** Cron firing on a live cluster remains a manual or opt-in integration check (not default PR CI).
- [x] 3.4 Instrument scraper processes with **`agent_runtime_scraper_runs_total`**, **`agent_runtime_scraper_run_duration_seconds`**, and **`agent_runtime_scraper_rag_submissions_total`** per **`runtime-scrapers`**.

## 4. MCP tools from modules

- [x] 4.1 Establish a module layout and packaging pattern for tool implementations with MCP manifest or code-first registration.
- [x] 4.2 Wire agent runtime to connect only to MCP servers/tools listed in values for that deployment.
- [ ] 4.3 **`sample.echo`** is the sample tool module. **Still open:** automated lint/snapshot proving Helm **`mcp.enabledTools`** ⊆ registered tool ids in **`dispatch.py`**.
- [x] 4.4 Register **`agent_runtime_mcp_tool_calls_total`** and **`agent_runtime_mcp_tool_duration_seconds`** on the agent (or MCP bridge) per **`runtime-tools-mcp`**.

## 5. Subagents

- [x] 5.1 Parse subagent blocks from values into distinct runtime configurations (system prompt, scraper/tool/skill flags).
- [x] 5.2 Implement supervisor orchestration so the main agent invokes each subagent via a tool-like boundary with **stateless per-invocation** subagent context.
- [x] 5.3 Add an example values snippet with two subagents and document how operators extend it.
- [x] 5.4 Register **`agent_runtime_subagent_invocations_total`** and **`agent_runtime_subagent_duration_seconds`** per **`runtime-subagents`**.

## 6. Skills

- [x] 6.1 Implement a skill catalog loaded from configuration (name → prompt source, optional tool bindings).
- [x] 6.2 Expose a **load skill** mechanism to the agent (tool or equivalent) that applies progressive disclosure per **`runtime-skills`** spec.
- [ ] 6.3 **Load:** **`load_skill`** unlocks tools per catalog (**`test_skill_load_unlocks_tool`**). **Unload / operator-visible reload cycle** for skill-bound tools is not fully implemented (test-only **`reset_skill_unlocked_tools`**); checkbox open until unload semantics ship.
- [x] 6.4 Register **`agent_runtime_skill_loads_total`** and **`agent_runtime_skill_load_duration_seconds`** per **`runtime-skills`**.

## 7. Verification

- [x] 7.1 Run **`helm lint`** / **`helm template`** on the affected chart(s) after values schema updates.
- [ ] 7.2 **Today:** separate automated tests cover scraper → **`/v1/embed`**, RAG **`/v1/query`**, **`POST /api/v1/trigger`**, and MCP tool calls—not necessarily one continuous integration test spanning all hops. Checkbox open if you require a single stitched E2E.
- [x] 7.3 Document **`agent_runtime_*`** metric names and label conventions in **`docs/observability.md`** and link **`grafana/dalc-overview.json`**, **`grafana/cfha-token-metrics.json`**, and **`grafana/README.md`**. *(Older OpenSpec change **`agent-centralized-o11y`** lives under **`openspec/changes/archive/`**; cite current DALC paths, not that folder name, when updating this task.)*
