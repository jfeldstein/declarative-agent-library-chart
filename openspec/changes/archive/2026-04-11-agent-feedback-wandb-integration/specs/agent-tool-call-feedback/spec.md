## ADDED Requirements

### Requirement: Checkpoints bind tool side effects to stable identifiers

The system SHALL create a **checkpoint** immediately before or after committing a user-visible side effect for a configured tool (for example posting a Slack message). Each checkpoint SHALL record at least: `checkpoint_id`, `run_id`, `tool_call_id`, `tool_name`, `external_ref` (channel-specific identifier such as Slack `channel` and `ts`), and timestamp.

#### Scenario: Slack message posted

- **WHEN** an agent tool successfully posts a message to Slack
- **THEN** the system SHALL persist a checkpoint linking that message’s `channel` and `ts` to `checkpoint_id`, `run_id`, and `tool_call_id`

### Requirement: Human feedback is correlated to checkpoints

The system SHALL accept human feedback signals labeled **positive**, **negative**, or **neutral** (or equivalent enums) and SHALL associate each signal with exactly one `checkpoint_id` when resolution succeeds.

#### Scenario: Positive reaction on a message

- **WHEN** a user adds a configured positive reaction (for example `:+1:`) to a message that was recorded in a checkpoint
- **THEN** the system SHALL store a positive feedback record bound to that checkpoint’s `checkpoint_id` and originating user identity per policy

#### Scenario: Negative reaction

- **WHEN** a user adds a configured negative reaction (for example `:-1:`) to such a message
- **THEN** the system SHALL store a negative feedback record bound to the same `checkpoint_id`

### Requirement: Unresolved feedback does not corrupt training labels

The system SHALL, when a reaction is received for a message with no matching checkpoint, record an orphan event for operations and SHALL NOT attach a training label to any run.

#### Scenario: Orphan reaction

- **WHEN** the reaction event references an unknown `external_ref`
- **THEN** the system SHALL log or queue the event for investigation and SHALL NOT emit a labeled feedback event for a `checkpoint_id`

### Requirement: Feedback updates are idempotent per policy

The system SHALL define idempotency rules (for example one active label per user per checkpoint or latest-wins). Duplicate deliveries of the same reaction SHALL NOT create duplicate conflicting primary labels without an explicit conflict-resolution policy.

#### Scenario: Duplicate event delivery

- **WHEN** the same reaction-added event is delivered twice
- **THEN** the persisted feedback state SHALL match the policy (no duplicate rows, or upserted single row) and SHALL remain consistent with the latest known Slack state after reconciliation
