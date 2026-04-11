## ADDED Requirements

### Requirement: Runs can be exported as ATIF-compatible trajectories

The system SHALL provide an export path that transforms a completed or checkpointed **run** (ordered messages and tool spans with metadata) into **ATIF-compatible** JSON documents suitable for downstream training tooling.

#### Scenario: Export includes tool calls

- **WHEN** an operator requests ATIF export for a `run_id` that contains tool calls
- **THEN** the exported document SHALL include those tool invocations with arguments and results (subject to redaction) in ATIF-compatible structure

### Requirement: Redaction is applied before export

The system SHALL apply a configurable **redaction** step to exports so that secrets, tokens, and disallowed PII categories do not appear in exported trajectories.

#### Scenario: Secret in tool args

- **WHEN** tool arguments contain a value classified as secret
- **THEN** the exported ATIF SHALL replace or remove that value according to redaction policy

### Requirement: Positive-labeled subsequences can be extracted for SFT or RLFT

The system SHALL support extraction of trajectory **segments** where human feedback for the segment’s terminal checkpoint is **positive**, for use in **SFT** or **RLFT** pipelines. The extraction rules (segment boundaries, minimum length, inclusion of shadow runs) SHALL be configuration-defined.

#### Scenario: Positive checkpoint selects segment

- **WHEN** a run has a checkpoint with positive feedback and extraction is configured to end at that checkpoint
- **THEN** the exporter SHALL emit a training example (or trajectory slice) containing the ordered steps from run start (or configured window) through that checkpoint

### Requirement: Negative labels are excluded from default positive mining

The system SHALL, when default positive mining is enabled, exclude runs or segments whose terminal checkpoint has negative feedback from the positive mining output unless an explicit override configuration allows contrastive pairs.

#### Scenario: Negative feedback excluded

- **WHEN** the terminal checkpoint for a candidate segment has negative feedback
- **THEN** the default positive-mining job SHALL omit that segment from positive datasets
