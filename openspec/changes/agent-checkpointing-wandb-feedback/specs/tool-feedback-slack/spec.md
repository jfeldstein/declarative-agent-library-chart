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

### Requirement: Reaction add/remove and mutually exclusive polarity

The system SHALL ingest **two classes** of normalized reaction signals per message: **`reaction_added`** and **`reaction_removed`** (for example via `event_type` on the integration payload).

- **WHEN** a **`reaction_added`** event resolves to registry label **L** for user **U** on a correlated message  
  - **THEN** the system SHALL persist feedback for **L** under the **dedupe key** policy (`user_id`, `checkpoint_id`, `label_id`), and **SHALL** retract any persisted feedback for **U** on the same correlation for labels whose **scalar** is on the **opposite side of zero** from **L** (for example adding **positive** retracts **negative** for **U**, and vice versa).

- **WHEN** a **`reaction_removed`** event resolves to registry label **L** for **U**  
  - **THEN** the system SHALL **retract** the persisted feedback row for **U** + **L** for that correlation (same dedupe key as add), so the store reflects “no longer reacted with **L**”.

When **U** adds **L1** then adds **L2** where **L1** and **L2** are not mutually exclusive by scalar policy, **latest label wins** per dedupe policy (one row per `(user_id, checkpoint_id, label_id)`; distinct labels produce distinct rows unless retracted).

#### Scenario: Duplicate webhook delivery

- **WHEN** the same **reaction_added** event is delivered twice with identical dedupe semantics  
- **THEN** the persisted feedback state SHALL upsert (no duplicate rows for the same dedupe key)

#### Scenario: User removes an emoji

- **WHEN** **`reaction_removed`** is ingested for an emoji mapped to label **L**  
- **THEN** the persisted human-feedback row for that user + **L** + correlation SHALL be removed when present

#### Scenario: User switches thumbs up versus thumbs down

- **WHEN** the user previously recorded **positive** scalar feedback and subsequently adds **negative** scalar feedback (or the reverse), on the same correlated message  
- **THEN** the opposite polarity feedback for that user SHALL be retracted before recording the new label
