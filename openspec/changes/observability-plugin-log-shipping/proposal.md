# Proposal: Observability plugin — log shipping (`dalc-plugin-log-shipping`)

## Problem

Operators need a single Helm subtree (`observability.plugins.*`) to express intent for optional integrations. The **`logShipping`** scaffold existed as a boolean stub without normative wiring to **`HOSTED_AGENT_LOG_FORMAT`** or collector-facing documentation scoped to stdout JSON shipping.

## Proposal

Promote **`dalc-plugin-log-shipping`**: Helm **`observability.plugins.logShipping.enabled`** OR **`observability.structuredLogs.json`** injects **`HOSTED_AGENT_LOG_FORMAT=json`**. Document Fluent Bit / Promtail / Vector mapping examples in **`docs/observability.md`**, aligned with **`dalc-agent-o11y-logs-dashboards`** structured-log field names for **[DALC-REQ-O11Y-LOGS-001]** / **[DALC-REQ-O11Y-LOGS-002]** where operators ship logs.

## Out of scope

Rendering Fluent Bit / Promtail / Vector as chart subcomponents (values-only contract + docs).
