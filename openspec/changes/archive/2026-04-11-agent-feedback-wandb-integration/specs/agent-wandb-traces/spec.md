## ADDED Requirements

### Requirement: Agent runs are recorded to Weights & Biases with traces

The system SHALL integrate with **Weights & Biases (wandb)** so that each configured agent **run** produces a **wandb** run (or session object per deployment policy) and records **traces** or structured logs that include LLM and tool spans consistent with internal tracing.

#### Scenario: Tool span in wandb

- **WHEN** a tool executes during a wandb-enabled run
- **THEN** the system SHALL record a corresponding span or structured log entry identifiable by `tool_name` and `tool_call_id`

### Requirement: Required tags are present on wandb runs

Each wandb run (or top-level trace object) SHALL include the following **tags** when values are known: `env`, `agent_name`, `agent_version`, `skill_set_version`, `model_id`, and `rollout` with value `primary` or `shadow`.

#### Scenario: Primary run tags

- **WHEN** a primary (non-shadow) run is logged to wandb
- **THEN** the run SHALL include `rollout=primary` and the other required tags that are available from configuration and runtime context

### Requirement: Human feedback is pushed to wandb traces

- **WHEN** human feedback (positive, negative, or neutral) is correlated to a `checkpoint_id` for a run that was logged to wandb
- **THEN** the system SHALL append or update wandb trace data so that the feedback is queryable together with that run, including at least `feedback_label`, `feedback_source`, and `checkpoint_id`

#### Scenario: Late reaction after run completion

- **WHEN** feedback arrives after the main run span is closed
- **THEN** the system SHALL still record the feedback against the same wandb run identifier for that `run_id` (for example as a late event or metadata update) according to wandb API capabilities

### Requirement: Tag cardinality and sensitive values are controlled

The system SHALL NOT emit unbounded high-cardinality tags (for example raw message bodies) as wandb tags. Sensitive values SHALL be hashed or omitted per policy.

#### Scenario: High-cardinality field not a tag

- **WHEN** logging a run with long free-text content
- **THEN** that content SHALL appear only in redacted trace payloads or summaries, not as a wandb tag key or value that explodes cardinality
