## ADDED Requirements

### Requirement: Mandatory run tags

Every agent run logged to Weights & Biases SHALL include the following tags when the values are known: `agent_id`, `environment`, `skill_id`, `skill_version`, `model_id`, `prompt_hash`, `rollout_arm`, and `thread_id`. Deployments MAY also emit equivalent aliases (`agent_name`, `agent_version`, `skill_set_version`, `rollout`) for compatibility with existing dashboards, provided the canonical keys above remain populated when known. Unknown values SHALL be omitted or explicitly set to a sentinel defined in configuration documentation.

#### Scenario: Primary run logged

- **WHEN** a primary (non-shadow) run completes or streams telemetry to W&B
- **THEN** the W&B run SHALL include `rollout_arm=primary` and all known tags from the mandatory set

#### Scenario: Shadow run logged

- **WHEN** a shadow rollout run emits telemetry to W&B
- **THEN** the W&B run SHALL include `rollout_arm=shadow` and the same mandatory tag keys as the primary where applicable

### Requirement: Tool calls as spans or structured steps

Each tool invocation during a run SHALL be represented in W&B as a child span, nested structure, or equivalent hierarchical log such that duration, inputs (redacted per policy), outputs (redacted per policy), and `tool_call_id` are queryable.

#### Scenario: Tool invoked during run

- **WHEN** the agent executes a tool with a stable `tool_call_id`
- **THEN** telemetry sent to W&B SHALL include that `tool_call_id` on the corresponding span or structured record

### Requirement: Human feedback on traces

When feedback (registry labels or configured scalar mappings) is recorded for a `tool_call_id` and, when known, `checkpoint_id`, the system SHALL push that signal to W&B in association with the same run and tool span (or an explicitly documented fallback such as a keyed `wandb.log` metric) within a bounded latency after ingestion. The update SHALL include at least `feedback_label` (or equivalent), `feedback_source`, and `checkpoint_id` when available.

#### Scenario: Negative feedback after Slack reaction

- **WHEN** feedback -1 is correlated to a `tool_call_id` that already has a W&B span
- **THEN** the system SHALL update W&B so the feedback is visible on the trace for that tool call or on the run with an unambiguous `tool_call_id` key

#### Scenario: Late reaction after run completion

- **WHEN** human feedback arrives after the main run span is closed
- **THEN** the system SHALL still record the feedback against the same wandb run identifier for that `run_id` (for example as a late event or metadata update) according to wandb API capabilities

### Requirement: Tag cardinality and sensitive values are controlled

The system SHALL NOT emit unbounded high-cardinality tags (for example raw message bodies) as wandb tags. Sensitive values SHALL be hashed or omitted per policy.

#### Scenario: High-cardinality field not a tag

- **WHEN** logging a run with long free-text content
- **THEN** that content SHALL appear only in redacted trace payloads or summaries, not as a wandb tag key or value that explodes cardinality
