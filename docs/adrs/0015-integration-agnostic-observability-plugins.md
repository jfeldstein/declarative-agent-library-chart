# ADR 0015: Integration-agnostic observability plugins

## Status

Accepted

## Context

Observability plugins (Prometheus, Langfuse, log shipping, and similar) sit **outside** integration-specific tool and trigger implementations. They consume **lifecycle events** and export data using each plugin’s own vocabulary (Prometheus metric families, OTel semantic conventions, and so on).

Duplicating metrics or event fields per integration (for example Slack Web API **method** names alongside generic tool ids) spreads integration concepts into shared plugin code and forces every new toolset to justify changes in unrelated layers.

Integration-specific contracts belong in:

- **Triggers** — inbound bridges (`*-trigger` routes, dispatch modules).
- **Scrapers** — scheduled ingestion jobs and their metrics registry.
- **Tools** — `agent.tools.<integration>` modules and entry-point registration.

The **core** runtime (middleware, plugins, generic dispatch) **SHALL** remain neutral: a tool call is a tool call; labels use **catalog tool ids** such as `{toolset}.{tool_name}` (for example `slack.post_message`), not vendor HTTP method strings or other redundant axes.

## Decision

1. **Plugins MUST NOT** define symbols, metric names, or helper functions whose names or docstrings imply a single vendor (for example no `observe_slack_*` or `DALC_SLACK_*` in the Prometheus plugin). **Inbound bridge triggers** share one code path keyed by the **`trigger`** label value (`http`, `slack`, `jira`, …), not separate “Slack vs Jira” exporter APIs in the plugin.

2. **Tool-call metrics** use a single pair of series with labels **`tool`** and **`result`**: counter **`dalc_tool_calls_total`** and histogram **`dalc_tool_calls_duration_seconds`**. The **`tool`** label **SHALL** be the stable registry id (`toolset.tool_name`). Duplicate series per vendor transport (for example Slack Web API method as its own metric family) **SHALL NOT** be emitted from shared plugins.

3. **Lifecycle publishers** in generic middleware **SHALL NOT** attach integration-only payload keys (for example vendor HTTP method maps) solely for metrics; subscribers derive dimensions from **`tool`** and other documented catalog fields.

4. **Relationship to ADR 0011** — Naming and cardinality rules in [ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md) still apply; this ADR narrows **where** integration-specific naming may appear (triggers, scrapers, tools) vs **plugins and shared observability**.

## Consequences

**Positive:**

- New integrations add tools and triggers without editing the Prometheus plugin for parallel metric families.
- Dashboards and alerts can aggregate **`dalc_tool_calls_total`** by **`tool`** prefix (`slack.*`, `jira.*`, …) without vendor-only series.

**Negative / trade-offs:**

- Operators who relied on **`dalc_slack_tool_web_api_*`** must switch PromQL to **`dalc_tool_calls_total{tool=~"slack\\..*"}`** (or by exact tool id).
- Histogram rename from **`dalc_tool_duration_seconds`** to **`dalc_tool_calls_duration_seconds`** is a breaking change for saved queries; release notes and Grafana updates should follow [ADR 0011](0011-prometheus-metrics-schema-and-cardinality.md) migration expectations.

## Related

- [ADR 0011: Prometheus metrics schema and cardinality](0011-prometheus-metrics-schema-and-cardinality.md)
- [ADR 0014: Observability plugin architecture](0014-observability-plugin-architecture.md)
