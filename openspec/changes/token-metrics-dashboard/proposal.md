## Why

Operators cannot see **LLM token economics** or **streaming health** next to existing HTTP and tool metrics. **Time-to-first-token**, **generation throughput**, **token counts**, **request/response payload sizes**, and **estimated cost** belong in **Prometheus** (same scrape path as `agent_runtime_*`) and in a **Grafana** view so teams can tune models, catch regressions, and attribute spend per agent or route.

## What Changes

- Add **Prometheus metrics** (histograms/counters/gauges as appropriate) for: **time to first output token** (or first streamed chunk when token boundaries are unavailable), **output token throughput**, **input/output token counts**, **HTTP request and response body sizes** (bounded buckets; no raw content), and **estimated monetary cost** (configurable price table or env-derived rates; clearly labeled as **estimate**).
- Ensure metrics use **low-cardinality** labels (`agent_id`, `model_id`, `route` or equivalent bounded enums—never raw prompts or full URLs).
- Add or extend a **Grafana dashboard JSON** with panels for the above series, plus **`grafana/README.md`** import notes and datasource assumptions (aligned with **[CFHA-REQ-O11Y-LOGS-003]**).
- Wire instrumentation at the **trigger / LLM call** boundary where the runtime obtains token usage from LangChain/LangGraph callbacks or provider responses.
- **BREAKING**: None for HTTP APIs; metric **names** are additive unless a follow-on deprecates experimental series explicitly in `design.md`.

## Capabilities

### New Capabilities

- `cfha-runtime-token-metrics`: Normative **Prometheus** metric names, units, labels, and recording rules for token timing, counts, payload sizes, and cost **estimates** on the agent `/metrics` endpoint.

### Modified Capabilities

- `cfha-agent-o11y-logs-dashboards`: Extend dashboard obligations so the committed Grafana artifact set covers **token / cost / streaming latency** panels backed by `cfha-runtime-token-metrics` (delta spec under this change).

## Impact

- **`runtime/src/hosted_agents/`**: metrics module extensions, LLM/trigger instrumentation (callbacks or wrappers), optional config for pricing inputs.
- **`grafana/`**: new dashboard JSON or revision of `cfha-agent-overview.json` (per design).
- **`docs/observability.md`**: document new series names and cardinality rules.
- **Helm**: optional values for cost-estimation env (no secrets in values); chart defaults unchanged when unset.
- **CI**: pytest asserting metric registration and label bounds; Helm unchanged unless scrape annotations need notes.
