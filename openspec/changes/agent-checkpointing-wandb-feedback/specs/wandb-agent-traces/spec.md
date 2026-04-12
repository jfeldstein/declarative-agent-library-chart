## ADDED Requirements

### Requirement: Mandatory run tags

Every agent run logged to Weights & Biases SHALL include the following **tags** when the values are known: `agent_id`, `environment`, `skill_id`, `skill_version`, `model_id`, `prompt_hash`, and `thread_id`. Deployments MAY also emit equivalent aliases (`agent_name`, `agent_version`, `skill_set_version`) for compatibility with existing dashboards, provided the canonical keys above remain populated when known. Unknown values SHALL be omitted or explicitly set to a sentinel defined in configuration documentation.

#### Scenario: Run logged with known context

- **WHEN** a run streams or completes telemetry to W&B and configured identifiers are available
- **THEN** the W&B run SHALL include all known tags from the mandatory set

### Requirement: Automatic tracing during execution

The system SHALL emit W&B traces (or equivalent hierarchical telemetry) **automatically** as LLM and tool work proceeds during a run, without requiring a separate export or batch step before traces exist.

#### Scenario: LLM call during run

- **WHEN** the agent invokes an LLM as part of a traced run
- **THEN** that invocation SHALL appear in W&B trace telemetry for that run according to the configured integration

### Requirement: Checkpoint linkage to W&B identifiers

For deployments with W&B tracing enabled, the system SHALL persist, alongside each checkpoint (or in a durable index keyed by `checkpoint_id`), the W&B identifiers required to **annotate** that step after the run (for example `wandb_run_id` and span or trace fragment ids as supported by the W&B SDK). This linkage SHALL support resolving **tool_call_id** and **checkpoint_id** to a concrete W&B target when applying late human feedback.

#### Scenario: Checkpoint written after tool step

- **WHEN** a checkpoint is persisted for a step that was traced to W&B
- **THEN** the persisted metadata SHALL include enough W&B addressing information to update or annotate that step’s trace record when feedback arrives later

### Requirement: Tool calls as spans or structured steps

Each tool invocation during a run SHALL be represented in W&B as a child span, nested structure, or equivalent hierarchical log such that duration, inputs (redacted per policy), outputs (redacted per policy), and `tool_call_id` are queryable.

#### Scenario: Tool invoked during run

- **WHEN** the agent executes a tool with a stable `tool_call_id`
- **THEN** telemetry sent to W&B SHALL include that `tool_call_id` on the corresponding span or structured record

### Requirement: Human feedback on traces

When explicit human feedback is recorded for a `tool_call_id` and, when known, `checkpoint_id`, the system SHALL push that signal to W&B in association with the same run and tool span (or an explicitly documented fallback such as keyed `wandb.log`) within a bounded latency after ingestion. The update SHALL include at least `feedback_label` (or equivalent), `feedback_source`, and `checkpoint_id` when available, using the **checkpoint → W&B** linkage persisted for that step.

#### Scenario: Negative feedback after Slack reaction

- **WHEN** negative feedback is correlated to a `tool_call_id` that has a persisted W&B linkage
- **THEN** the system SHALL update W&B so the feedback is visible on the trace for that tool call or on the run with an unambiguous `tool_call_id` key

#### Scenario: Late reaction after run completion

- **WHEN** human feedback arrives after the main run span is closed
- **THEN** the system SHALL still record the feedback in durable storage and apply the W&B update against the resolved run/span identifiers for that `run_id` according to W&B API capabilities

### Requirement: Tag cardinality and sensitive values are controlled

The system SHALL NOT emit unbounded high-cardinality tags (for example raw message bodies) as W&B tags. Sensitive values SHALL be hashed or omitted per policy.

#### Scenario: High-cardinality field not a tag

- **WHEN** logging a run with long free-text content
- **THEN** that content SHALL appear only in redacted trace payloads or summaries, not as a W&B tag key or value that explodes cardinality

### Requirement: Operator documentation and runtime stubs

The repository SHALL keep **`docs/observability.md`** aligned with this capability: **checkpointer** as the authoritative step record, **automatic W&B tracing** (when enabled), the **mandatory W&B tag keys**, **tag cardinality** rules (bounded tags vs trace payloads), the **server-side** Slack correlation chain (**Slack `channel` + `message_ts` → tool call → checkpoint → W&B**), and the **environment variables** that gate tracing and checkpoint store selection.

The Python package SHALL expose a small **stub module** (`hosted_agents.agent_tracing`) that reads those environment variables and surfaces a **non-secret** summary shape (for example via **`GET /api/v1/runtime/summary`**) so operators can verify configuration before the full LangGraph checkpointer and W&B SDK integration is wired. The stub SHALL NOT send telemetry to W&B until the integration tasks attach real `wandb` calls.

#### Scenario: Documentation lists tag keys and env vars

- **WHEN** an operator reads `docs/observability.md` for W&B and checkpoints
- **THEN** the document SHALL list the mandatory tag keys and SHALL document `HOSTED_AGENT_WANDB_ENABLED`, standard `WANDB_*` variables as referenced in that doc, and `HOSTED_AGENT_CHECKPOINT_STORE` (or equivalent) for the checkpointer backend knob

#### Scenario: Runtime summary reflects stub config

- **WHEN** `GET /api/v1/runtime/summary` is called
- **THEN** the JSON response SHALL include fields derived from `hosted_agents.agent_tracing` that report whether W&B tracing is **intended** (`HOSTED_AGENT_WANDB_ENABLED`) and the **checkpoint store kind** string, without exposing secret values
