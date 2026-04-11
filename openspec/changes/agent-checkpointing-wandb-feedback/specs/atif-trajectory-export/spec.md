## ADDED Requirements

### Requirement: Canonical trajectory representation

The system SHALL maintain a canonical ordered trajectory for each run, consisting of user/model messages, tool calls, tool results, checkpoint references, and human feedback fields sufficient to render an ATIF-compatible export.

#### Scenario: Run with tool calls and feedback

- **WHEN** a run includes at least one tool call and later receives human feedback on that tool call
- **THEN** the canonical trajectory SHALL contain both the tool call record and the feedback annotation linked by `tool_call_id`

### Requirement: ATIF export

The system SHALL provide an exporter that converts the canonical trajectory for a run or batch of runs into ATIF-conformant documents according to a pinned ATIF schema version configured for the deployment. Exported documents SHALL include tool invocations with names, arguments, and results (subject to redaction) in ATIF-compatible structure when present in the canonical trajectory.

#### Scenario: Export batch for analysis

- **WHEN** an operator requests export for a time range and agent filter
- **THEN** the system SHALL emit ATIF documents that validate against the configured ATIF schema version

#### Scenario: Export includes tool calls

- **WHEN** an operator requests ATIF export for a `run_id` that contains tool calls
- **THEN** the exported document SHALL include those tool invocations with arguments and results (subject to redaction) in ATIF-compatible structure

### Requirement: Redaction is applied before export

The system SHALL apply a configurable **redaction** step to exports so that secrets, tokens, and disallowed PII categories do not appear in exported trajectories.

#### Scenario: Secret in tool args

- **WHEN** tool arguments contain a value classified as secret
- **THEN** the exported ATIF SHALL replace or remove that value according to redaction policy

### Requirement: Positive-feedback subset for training

The system SHALL support extracting subsequences or full trajectories that meet a positive-feedback criterion (e.g. all tool calls in window have +1 or no -1), for use in SFT or RLFT dataset builders. The system SHALL additionally support extraction of trajectory **segments** where human feedback for the segment’s **terminal checkpoint** (or terminal labeled step per configuration) is **positive**, with **segment boundaries**, **minimum length**, and **inclusion of shadow runs** defined by configuration.

#### Scenario: Build SFT dataset from +1-only windows

- **WHEN** a dataset builder requests trajectories where all labeled tool calls are +1
- **THEN** the exporter SHALL include only runs or segments satisfying that criterion

#### Scenario: Positive checkpoint selects segment

- **WHEN** a run has a checkpoint with positive feedback and extraction is configured to end at that checkpoint
- **THEN** the exporter SHALL emit a training example (or trajectory slice) containing the ordered steps from run start (or configured window) through that checkpoint

### Requirement: Negative labels excluded from default positive mining

The system SHALL, when default positive mining is enabled, exclude runs or segments whose terminal checkpoint has negative feedback from the positive mining output unless an explicit override configuration allows contrastive pairs.

#### Scenario: Negative feedback excluded

- **WHEN** the terminal checkpoint for a candidate segment has negative feedback
- **THEN** the default positive-mining job SHALL omit that segment from positive datasets

### Requirement: Provenance of labels in exports

When a trajectory includes both explicit human feedback (per `agent-feedback-model`) and operational run signals that may be mapped to derived training fields, the ATIF export or accompanying manifest SHALL distinguish **explicit human judgment** from **derived** or **operational** annotations so downstream training can filter by provenance.

#### Scenario: Export lists explicit feedback only

- **WHEN** a consumer requests an export mode that includes only explicit human feedback labels
- **THEN** the output SHALL omit derived-from-operational annotations unless the request explicitly opts in to include them
