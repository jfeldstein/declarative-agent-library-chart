## ADDED Requirements

### Requirement: LangGraph replaces subagent, skill, and tool HTTP handlers

The behaviors previously implemented by `POST /api/v1/subagents/{name}/invoke`, `POST /api/v1/skills/load`, and `POST /api/v1/tools/invoke` SHALL be implemented using **LangGraph** orchestration invoked from the trigger handling path. Those three HTTP routes SHALL NOT remain part of the public API.

#### Scenario: No public subagent invoke route

- **WHEN** a client sends `POST /api/v1/subagents/example/invoke`
- **THEN** the server responds with `404 Not Found` (or another consistent non-success status indicating the route is not served)

#### Scenario: No public skill load route

- **WHEN** a client sends `POST /api/v1/skills/load` with a JSON body
- **THEN** the server responds with `404 Not Found` (or another consistent non-success status indicating the route is not served)

#### Scenario: No public tools invoke route

- **WHEN** a client sends `POST /api/v1/tools/invoke` with a JSON body
- **THEN** the server responds with `404 Not Found` (or another consistent non-success status indicating the route is not served)

### Requirement: Graph honors declarative config

The LangGraph execution path SHALL consume the same declarative configuration sources already used by the runtime for subagents, skills, and allowlisted MCP tools (e.g. environment/ConfigMap-derived `RuntimeConfig`), so that Helm values continue to drive behavior without separate HTTP calls.

#### Scenario: Enabled tool from config is invokable from the graph

- **WHEN** a tool identifier is allowlisted in runtime configuration for the deployment
- **THEN** the graph execution path MAY invoke that tool during a trigger run subject to the same allowlist and skill-unlock rules as the previous implementation

### Requirement: Observability for orchestration

The implementation SHALL expose metrics or structured logs sufficient to observe LangGraph-based runs (e.g. per-phase counters or durations) without requiring the removed HTTP endpoints. Existing `POST /api/v1/trigger` metrics SHALL continue to record overall trigger success and latency.

#### Scenario: Successful trigger after graph execution

- **WHEN** a trigger run completes successfully through the LangGraph path
- **THEN** `agent_runtime_http_trigger_requests_total{result="success"}` (or its documented successor) is incremented and no caller depends on subagent HTTP metrics for basic health verification
