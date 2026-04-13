## ADDED Requirements

### Requirement: Versioned label registry

The system SHALL maintain a versioned registry of **explicit human-judgment** labels (identifiers, display names, and normalization rules such as emoji-to-scalar mappings). Stored feedback events SHALL reference `registry_id` and `schema_version` (or equivalent) so label meaning can be interpreted historically.

#### Scenario: Feedback stored with registry reference

- **WHEN** explicit human feedback is persisted (e.g. from a Slack reaction mapped through the registry)
- **THEN** the record SHALL include stable label identifiers and a registry version sufficient to resolve semantics when the record is read

### Requirement: Global-only labels

All human-judgment labels persisted as explicit human feedback SHALL be defined in the **single global** versioned registry. The system SHALL NOT accept or persist agent-local or workspace-local label identifiers that are absent from that registry. New labels SHALL be introduced only by **registry version** change (and documented migration), not by per-agent configuration alone.

#### Scenario: Feedback uses only global label ids

- **WHEN** a channel (e.g. Slack) maps an incoming signal to a feedback label
- **THEN** the persisted event SHALL reference a `label_id` that exists in the deployed global registry for the recorded `schema_version`

#### Scenario: Attribution without per-agent taxonomy

- **WHEN** feedback is recorded for a run identified by `agent_id`
- **THEN** the event MAY include `agent_id` for slicing and analytics, but the **label meaning** SHALL be determined solely by the global registry, not by agent-specific label tables
