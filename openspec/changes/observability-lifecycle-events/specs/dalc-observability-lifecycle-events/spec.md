# Delta spec: dalc-observability-lifecycle-events

Draft for review; promotion copies normative SHALL rows into `openspec/specs/dalc-observability-lifecycle-events/spec.md`.

## ADDED Requirements

### Requirement: [DALC-REQ-OBS-LIFE-001] Stable lifecycle event vocabulary

The runtime SHALL publish lifecycle work using stable string names under the `agent.observability.events.EventName` enumeration, including at minimum: `run.started`, `run.ended`, `trigger.request.{received,responded,failed}`, `llm.generation.{started,first_token,completed,failed}`, `tool.call.{started,completed,failed}`, `subagent.invocation.{started,completed,failed}`, `skill.load.{started,completed,failed}`, `rag.embed.completed`, `rag.query.completed`, `scraper.run.completed`, `scraper.rag.embed.attempt`, and `feedback.recorded`.

#### Scenario: Event names are enumerated

- **WHEN** instrumentation emits a lifecycle signal
- **THEN** it SHALL use `EventName` values (not ad hoc strings) for publish operations

---

### Requirement: [DALC-REQ-OBS-LIFE-002] Middleware owns instrumentation boundaries

Business tools (Slack/Jira MCP modules) SHALL NOT call Prometheus or legacy `observe_*` helpers directly for lifecycle metrics; HTTP trigger, `run_tool_json`, LLM callbacks, RAG HTTP middleware, and scraper runtime SHALL publish through `agent.observability.middleware` helpers or equivalent bus publishers registered for that process.

#### Scenario: Slack Web API tools stay metric-free

- **WHEN** an LLM-time Slack tool executes
- **THEN** the tool module SHALL NOT increment Prometheus counters; MCP-level metrics SHALL be emitted once from the shared tool pipeline with bounded labels

---

### Requirement: [DALC-REQ-OBS-LIFE-003] Legacy metrics shim until Prometheus plugin

When the legacy Prometheus bridge is registered on a process bus, publishing completion events for tools, triggers, LLM generations, RAG HTTP paths, and scraper runs SHALL preserve **`dalc_*` Prometheus metric names** (see **ADR 0011**) and label semantics expected by dashboards and scrape docs.

#### Scenario: HTTP trigger counters unchanged

- **WHEN** `POST /api/v1/trigger` completes successfully
- **THEN** `dalc_http_trigger_requests_total{result="success"}` SHALL increment as observed by the existing test suite

---

### Requirement: [DALC-REQ-OBS-LIFE-004] Independent agent vs scraper buses

The agent HTTP process and scraper CronJob processes SHALL each construct an isolated `SyncEventBus` instance; scraper lifecycle events SHALL NOT be published to the agent pod bus at runtime.

#### Scenario: Scraper embed attempts use scraper bus

- **WHEN** a scraper posts to RAG `/v1/embed`
- **THEN** metrics SHALL be recorded via the scraper process bus subscribers (same Helm `observability.plugins` tree, distinct instance)

---

### Requirement: [DALC-REQ-OBS-LIFE-005] Opt-in plugins and graceful degradation

Observability plugins (Prometheus, Langfuse, W&B, Grafana, log shipping) SHALL be disabled by default in Helm values; an absent or disabled plugin SHALL NOT cause runtime request handling to fail.

#### Scenario: Default chart values stay safe

- **WHEN** all `observability.plugins.*.enabled` flags are false
- **THEN** chart rendering and agent startup SHALL succeed without additional configuration
