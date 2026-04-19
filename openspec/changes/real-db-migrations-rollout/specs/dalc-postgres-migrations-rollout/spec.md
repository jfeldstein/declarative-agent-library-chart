## ADDED Requirements

### Requirement: [DALC-REQ-PG-MIG-ROLL-001] Chart exposes an optional migration Job for Postgres schema apply

The Helm library chart SHALL expose **values** that allow operators to render a **Kubernetes `Job`** (or equivalent batch workload) whose sole responsibility is to **apply** the repository’s bundled hosted-agents Postgres migration SQL to the target database **before** or **during** install/upgrade, using the **same** Postgres connection semantics as the agent runtime (`HOSTED_AGENT_POSTGRES_URL` or equivalent documented Secret wiring).

#### Scenario: Operator enables migration Job

- **WHEN** an operator enables the documented migration Job values and supplies a valid Postgres URL via the chart’s established Secret/values paths
- **THEN** `helm template` SHALL render a `Job` manifest that references migration SQL sources and database credentials **without** introducing a second undocumented DSN channel

### Requirement: [DALC-REQ-PG-MIG-ROLL-002] Migration Job failure blocks silent proceed semantics

When the migration Job is enabled, the chart documentation SHALL state that **failed migration apply** (non-zero Job exit or terminal failure state) MUST be resolved before the deployment is considered healthy; the chart SHALL NOT document “ignore hook failure” as the default operator path.

#### Scenario: Maintainer reads rollout semantics

- **WHEN** a maintainer reads the chart or runbook section for Postgres migrations rollout
- **THEN** they SHALL find explicit guidance that failed migration Jobs require investigation before relying on new agent replicas

### Requirement: [DALC-REQ-PG-MIG-ROLL-003] Idempotent apply posture is documented

The repository SHALL document that migration SQL is applied with an **idempotent** posture where practical (for example guarded DDL and transactional batches per file), and SHALL describe how operators detect partial apply vs full success (Job logs and Kubernetes events).

#### Scenario: Operator troubleshoots failed apply

- **WHEN** a migration Job fails in a cluster
- **THEN** documentation SHALL point operators to Job logs, common retry steps, and break-glass manual apply pointers without contradicting **[DALC-REQ-POSTGRES-AGENT-PERSISTENCE-004]** DDL ownership
