## ADDED Requirements

### Requirement: Automatic checkpoint persistence

The agent runtime SHALL persist workflow state to a checkpointer after each completed task (or equivalent atomic step) for any registered agent workflow, without requiring workflow authors to manually invoke save APIs for each step.

#### Scenario: Task completes and state is persisted

- **WHEN** a task finishes successfully or with a handled error that is modeled as a persisted terminal state
- **THEN** a new checkpoint SHALL be written that includes outputs required to resume or inspect that step

#### Scenario: Ephemeral workflows opt out explicitly

- **WHEN** a workflow is declared with an explicit ephemeral execution flag approved by configuration
- **THEN** the runtime SHALL NOT persist checkpoints for that workflow invocation

### Requirement: Thread and checkpoint identification

The system SHALL assign a stable `thread_id` per logical conversation or run and SHALL record monotonic checkpoint history such that callers can retrieve the latest state or enumerate prior checkpoints for that thread.

#### Scenario: Resume after failure without redoing completed tasks

- **WHEN** a run fails mid-workflow and the same `thread_id` is invoked again with resume semantics
- **THEN** completed tasks whose results are present in the checkpoint SHALL NOT be re-executed unless configured otherwise

### Requirement: Inspection API aligned with LangGraph semantics

The runtime SHALL expose operations to read the latest checkpoint state and to list checkpoint history for a thread, analogous to LangGraph `get_state` and `get_state_history` behavior, including optional `checkpoint_id` targeting when supported by the store.

#### Scenario: Fetch latest state for a thread

- **WHEN** a client requests state for a valid `thread_id` with no `checkpoint_id`
- **THEN** the response SHALL represent the most recent persisted state for that thread

#### Scenario: List historical checkpoints

- **WHEN** a client requests checkpoint history for a valid `thread_id`
- **THEN** the system SHALL return an ordered sequence of checkpoint snapshots with metadata sufficient to identify parent/child relationships

### Requirement: Checkpoints bind user-visible tool side effects

For configured tools that commit a user-visible external side effect (for example posting a Slack message), the system SHALL create a **checkpoint** immediately before or after committing that side effect (per deployment policy). The checkpoint record SHALL include at least: `checkpoint_id`, `run_id`, `tool_call_id`, `tool_name`, `external_ref` (channel-specific identifier such as Slack `channel` and `ts`), and timestamp. When W&B tracing is enabled for the run, the checkpoint metadata SHALL also include the W&B linkage fields required by `wandb-agent-traces` so feedback can target the correct trace record.

#### Scenario: Slack message posted

- **WHEN** an agent tool successfully posts a message to Slack
- **THEN** the system SHALL persist a checkpoint linking that message’s channel identifier and `ts` to `checkpoint_id`, `run_id`, and `tool_call_id`
