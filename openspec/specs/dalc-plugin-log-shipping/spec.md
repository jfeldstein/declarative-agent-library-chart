## ADDED Requirements

### Requirement: [DALC-REQ-PLUGIN-LOG-SHIPPING-001] Log-shipping plugin enables JSON stdout logs via Helm

The Helm library chart SHALL set **`HOSTED_AGENT_LOG_FORMAT=json`** on the agent **`Deployment`** container when **`observability.plugins.logShipping.enabled`** is **`true`** OR **`observability.structuredLogs.json`** is **`true`** (logical inclusive **OR**). Both toggles SHALL produce the same runtime behavior for structured logging.

#### Scenario: Operator enables only the log-shipping plugin flag

- **WHEN** a chart consumer sets **`observability.plugins.logShipping.enabled`** to **`true`** and **`observability.structuredLogs.json`** is **`false`** or unset
- **THEN** the rendered agent **`Deployment`** SHALL include an environment entry **`HOSTED_AGENT_LOG_FORMAT`** with value **`json`**

#### Scenario: Structured logs flag still works alone

- **WHEN** **`observability.structuredLogs.json`** is **`true`** and **`observability.plugins.logShipping.enabled`** is **`false`**
- **THEN** the rendered agent **`Deployment`** SHALL include **`HOSTED_AGENT_LOG_FORMAT=json`**

### Requirement: [DALC-REQ-PLUGIN-LOG-SHIPPING-002] Values schema documents the log-shipping plugin

The chart **`values.schema.json`** SHALL define **`observability.plugins.logShipping`** with at least an **`enabled`** boolean property and SHALL describe that **`enabled`** drives **`HOSTED_AGENT_LOG_FORMAT=json`** consistent with **[DALC-REQ-PLUGIN-LOG-SHIPPING-001]**.

#### Scenario: Maintainer validates values against schema

- **WHEN** a maintainer inspects **`helm/chart/values.schema.json`** under **`observability.plugins.logShipping`**
- **THEN** they SHALL find **`enabled`** documented as controlling JSON stdout application logs for shipping

### Requirement: [DALC-REQ-PLUGIN-LOG-SHIPPING-003] Collector mapping examples for stdout JSON

Project documentation under **`docs/observability.md`** (or a successor path referenced from the observability docs index) SHALL include **illustrative** configuration fragments for mapping **stdout JSON** logs (fields at minimum **`level`**, **`message`**, **`service`**, and correlation **`request_id`** when present—aligned with **`dalc-agent-o11y-logs-dashboards`** **[DALC-REQ-O11Y-LOGS-001]** and **[DALC-REQ-O11Y-LOGS-002]**) into a log store using **Fluent Bit**, **Promtail**, and **Vector**, so operators can label or parse without reverse-engineering the runtime.

#### Scenario: Operator configures a Loki pipeline

- **WHEN** an operator follows the observability logging section to wire a collector
- **THEN** they SHALL find at least one example per named collector family (**Fluent Bit**, **Promtail**, **Vector**) showing how JSON keys become labels or structured metadata for downstream queries
