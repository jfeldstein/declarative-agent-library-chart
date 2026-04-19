## ADDED Requirements

### Requirement: [DALC-REQ-LANGFUSE-TRACE-001] Langfuse SDK bridge listens to lifecycle bus segments

When Langfuse credentials are configured, the hosted agent runtime SHALL instantiate a Langfuse SDK client during agent process bootstrap and subscribe to the synchronous lifecycle bus (`SyncEventBus`) such that emitted events corresponding to HTTP trigger completion, supervised LLM completions, MCP-style tool invocation, skill loading, subagent delegation, and RAG embed/query timings create Langfuse traces and/or **observations** compatible with traces, generations (LLM spans), spans (tools / retrieval / ancillary work), scores (when structured feedback payloads are emitted), sessions (bounded session identifiers propagated via Langfuse trace attributes), and bounded tags listing trigger flavor (`http`, `slack`, …).

Implementations SHOULD limit observation inputs/outputs to **bounded operational fields** (identifiers, enums, durations, counts) and MUST NOT synthesize Langfuse payloads from unstructured prompt/output bodies sourced from end users unless those bodies have already passed through middleware redaction policies documented elsewhere.

#### Scenario: Successful trigger emits trace observations

- **WHEN** a supervised run publishes `llm.generation.completed` with token counts and publishes `trigger.request.responded` indicating successful HTTP completion
- **THEN** Langfuse-facing code SHALL flush batched ingest data as part of completing the HTTP trigger lifecycle so operators see near-real-time telemetry for that run

---

### Requirement: [DALC-REQ-LANGFUSE-TRACE-002] Helm values wire Langfuse connectivity

The Helm library chart SHALL expose `observability.plugins.langfuse.*` keys that operators can tune without editing helpers directly:

- `enabled` toggles plugin activation for the agent Deployment.
- `host` maps to `HOSTED_AGENT_LANGFUSE_HOST`.
- `flushIntervalSeconds` maps to `HOSTED_AGENT_LANGFUSE_FLUSH_INTERVAL_SECONDS` for SDK batching configuration.
- `publicKeySecret` / `secretKeySecret` map to `HOSTED_AGENT_LANGFUSE_PUBLIC_KEY` / `HOSTED_AGENT_LANGFUSE_SECRET_KEY` via `secretKeyRef`.

When `enabled` is false, the chart SHALL emit none of these variables except what operators opt into via `extraEnv`.

#### Scenario: Operator enables Langfuse with secrets

- **WHEN** `observability.plugins.langfuse.enabled` is true and host + secret refs are supplied
- **THEN** rendered agent manifests SHALL include the Langfuse env wiring described above with secret-backed keys

---

### Requirement: [DALC-REQ-LANGFUSE-TRACE-003] Langfuse bridge does not own PII redaction

The Langfuse integration SHALL treat **prompt redaction, token hygiene, and human-data minimization** as responsibilities of HTTP middleware, LangGraph instrumentation shims, and persistence layers already governed by observability architecture.

The Langfuse bridge MUST NOT introduce parallel redaction pipelines or duplicate privacy controls; instead it SHALL emit only bounded labels/metadata (`tenant_id`, tool identifiers, structured counters) consistent with existing lifecycle events.

#### Scenario: Generation observations avoid raw prompts

- **WHEN** Langfuse generations are emitted from lifecycle events
- **THEN** implementations MUST avoid attaching raw chat transcripts by default and MUST document that operators rely on middleware/stores for prompt/output capture policies

---

### Requirement: [DALC-REQ-LANGFUSE-TRACE-004] Flush interval propagates to SDK batching

When `HOSTED_AGENT_LANGFUSE_FLUSH_INTERVAL_SECONDS` is set to a positive floating-point value, the Langfuse SDK client SHALL be constructed with the matching `flush_interval` parameter so operators can tune batching latency versus overhead without rebuilding images.

#### Scenario: Flush interval env honored

- **WHEN** `HOSTED_AGENT_LANGFUSE_FLUSH_INTERVAL_SECONDS` is present and positive
- **THEN** client construction SHALL forward the interval to `Langfuse(..., flush_interval=...)`
