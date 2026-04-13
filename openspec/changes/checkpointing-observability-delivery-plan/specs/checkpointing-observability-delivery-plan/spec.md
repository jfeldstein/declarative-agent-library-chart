# Spec: Checkpointing observability delivery plan

### Requirement: Published delivery order

The repository SHALL maintain an ordered list of OpenSpec change directories (steps **1–13**) for checkpointing and runtime observability, with explicit dependencies, in `openspec/changes/checkpointing-observability-delivery-plan/design.md`.

#### Scenario: Contributor finds the next slice

- **WHEN** a contributor needs to know what to implement next
- **THEN** they SHALL be able to read the table in `design.md` and locate the corresponding change directory

### Requirement: No broad observability coverage omit

Runtime coverage configuration SHALL NOT exclude `hosted_agents/observability/` via a package-wide `omit` glob solely to satisfy `fail-under`.

#### Scenario: CI coverage measurement

- **WHEN** CI runs pytest with coverage for `hosted_agents`
- **THEN** modules under `src/hosted_agents/observability/` SHALL be measured the same as other first-party runtime modules
