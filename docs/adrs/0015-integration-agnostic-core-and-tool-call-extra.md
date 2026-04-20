# ADR 0015: Integration-agnostic observability core and tool-result `extra`

## Status

Accepted

## Context

Several concerns were crossing layers without a crisp rule:

1. **Integration leakage** — Core middleware (and “shared” Prometheus subscribers) carried Slack-specific field names such as `slack_web_api_method`, inferred from MCP tool ids. That couples the platform lifecycle contract to Slack naming and duplicates knowledge that belongs in Slack tools.

2. **Plugin neutrality** — Optional observability plugins ([ADR 0014](0014-observability-plugin-architecture.md)) must not embed every integration’s vocabulary in shared code paths; otherwise each new bridge forces edits to unrelated subscribers.

3. **Where integrations live** — Triggers (`POST /api/v1/trigger`, Slack/Jira inbound bridges), **scrapers**, and **tools** may be integration-specific. The **runtime core** (trigger pipeline glue, middleware publishers, generic metrics subscribers, shared lifecycle types) **SHALL NOT** encode Slack/Jira/Google-specific semantics.

## Decision

1. **`invoke_tool` result `extra`** — Tool handlers **MAY** return a dict that includes optional top-level key **`extra`**: a JSON-serializable mapping of **opaque** integration metadata. **`run_tool_json`** copies this into **`publish_tool_call_completed`** / **`publish_tool_call_failed`** under the lifecycle payload key **`extra`**, and **SHALL** strip `extra` from the JSON body returned to HTTP/API callers so instrumentation metadata is not part of the agent tool contract surface.

2. **Namespacing** — Integration-specific keys inside **`extra`** **SHALL** live under a short integration key (e.g. **`extra["slack"]`**, **`extra["jira"]`**) so shared code and plugins can route without flat Slack-prefixed names at the top level.

3. **Slack Web API metrics** — Slack tools **SHALL** attach **`extra["slack"]["web_api_method"]`** (Slack Web API method string) via **`agent.tools.slack.support.with_slack_tool_extra`**. Recording **`dalc_slack_tool_*`** series **SHALL** happen only in **`register_slack_tool_metrics_plugin`**, which subscribes to the same generic **`tool.call.*`** events and reads **`payload["extra"]`**. The core **`register_prometheus_agent_plugin`** **SHALL** record only **`dalc_tool_*`** from **`observe_mcp_tool`** (tool id + result + latency).

4. **Plugins** — Shared observability plugins **SHALL** remain **integration-agnostic**: they subscribe to generic **`EventName`** values and generic payload shapes. Integration-specific **optional** subscribers (same bus, extra module) **MAY** interpret namespaced **`extra`** for their metrics or sinks. Enabling **`observability.plugins.prometheus`** continues to register both the generic Prometheus agent plugin and the Slack tool metrics subscriber so existing **`dalc_slack_*`** behavior is preserved without polluting core subscribers.

## Consequences

**Positive:**

- Clear boundary: tools (and triggers/scrapers) own integration vocabulary; core publishes opaque **`extra`**.
- New integrations can add namespaced **`extra`** and optional plugins without editing middleware maps.
- Prometheus “core” subscriber stays small and stable.

**Negative / trade-offs:**

- Tool authors must attach **`extra`** consistently if they want integration-specific metrics; otherwise only **`dalc_tool_*`** is recorded.
- Two subscriber modules run for Slack Web API metrics when Prometheus is enabled (acceptable; both are thin).

## Related

- [ADR 0014 — Observability plugin architecture](0014-observability-plugin-architecture.md)
- [ADR 0011 — Prometheus metrics schema and cardinality](0011-prometheus-metrics-schema-and-cardinality.md)
