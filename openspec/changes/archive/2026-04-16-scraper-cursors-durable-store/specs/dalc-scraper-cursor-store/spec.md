## ADDED Requirements

### Requirement: [DALC-REQ-SCRAPER-CURSOR-001] Scraper incremental state SHALL support a selectable persistence backend

The runtime SHALL support persisting scraper incremental state (for example Jira watermark timestamps and Slack channel `watermark_ts`) using a **configurable backend**. The default backend SHALL be **file**-based and remain compatible with existing `JIRA_WATERMARK_DIR` and `SLACK_STATE_DIR` behavior unless a different backend is explicitly selected.

#### Scenario: Default file backend unchanged

- **WHEN** no durable backend is configured (default)
- **THEN** the scraper SHALL read and write incremental state using the existing file-based paths documented for that scraper integration

#### Scenario: Postgres backend selected

- **WHEN** the operator configures the Postgres cursor backend for a scraper workload per documented Helm/env
- **THEN** the scraper SHALL read and write incremental state using the Postgres-backed implementation without requiring a writable ephemeral directory for that state

### Requirement: [DALC-REQ-SCRAPER-CURSOR-002] Postgres backend SHALL use a documented relational model and bounded keys

When the Postgres backend is enabled, the implementation SHALL persist state in a **documented** table (or tables) using a primary key composed of stable fields including **integration identifier**, **scraper scope**, and a **bounded key** derived from the logical cursor key (for example a hash when the raw key exceeds a documented maximum length). Writes SHALL be **upsert**-safe for a single scraper run.

#### Scenario: Upsert on repeated runs

- **WHEN** a scraper run completes and writes cursor state for a given `(integration, scope, key)`
- **THEN** a subsequent run SHALL observe the stored state such that incremental queries remain consistent with the documented overlap/watermark semantics for that integration

### Requirement: [DALC-REQ-SCRAPER-CURSOR-003] Helm SHALL wire Postgres URL to scraper workloads only when the durable backend is enabled

The Helm chart SHALL NOT inject Postgres credentials into scraper pods solely because the agent uses Postgres. When (and only when) the chart's documented **cursor store** settings select the Postgres backend, the chart SHALL set the scraper container environment to include a **non-empty** Postgres DSN sourced from the same documented precedence as other chart surfaces (shared `checkpoints.postgresUrl` / `HOSTED_AGENT_POSTGRES_URL`, with an optional scraper-specific override if documented).

#### Scenario: Agent Postgres without scraper cursor backend

- **WHEN** `checkpoints.postgresUrl` is set for the agent and the scraper cursor backend remains **file** (default)
- **THEN** the chart SHALL NOT require scraper CronJob pods to receive `HOSTED_AGENT_POSTGRES_URL` solely for cursor persistence

#### Scenario: Scraper Postgres cursor backend enabled

- **WHEN** the operator enables the Postgres cursor backend per documented values
- **THEN** rendered scraper CronJob pods SHALL include environment wiring that supplies the DSN to the runtime using the documented variable name(s)

### Requirement: [DALC-REQ-SCRAPER-CURSOR-004] Secrets SHALL NOT be embedded in scraper ConfigMap job JSON

Cursor backend connection parameters that contain credentials SHALL be delivered only via **Kubernetes Secret** references (for example `env` / `envFrom`) consistent with existing scraper auth patterns. The **ConfigMap** `job.json` SHALL remain non-secret.

#### Scenario: DSN from Secret

- **WHEN** Postgres is enabled for cursor storage and the DSN is provided via a Secret reference
- **THEN** the rendered manifests SHALL reference the Secret for the DSN value and SHALL NOT place the DSN literal into the scraper `job.json` ConfigMap
