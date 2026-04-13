## ADDED Requirements

### Requirement: Observability package included in coverage measurement

The project SHALL measure statement coverage for all Python modules under `hosted_agents/observability/` in the same `pytest-cov` run used for the rest of `hosted_agents`, without excluding the package via broad `omit` globs in `runtime/pyproject.toml`.

#### Scenario: CI coverage run includes observability

- **WHEN** continuous integration executes the configured pytest coverage command for the runtime
- **THEN** files under `src/hosted_agents/observability/` SHALL contribute to the coverage report totals

### Requirement: Global coverage threshold holds with observability included

The project SHALL satisfy the configured minimum total coverage (`fail-under`) for `hosted_agents` after observability modules are included in measurement, consistent with ADR 0002’s intent for first-party runtime code.

#### Scenario: Tests pass coverage gate

- **WHEN** the test suite completes with coverage enforcement enabled
- **THEN** the reported total coverage SHALL be greater than or equal to the configured `fail-under` percentage

### Requirement: External integrations are not required for unit coverage

Automated tests that exist solely to satisfy observability coverage SHALL NOT require network access to Weights & Biases, Slack, or Postgres; such behavior SHALL be exercised via mocks, stubs, or configuration that keeps calls in-process.

#### Scenario: W&B-off unit path

- **WHEN** tests run with Weights & Biases disabled or mocked
- **THEN** coverage of the W&B adapter module SHALL still be achievable without outbound network I/O
