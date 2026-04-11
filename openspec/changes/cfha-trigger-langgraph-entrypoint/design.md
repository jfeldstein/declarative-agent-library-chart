## Context

The `config-first-hosted-agents` Python runtime (`hosted_agents`) is a FastAPI app. Today it exposes `POST /api/v1/trigger` (plain-text reply from configured system prompt) plus separate routes for RAG proxy, runtime summary, subagent invoke (including `metrics` and `rag` roles), skill load, and MCP tool invoke. Observability already binds `request_id` from `X-Request-Id` (or generates one) in `ObservabilityMiddleware` and echoes it on responses; outbound calls do not yet consistently attach that id.

## Goals / Non-Goals

**Goals:**

- Make **`POST /api/v1/trigger` the sole public HTTP entry** used to **launch** an agent run from outside the process.
- Replace the implementation behind the former **`subagents/{name}/invoke`**, **`skills/load`**, and **`tools/invoke`** routes with a **LangGraph** graph that runs inside the trigger request (or a clearly documented subgraph invoked only from trigger).
- **Forward `X-Request-Id`** (or the middleware’s chosen id) on outbound HTTP requests made during that run (minimum: RAG proxy calls; same pattern for any future HTTP tool backends).
- Keep **`GET /metrics`**, **`GET /api/v1/runtime/summary`** (updated fields), and existing **trigger metrics** (`agent_runtime_http_trigger_*`) unless specs require renaming—extend or add graph-phase metrics as needed without breaking PromQL dashboards unnecessarily.

**Non-Goals:**

- Choosing a specific checkpoint store or HITL product surface (may compose with other OpenSpec changes later).
- Rewriting the Helm library chart structure beyond values/docs/tests needed for the new contract.
- Mandating a particular LLM provider SDK beyond what the runtime already uses for `trigger_reply_text`—LangGraph integrates with existing call sites where practical.

## Decisions

1. **Single graph per trigger invocation**  
   **Decision:** Build (or retrieve a cached compiled) LangGraph `StateGraph` that encodes subagent routing, skill activation, and tool calls as nodes/edges instead of HTTP handlers.  
   **Rationale:** One process-local orchestration model; webhooks and cron only need trigger.  
   **Alternatives:** Keep HTTP micro-calls between internal services (rejected: extra surface and latency); multiple graphs per role (deferred unless complexity demands).

2. **Trigger payload**  
   **Decision:** If the graph needs structured input (e.g. webhook body, user message), extend `POST /api/v1/trigger` to accept an optional JSON body with a versioned schema while preserving a default that matches today’s env-only behavior for hello-world.  
   **Rationale:** External callers need a stable place to pass context without new paths.  
   **Alternatives:** Query params only (weak for rich payloads); new path (rejected: violates trigger-only launch).

3. **Request ID forwarding**  
   **Decision:** Thread `request_id` from Starlette `Request` into the graph context (or `configurable`) and set `headers={"X-Request-Id": request_id}` on `httpx` calls made during the run.  
   **Rationale:** Aligns with existing middleware logging.  
   **Alternatives:** W3C `traceparent` only—optional add-on later.

4. **Removal of HTTP routes**  
   **Decision:** Delete `invoke_subagent`, `load_skill`, and `tools_invoke` from `app.py` and remove/adjust tests that asserted those endpoints.  
   **Rationale:** User-requested replacement of lines 90–180 with LangGraph.  
   **Alternatives:** Deprecation period with `410 Gone`—only if product needs a transition window (call out in migration if adopted).

5. **`POST /api/v1/rag/query`**  
   **Decision:** **Keep** as a separate operational/debug path; document it as **not** the agent launch path (orchestration uses **`POST /api/v1/trigger`**).  
   **Rationale:** Direct RAG proxy remains useful for scripts and dashboards without running the full graph.

## Risks / Trade-offs

- **[Risk] Breaking integrators** that called subagent/skill/tool HTTP APIs → **Mitigation:** Major version note in README and Helm chart changelog; grep-based cleanup of docs and examples.
- **[Risk] LangGraph dependency weight** → **Mitigation:** Pin conservative versions; keep graph module thin and unit-tested without network.
- **[Risk] Trigger latency** increases if graph is heavier than one LLM call → **Mitigation:** metrics on phases; document expected behavior for hello-world vs. extended config.
- **[Risk] Request ID threading** missed on a code path → **Mitigation:** centralize outbound HTTP client factory used by RAG proxy and tools.

## Migration Plan

1. Implement graph + trigger integration behind feature flag **or** direct cutover in the same PR series as tasks (per repo practice).
2. Update all docs and Helm descriptions referencing removed endpoints.
3. Run runtime tests and kind/Prometheus script if it only uses trigger (already true); fix any test that used removed routes.
4. Rollback: revert deployment to prior image/chart version that still exposes old routes (keep git history).

## Open Questions

- _(resolved)_ **`POST /api/v1/rag/query`** remains as a **documented non-launch utility** for direct RAG proxying; agent orchestration uses **`POST /api/v1/trigger`**.
- _(resolved)_ Trigger JSON schema v1: optional **`load_skill`**, **`subagent`** (with RAG fields on the same object when `role: rag`), **`tool`** + **`tool_arguments`**; empty body preserves hello-world main reply behavior.
