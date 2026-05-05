## ADDED Requirements

### Requirement: [DALC-REQ-CHART-RTV-001] Checkpoints values

The Helm library chart SHALL expose a top-level **`checkpoints`** object that includes at minimum:

- **`postgresUrl`**: optional string mapped to **`HOSTED_AGENT_POSTGRES_URL`** when non-empty.
- **`enabled`** and **`backend`**: control checkpoint store enablement and backend selection consistent with runtime documentation.

The chart SHALL NOT nest these fields under a key named **`observability`** (reserved for Prometheus/logs/scrape configuration).

#### Scenario: Postgres URL from values

- **WHEN** an operator sets **`checkpoints.postgresUrl`** to a non-empty DSN
- **THEN** rendered manifests SHALL expose that value to the agent container as **`HOSTED_AGENT_POSTGRES_URL`**

### Requirement: [DALC-REQ-CHART-RTV-002] Weights & Biases values

The Helm library chart SHALL expose **`observability.plugins.wandb`** with **enabled**, **project**, and **entity** fields that map to the runtime’s documented **W&B** environment variables when enabled (breaking migration from the earlier top-level **`wandb`** values key).

The agent runtime SHALL continue to accept legacy **`HOSTED_AGENT_WANDB_ENABLED`** as an alias when **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED`** is unset.

#### Scenario: W&B enabled from values

- **WHEN** an operator sets **`observability.plugins.wandb.enabled`** to **true**
- **THEN** rendered manifests SHALL set **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_WANDB_ENABLED`** and SHALL pass **project** and **entity** when provided

### Requirement: [DALC-REQ-CHART-RTV-003] Slack feedback under scrapers

The Helm library chart SHALL expose Slack feedback configuration under **`scrapers.slack.feedback`**, including at minimum **enabled** and an **emoji-to-label map** for reaction ingestion, rendered to the documented ConfigMap keys and environment variables.

Human-feedback **label taxonomy** data (the object that populates **`HOSTED_AGENT_LABEL_REGISTRY_JSON`** / `label-registry.json`) SHALL be configured under this **`scrapers.slack.feedback`** subtree as **`labelRegistry`** and SHALL be documented as the **feedback label registry**, not Kubernetes or Prometheus labels.

#### Scenario: Slack feedback enabled from values

- **WHEN** an operator sets **`scrapers.slack.feedback.enabled`** to **true**
- **THEN** rendered manifests SHALL enable **`HOSTED_AGENT_SLACK_FEEDBACK_ENABLED`** and SHALL mount or inline the emoji label map as documented

### Requirement: [DALC-REQ-CHART-RTV-004] No ATIF export or shadow in chart contract

The Helm library chart SHALL NOT expose values keys for **ATIF trajectory export** or **shadow rollouts** (including sample rate, tenant allowlists, or variant JSON). Operators SHALL not rely on chart-rendered defaults for removed features.

#### Scenario: Chart values schema excludes removed features

- **WHEN** a maintainer inspects **`values.yaml`** and **`values.schema.json`** for the library chart
- **THEN** there SHALL be no **`atifExport`**, **`shadow`**, or equivalent keys under any path

### Requirement: [DALC-REQ-CHART-RTV-005] Consumer observability plugins as entry-point name list

The Helm library chart SHALL expose **`observability.plugins.consumerPlugins`** as an **array of strings** (entry-point **names** registered under **`declarative_agent.observability_plugins`**).

When the array is **empty** (default), rendered manifests SHALL NOT inject **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS`** solely for consumer plugins.

#### Scenario: Non-empty list wires allowlist env

- **WHEN** **`observability.plugins.consumerPlugins`** lists one or more non-empty strings
- **THEN** rendered manifests for agent, scraper CronJobs, and managed RAG (when deployed) SHALL include **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS`** as a comma-separated list matching those names in order suitable for the runtime allowlist

#### Scenario: Defaults omit consumer plugin env

- **WHEN** an operator applies chart defaults (**`consumerPlugins: []`** or unset)
- **THEN** rendered manifests SHALL NOT add **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS`** for consumer plugins

### Requirement: [DALC-REQ-CHART-RTV-007] First-class LLM provider API key wiring

The Helm library chart SHALL expose a top-level **`chatModelApiKey`** object that wires a Kubernetes Secret into the correct provider env var for the configured **`chatModel`**, without requiring the operator to use `extraEnv`.

- **`secretName`** and **`secretKey`** (default `token`) reference the Kubernetes Secret containing the API key.
- When `secretName` is non-empty, the chart SHALL inject one env var into the agent container via `secretKeyRef`, with the env var name determined as follows:
  - `chatModel` prefix `openai/` or `openai:` or `gpt-` → **`OPENAI_API_KEY`**
  - `chatModel` prefix `anthropic/` or `anthropic:` or `claude-` → **`ANTHROPIC_API_KEY`**
  - Any other prefix → the chart SHALL fail manifest rendering unless **`chatModelApiKey.envVarName`** is explicitly set.
- **`envVarName`** SHALL override the auto-inferred name when set to a non-empty string.
- When `secretName` is empty, the chart SHALL NOT inject any provider API key env var from this field.

#### Scenario: OpenAI model infers OPENAI_API_KEY

- **WHEN** `chatModel: openai/gpt-4o-mini` and `chatModelApiKey.secretName` is non-empty
- **THEN** the agent Deployment SHALL contain an env var `OPENAI_API_KEY` sourced from `secretKeyRef`

#### Scenario: Anthropic model infers ANTHROPIC_API_KEY

- **WHEN** `chatModel: anthropic/claude-3-5-haiku-latest` and `chatModelApiKey.secretName` is non-empty
- **THEN** the agent Deployment SHALL contain `ANTHROPIC_API_KEY` from `secretKeyRef`

#### Scenario: Unknown provider without envVarName fails

- **WHEN** `chatModelApiKey.secretName` is non-empty and `chatModel` does not match a known prefix and `chatModelApiKey.envVarName` is empty
- **THEN** Helm rendering SHALL fail with an explicit error message

### Requirement: [DALC-REQ-CHART-RTV-006] Prompt files via values (supervisor + subagents)

The Helm library chart SHALL support externalizing long prompt text into **parent chart files** (resolved via Helm **`.Files.Get`**) for both:

- the supervisor / orchestrator prompt (top-level **`systemPromptFile`**), and
- subagent prompts (per-entry **`subagents[].systemPromptFile`** and **`subagents[].system_prompt_file`**).

For each scope independently, the chart SHALL enforce mutual exclusion:

- **Supervisor**: the chart SHALL fail manifest rendering when **both** **`systemPrompt`** and **`systemPromptFile`** are non-empty after trim.
- **Subagents**: for any subagent entry, the chart SHALL fail manifest rendering when any inline prompt key (**`systemPrompt`** or **`system_prompt`**) is non-empty after trim **and** any file reference key (**`systemPromptFile`** or **`system_prompt_file`**) is non-empty after trim.

The chart SHALL render resolved subagent prompt text into **`subagents.json`** without including any prompt file reference keys (no leakage of `systemPromptFile` / `system_prompt_file` into runtime JSON).

#### Scenario: Supervisor prompt from chart file

- **WHEN** an operator sets **`systemPromptFile`** to a parent chart file path and leaves **`systemPrompt`** empty
- **THEN** rendered manifests SHALL include the loaded prompt text in the supervisor prompt ConfigMap surface

#### Scenario: Conflicting supervisor prompt sources fail

- **WHEN** an operator sets both **`systemPrompt`** and **`systemPromptFile`** to non-empty values
- **THEN** Helm rendering SHALL fail

#### Scenario: Subagent prompt from chart file with path keys stripped

- **WHEN** an operator sets a subagent prompt via **`subagents[].systemPromptFile`** (or `system_prompt_file`) without inline prompt text
- **THEN** rendered manifests SHALL include the resolved prompt content in **`subagents.json`** and SHALL NOT include the file reference keys in that JSON
