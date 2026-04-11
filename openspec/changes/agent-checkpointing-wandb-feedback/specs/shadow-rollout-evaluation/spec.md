## ADDED Requirements

### Requirement: Shadow configuration

The system SHALL allow declaring shadow variants that differ by skill version, model id, and/or prompt hash while sharing the same high-level task input as the primary run, subject to safety policies. Shadow execution SHALL be labeled distinctly from primary in logs, ATIF exports, and W&B using `rollout_arm=shadow` and a `shadow_variant_id` (or equivalent) identifying the variant.

#### Scenario: Shadow variant declared

- **WHEN** shadow rollout is enabled for an agent with a configured variant
- **THEN** the system SHALL schedule a shadow evaluation tagged `rollout_arm=shadow` alongside or immediately after the primary run per deployment policy

#### Scenario: Shadow labeled in traces

- **WHEN** shadow mode is enabled for a variant **V** and a request is processed
- **THEN** shadow outputs and spans for **V** SHALL carry `rollout_arm=shadow` and `shadow_variant_id` identifying **V**

### Requirement: Default non-mutating shadow execution

By default, shadow runs SHALL NOT perform external side effects (e.g. posting to Slack, writing customer data) unless tools are explicitly allowlisted for shadow or a dangerous override flag is enabled.

#### Scenario: Shadow with disallowed side effect tool

- **WHEN** a shadow run reaches a tool that would mutate external state and the tool is not allowlisted for shadow
- **THEN** the system SHALL stub or skip the side effect while still recording planned arguments and simulated or empty results per policy

### Requirement: Comparable telemetry

Shadow and primary runs for the same input SHALL emit telemetry with identical mandatory tag keys (where applicable) so that downstream W&B queries and ATIF exports can compare them by `rollout_arm` and variant fields. The system SHALL log comparable signals for primary and shadow paths including, where available, **latency**, **token usage**, **tool selection**, and **outcome classification**.

#### Scenario: Compare primary and shadow in W&B

- **WHEN** both primary and shadow complete for the same correlated request id
- **THEN** both runs SHALL be queryable in W&B using shared tag keys including `thread_id` or a dedicated `request_correlation_id` tag

#### Scenario: Comparison metrics

- **WHEN** both primary and shadow complete for the same triggering request
- **THEN** metrics or trace fields SHALL be present that allow joining primary and shadow records (for example shared `request_id` or `correlation_id`)

### Requirement: Shadow is opt-in and bounded

Shadow execution SHALL be disabled by default and SHALL support limits (percentage of traffic, allowlisted tenants, or time windows) to control cost and risk.

#### Scenario: Disabled by default

- **WHEN** no shadow configuration is enabled for a deployment
- **THEN** the system SHALL execute only the primary path and SHALL NOT emit `rollout_arm=shadow` spans for that deployment
