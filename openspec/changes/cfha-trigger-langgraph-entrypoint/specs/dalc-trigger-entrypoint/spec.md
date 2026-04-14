## ADDED Requirements

### Requirement: Trigger is the sole external launch path

The runtime SHALL expose exactly one HTTP path intended for external callers to **start an agent run**: `POST /api/v1/trigger`. Integrations such as webhooks, schedulers, or gateway services SHALL call this path (directly or via an application-specific forwarder) rather than invoking removed orchestration endpoints.

#### Scenario: Webhook forwards to trigger

- **WHEN** an external integration needs to start a run
- **THEN** it SHALL issue `POST /api/v1/trigger` (with optional JSON body as specified by implementation) and SHALL NOT rely on `POST /api/v1/subagents/{name}/invoke`, `POST /api/v1/skills/load`, or `POST /api/v1/tools/invoke`

### Requirement: Request correlation headers

The runtime SHALL accept an incoming `X-Request-Id` header on `POST /api/v1/trigger`. If the header is absent, the runtime SHALL generate a request identifier. The same identifier SHALL be returned to the client on the HTTP response (e.g. `X-Request-Id` response header). The runtime SHALL forward that identifier on outbound HTTP requests performed as part of handling that trigger (at minimum: requests to the configured RAG base URL).

#### Scenario: Client sends request id

- **WHEN** a client calls `POST /api/v1/trigger` with `X-Request-Id: abc-123`
- **THEN** the response includes `X-Request-Id: abc-123` and any outbound RAG HTTP call during that request includes `X-Request-Id: abc-123`

#### Scenario: Client omits request id

- **WHEN** a client calls `POST /api/v1/trigger` without `X-Request-Id`
- **THEN** the response includes an `X-Request-Id` chosen by the runtime and outbound HTTP calls use that same value

### Requirement: Documentation matches the entrypoint contract

Project documentation (including top-level README for `config-first-hosted-agents`, observability docs, and Helm values help text) SHALL state that **`POST /api/v1/trigger` is the supported way to launch a run** and SHALL describe request ID behavior. Documentation SHALL NOT present removed orchestration HTTP routes as supported integration APIs.

#### Scenario: Operator reads README

- **WHEN** an operator follows `README.md` to integrate an agent
- **THEN** they find clear instructions to use `POST /api/v1/trigger` for launch and `X-Request-Id` propagation expectations
