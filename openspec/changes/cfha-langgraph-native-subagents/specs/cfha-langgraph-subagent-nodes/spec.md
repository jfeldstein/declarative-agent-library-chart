## ADDED Requirements

### Requirement: Subagent units implement configured roles

For each entry in `HOSTED_AGENT_SUBAGENTS_JSON` with a non-empty `name`, the runtime SHALL provide an **invokable subagent unit** that honors **`role`** (`default`, `metrics`, `rag`, or documented extensions) with the same **functional** behavior as today’s `_run_subagent_text` (Prometheus text for `metrics`, RAG HTTP proxy for `rag`, prompt-derived reply for `default`) when that unit is executed.

#### Scenario: RAG role subagent unit

- **WHEN** a subagent is configured with `role: rag` and valid RAG inputs are supplied to its invocation
- **THEN** the unit performs an HTTP request to the configured RAG base URL with **`X-Request-Id`** propagation and returns the RAG response body as a string result to its caller

### Requirement: Subagent units are graph-backed implementations

Each subagent unit SHALL be implemented using **LangGraph-native** composition where practical (e.g. **subgraph** or compiled runnable per subagent) so that execution is not a single opaque function call only, and remains extensible for tracing and future checkpoint policies.

#### Scenario: Distinct compiled units per subagent

- **WHEN** two subagents are configured with different `name` values
- **THEN** the runtime maintains two distinct invokable implementations (e.g. two tool wrappers or two subgraphs) that can be bound separately to the main agent

### Requirement: Observability for subagent execution

When a subagent unit runs as part of handling a trigger, the runtime SHALL record **`agent_runtime_subagent_*`** metrics for that **subagent** name and **result** (success vs error) consistent with existing series.

#### Scenario: Subagent tool failure

- **WHEN** a subagent unit errors (e.g. missing RAG URL, HTTP failure)
- **THEN** `agent_runtime_subagent_invocations_total` (or documented successor) records an **error** for that subagent name
