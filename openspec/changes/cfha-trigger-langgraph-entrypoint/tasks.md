## 1. Dependencies and graph skeleton

- [x] 1.1 Add LangGraph (and any required LangChain compatibility packages) to `helm/src/pyproject.toml` and refresh the lockfile with `uv lock`
- [x] 1.2 Create a module (e.g. `hosted_agents/graph.py` or `hosted_agents/graph/`) that compiles a `StateGraph` from `RuntimeConfig` and exposes a single entry function used by the HTTP layer

## 2. Replace HTTP handlers with graph-backed trigger

- [x] 2.1 Remove `invoke_subagent`, `load_skill`, and `tools_invoke` route handlers from `app.py` (former `/api/v1/subagents/...`, `/api/v1/skills/load`, `/api/v1/tools/invoke`)
- [x] 2.2 Wire `POST /api/v1/trigger` to invoke the LangGraph graph instead of only `trigger_reply_text`, preserving hello-world behavior when config is minimal (optional JSON body, default env prompt path)
- [x] 2.3 Implement graph nodes or tools for prior behaviors: default/metrics/rag subagent roles, skill unlock + prompt injection, allowlisted MCP `invoke_tool`—reusing `subagent_system_prompt`, `unlock_tools` / `unlocked_tools`, and `invoke_tool` as appropriate

## 3. Request ID propagation

- [x] 3.1 Thread `request_id` from the Starlette request into the graph invocation context
- [x] 3.2 Ensure all `httpx` outbound calls from the trigger path (RAG proxy and any HTTP-using tools) send `X-Request-Id` matching the incoming or generated id

## 4. Metrics, summary, and tests

- [x] 4.1 Map or extend Prometheus metrics so trigger and graph phases remain observable; remove or replace metric hooks tied only to deleted HTTP routes (`observe_subagent` / `observe_skill_load` / `observe_mcp_tool` usage as applicable)
- [x] 4.2 Update `GET /api/v1/runtime/summary` to reflect the new model (no implication that subagent/skill/tool HTTP endpoints exist)
- [x] 4.3 Update or replace tests in `helm/src/tests/` (`test_subagent_roles.py`, `test_agent_extensions.py`, `test_o11y_metrics.py`, others referencing removed routes) to assert graph/trigger behavior and request-id forwarding
- [x] 4.4 Run `pytest` for the runtime package and fix failures

## 5. Documentation and packaging

- [x] 5.1 Update `README.md` (endpoints, curl examples, values table) for trigger-only launch and LangGraph
- [x] 5.2 Update `docs/observability.md`, `grafana/README.md`, `helm/chart/values.schema.json`, `helm/src/src/hosted_agents/tools_impl/README.md`, and chart test docs that mention removed APIs
- [x] 5.3 Resolve design open question: either keep `POST /api/v1/rag/query` as a documented non-launch utility or remove it and update specs/docs accordingly
