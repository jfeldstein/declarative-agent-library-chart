## ADDED Requirements

### Requirement: [DALC-REQ-POSTGRES-AGENT-PERSISTENCE-001] Postgres LangGraph checkpointer integration

When `HOSTED_AGENT_CHECKPOINT_BACKEND` is set to `postgres` and a valid Postgres connection URL (or equivalent configuration) is supplied, the runtime SHALL construct a LangGraph-compatible checkpointer that persists checkpoint history to PostgreSQL such that `thread_id` and checkpoint read APIs continue to behave per LangGraph semantics.

#### Scenario: Postgres backend is selected with valid configuration

- **WHEN** checkpointing is enabled and the backend is `postgres` with required connection parameters present
- **THEN** the runtime SHALL initialize a Postgres-backed checkpointer without raising a “not bundled” configuration error

#### Scenario: Postgres backend is selected without connection parameters

- **WHEN** checkpointing is enabled and the backend is `postgres` but connection parameters are missing
- **THEN** the runtime SHALL fail fast with a clear configuration error before serving traffic

### Requirement: [DALC-REQ-POSTGRES-AGENT-PERSISTENCE-002] Durable application persistence for correlation and feedback

The system SHALL support persisting Slack (or equivalent) correlation mappings and human feedback events to PostgreSQL when configured, so that records survive process restarts and are queryable for operator and export workflows.

#### Scenario: Correlation write and read across restart

- **WHEN** a correlation record is written for `(channel_id, message_ts)` and the application process is replaced
- **THEN** a subsequent process using the same database configuration SHALL resolve the same correlation for a matching lookup key

#### Scenario: Human feedback event durability

- **WHEN** a `HumanFeedbackEvent` is recorded while Postgres persistence is enabled
- **THEN** the event SHALL be retrievable after restart with stable identifiers (`registry_id`, `schema_version`, `label_id`, `tool_call_id`, and `checkpoint_id` when present)

### Requirement: [DALC-REQ-POSTGRES-AGENT-PERSISTENCE-003] Internal trace summaries (non-vendor)

The system SHALL support writing tool-invocation summaries (including `tool_call_id`, timing, and outcome classification) to PostgreSQL when configured, without requiring Weights & Biases for basic operator inspection.

#### Scenario: Tool span summary stored

- **WHEN** a tool invocation completes and Postgres trace-summary persistence is enabled
- **THEN** a row or record SHALL exist that allows lookup by `run_id` and/or `tool_call_id` for latency and outcome

### Requirement: [DALC-REQ-POSTGRES-AGENT-PERSISTENCE-004] Schema versioning and migrations

The project SHALL ship versioned database schema artifacts (migrations) for all Postgres tables it owns, and SHALL document how operators apply them during upgrades.

#### Scenario: Fresh install

- **WHEN** an operator provisions an empty database and applies the documented migration sequence
- **THEN** all required tables and indexes for checkpoints (if owned by the app migration set) and application observability tables SHALL exist

### Requirement: [DALC-REQ-POSTGRES-AGENT-PERSISTENCE-005] Memory mode remains supported

When Postgres persistence is not configured, the runtime SHALL continue to support in-memory stores and/or MemorySaver checkpointing without requiring a database.

#### Scenario: Default deployment without Postgres URL

- **WHEN** observability store is `memory` (or unset) and checkpoint backend is `memory`
- **THEN** the application SHALL start successfully without database credentials
