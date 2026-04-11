## ADDED Requirements

### Requirement: Versioned label registry

The system SHALL maintain a versioned registry of human-judgment labels (identifiers, display names, and normalization rules such as emoji-to-scalar mappings). Stored feedback events SHALL reference `registry_id` and `schema_version` (or equivalent) so label meaning can be interpreted historically.

#### Scenario: Feedback stored with registry reference

- **WHEN** a human feedback event is persisted (e.g. from a Slack reaction mapped to +1 / -1)
- **THEN** the record SHALL include stable label identifiers and a registry version sufficient to resolve semantics at export time

### Requirement: Global-only labels

All human-judgment labels that are persisted as `HumanFeedbackEvent` (or equivalent) SHALL be defined in the **single global** versioned registry. The system SHALL NOT accept or persist agent-local or workspace-local label identifiers that are absent from that registry. New labels SHALL be introduced only by **registry version** change (and documented migration), not by per-agent configuration alone.

#### Scenario: Feedback uses only global label ids

- **WHEN** a channel (e.g. Slack) maps an incoming signal to a feedback label
- **THEN** the persisted event SHALL reference a `label_id` that exists in the deployed global registry for the recorded `schema_version`

#### Scenario: Attribution without per-agent taxonomy

- **WHEN** feedback is recorded for a run identified by `agent_id`
- **THEN** the event MAY include `agent_id` for slicing and analytics, but the **label meaning** SHALL be determined solely by the global registry, not by agent-specific label tables

### Requirement: Human feedback events are explicit

Human-intention signals (reactions, in-app ratings, reviewer labels) SHALL be stored as **human feedback** records distinct from operational telemetry. The system SHALL NOT classify operational lifecycle events (e.g. message deleted, prompt edited by user, session abandoned) as human feedback unless a separate, explicit opt-in mapper is applied in a downstream job.

#### Scenario: Operational event is not a feedback event

- **WHEN** the system records that a user deleted a bot message or rewrote their prompt before send
- **THEN** that observation SHALL be stored as an operational run signal (or span attribute), not as a `HumanFeedbackEvent`, unless configuration explicitly enables a labeled bridge product feature

### Requirement: Opt-in derivation from operational signals

Any training or analytics pipeline that converts operational run signals into reward-like or label-like fields SHALL use documented, opt-in mappers; default exports SHALL treat such derived fields separately from explicit human feedback in ATIF or dataset manifests.

#### Scenario: Dataset export distinguishes sources

- **WHEN** an ATIF or training export includes both explicit human feedback and derived labels from operational events
- **THEN** the export SHALL encode provenance so consumers can filter to explicit feedback only
