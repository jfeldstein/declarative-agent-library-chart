## Why

The hosted agent runtime currently exposes several HTTP paths (`subagents`, `skills/load`, `tools/invoke`) that duplicate orchestration concerns that belong in a single agent graph. Operators and future webhooks need one stable contract: **start a run** via `POST /api/v1/trigger`, with **request correlation** propagated end-to-end. Consolidating orchestration behind **LangGraph** reduces surface area, aligns with multi-agent patterns, and makes documentation truthful about how the agent is launched.

## What Changes

- **BREAKING**: Remove public HTTP routes that today implement supervisor-style subagent invoke, progressive skill load, and direct MCP tool invoke (`POST /api/v1/subagents/{name}/invoke`, `POST /api/v1/skills/load`, `POST /api/v1/tools/invoke`). Their behavior moves into a **LangGraph**-backed execution path invoked from the trigger flow (or equivalent single entry), not as separate REST endpoints.
- **`POST /api/v1/trigger` remains the only supported way to *launch* an agent run** from outside the process; webhooks and other integrations must call this path (or an app-specific shim that forwards to it) rather than calling subagent/skill/tool HTTP APIs.
- **Request ID propagation**: Incoming `X-Request-Id` (or generated id) must be forwarded on outbound HTTP calls made during a trigger run (e.g. RAG proxy, future tool backends) so logs and upstream systems stay correlated.
- **Documentation update**: README, observability docs, Helm values schema descriptions, and integration scripts/tests that reference the removed routes must be revised to describe trigger-only launch and LangGraph-based orchestration.

## Capabilities

### New Capabilities

- `cfha-trigger-entrypoint`: Single external entry for launching agent runs; correlation headers; contract for how webhooks and other surfaces integrate.
- `cfha-langgraph-runtime`: LangGraph-based graph replaces the HTTP handlers that previously exposed subagent, skill, and tool invocation as separate APIs; metrics and error semantics remain observable.

### Modified Capabilities

- _(none — no existing `openspec/specs/` capability documents for this project yet)_

## Impact

- **Code**: `runtime/src/hosted_agents/app.py` (and related modules: metrics, tests, models), new LangGraph wiring and dependencies in the runtime `pyproject.toml` / lockfile.
- **APIs**: **BREAKING** removal of three REST endpoints; possible extension of trigger request/response shape if the graph needs input payload (to be detailed in design).
- **Docs & ops**: `README.md`, `docs/observability.md`, `helm/chart/values.schema.json`, Grafana/README copy, chart tests, `scripts/integration_kind_o11y_prometheus.sh`, runtime tests under `runtime/tests/`.
