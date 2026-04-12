## ADDED Requirements

### Requirement: Shadow variants can execute alongside primary

The system SHALL support **shadow** execution of alternate **prompts**, **skills**, or **models** for a subset of traffic when enabled by configuration. Shadow execution SHALL be labeled distinctly from primary in logs, ATIF exports, and wandb (`rollout=shadow`, `shadow_variant_id`).

#### Scenario: Shadow labeled in traces

- **WHEN** shadow mode is enabled for a variant **V** and a request is processed
- **THEN** shadow outputs and spans for **V** SHALL carry `rollout=shadow` and `shadow_variant_id` identifying **V**

### Requirement: Shadow must not duplicate unauthorized side effects

By default, shadow execution SHALL NOT perform **mutating** external tool calls (for example posting to Slack) unless explicitly allowed by policy. Mutations SHALL be stubbed, skipped, or redirected to sandbox resources per configuration.

#### Scenario: Slack post stubbed in shadow

- **WHEN** shadow execution reaches a tool that would post to Slack
- **THEN** the system SHALL NOT post a user-visible Slack message for the shadow path unless mutating shadow is explicitly enabled

### Requirement: Shadow data is usable for comparison

The system SHALL log comparable signals for primary and shadow paths (for example latency, token usage, tool selection, and outcome classification) so operators can compare variants in wandb or batch analytics.

#### Scenario: Comparison metrics

- **WHEN** both primary and shadow complete for the same triggering request
- **THEN** metrics or trace fields SHALL be present that allow joining primary and shadow records (for example shared `request_id` or `correlation_id`)

### Requirement: Shadow is opt-in and bounded

Shadow execution SHALL be disabled by default and SHALL support limits (percentage of traffic, allowlisted tenants, or time windows) to control cost and risk.

#### Scenario: Disabled by default

- **WHEN** no shadow configuration is enabled for a deployment
- **THEN** the system SHALL execute only the primary path and SHALL NOT emit `rollout=shadow` spans for that deployment
