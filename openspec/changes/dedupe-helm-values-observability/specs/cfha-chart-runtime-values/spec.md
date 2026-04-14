## ADDED Requirements

### Requirement: [CFHA-REQ-CHART-RTV-001] Checkpoints values

The Helm library chart SHALL expose a top-level **`checkpoints`** object that includes at minimum:

- **`postgresUrl`**: optional string mapped to **`HOSTED_AGENT_POSTGRES_URL`** when non-empty.
- **`enabled`** and **`backend`**: control checkpoint store enablement and backend selection consistent with runtime documentation.

The chart SHALL NOT nest these fields under a key named **`observability`** (reserved for Prometheus/logs/scrape configuration).

#### Scenario: Postgres URL from values

- **WHEN** an operator sets **`checkpoints.postgresUrl`** to a non-empty DSN
- **THEN** rendered manifests SHALL expose that value to the agent container as **`HOSTED_AGENT_POSTGRES_URL`**

### Requirement: [CFHA-REQ-CHART-RTV-002] Weights & Biases values

The Helm library chart SHALL expose a top-level **`wandb`** object with **enabled**, **project**, and **entity** fields that map to the runtime’s documented **W&B** environment variables when enabled.

#### Scenario: W&B enabled from values

- **WHEN** an operator sets **`wandb.enabled`** to **true**
- **THEN** rendered manifests SHALL set **`HOSTED_AGENT_WANDB_ENABLED`** and SHALL pass **project** and **entity** when provided

### Requirement: [CFHA-REQ-CHART-RTV-003] Slack feedback under scrapers

The Helm library chart SHALL expose Slack feedback configuration under **`scrapers.slack.feedback`**, including at minimum **enabled** and an **emoji-to-label map** for reaction ingestion, rendered to the documented ConfigMap keys and environment variables.

Human-feedback **label taxonomy** data (the object that populates **`HOSTED_AGENT_LABEL_REGISTRY_JSON`** / `label-registry.json`) SHALL be configured under this **`scrapers.slack.feedback`** subtree (field name as implemented—e.g. **`labelRegistry`** or **`feedbackLabelRegistry`**) and SHALL be documented as the **feedback label registry**, not Kubernetes or Prometheus labels.

#### Scenario: Slack feedback enabled from values

- **WHEN** an operator sets **`scrapers.slack.feedback.enabled`** to **true**
- **THEN** rendered manifests SHALL enable **`HOSTED_AGENT_SLACK_FEEDBACK_ENABLED`** and SHALL mount or inline the emoji label map as documented

### Requirement: [CFHA-REQ-CHART-RTV-004] No ATIF export or shadow in chart contract

The Helm library chart SHALL NOT expose values keys for **ATIF trajectory export** or **shadow rollouts** (including sample rate, tenant allowlists, or variant JSON). Operators SHALL not rely on chart-rendered defaults for removed features.

#### Scenario: Chart values schema excludes removed features

- **WHEN** a maintainer inspects **`values.yaml`** and **`values.schema.json`** for the library chart
- **THEN** there SHALL be no **`atifExport`**, **`shadow`**, or equivalent keys under any path
