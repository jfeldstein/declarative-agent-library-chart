## ADDED Requirements

### Requirement: Tool-call correlation for external messages

When a tool posts a user-visible Slack message, the system SHALL associate that message with `tool_call_id`, `thread_id`, and `run_id` in a **durable server-side** mapping keyed by Slack `channel_id` and `message_ts`. The system SHALL NOT rely on hidden or unsupported metadata attached to the Slack message itself for correlation.

#### Scenario: Message posted from a tool call

- **WHEN** a tool execution results in a Slack message send
- **THEN** the system SHALL store a mapping from Slack `channel_id` and `message_ts` to `tool_call_id`, `checkpoint_id` when known, `run_id`, `thread_id`, and W&B identifiers needed for annotation per `wandb-agent-traces`

### Requirement: Reaction ingestion maps to registry labels

The system SHALL ingest Slack reaction events and SHALL normalize configured emoji into **global registry** labels per `agent-feedback-model`. Each resolved signal SHALL be attached to the correlated `tool_call_id` and, when available, the matching `checkpoint_id`.

#### Scenario: User adds thumbs-down reaction

- **WHEN** a user adds a configured negative reaction to a tracked Slack message
- **THEN** the system SHALL record negative feedback linked to the tool call that produced that message (and to `checkpoint_id` when resolution succeeds) and SHALL update W&B per persisted linkage

#### Scenario: User adds thumbs-up reaction

- **WHEN** a user adds a configured positive reaction to a tracked Slack message
- **THEN** the system SHALL record positive feedback linked to the tool call that produced that message (and to `checkpoint_id` when resolution succeeds) and SHALL update W&B per persisted linkage

### Requirement: Human feedback correlated to checkpoints

When a checkpoint exists for an external artifact, the system SHALL associate each successfully resolved human feedback signal with exactly one `checkpoint_id` in addition to `tool_call_id`, consistent with the global label registry.

#### Scenario: Positive reaction on a checkpointed message

- **WHEN** a user adds a configured positive reaction to a message that was recorded in a checkpoint mapping
- **THEN** the system SHALL store a positive feedback record bound to that checkpoint’s `checkpoint_id` and originating user identity per policy

### Requirement: Unresolved feedback does not claim false correlation

When a reaction is received for a message with no matching correlation record, the system SHALL record an **orphan** event for operations and SHALL NOT attach a resolved human feedback label to any `checkpoint_id` or `tool_call_id`.

#### Scenario: Orphan reaction

- **WHEN** the reaction event references an unknown `external_ref` (or unknown channel and `ts`)
- **THEN** the system SHALL log or queue the event for investigation and SHALL NOT emit a labeled human feedback record tied to a `checkpoint_id`

### Requirement: Idempotent feedback and Slack reconciliation

The system SHALL define idempotency rules (for example one active label per user per checkpoint or latest-wins). Duplicate deliveries of the same reaction SHALL NOT create duplicate conflicting primary labels without an explicit conflict-resolution policy. Where channel APIs allow, persisted feedback state SHOULD remain consistent with the latest known Slack reaction state after reconciliation (including reaction removed events mapped per policy).

#### Scenario: Duplicate webhook delivery

- **WHEN** the same reaction-added event is delivered twice with identical event identifiers
- **THEN** the persisted feedback state SHALL match the policy (no duplicate rows, or upserted single row) and SHALL remain consistent with the latest known Slack state after reconciliation
