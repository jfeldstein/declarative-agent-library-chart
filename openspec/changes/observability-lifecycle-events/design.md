## Architecture

- **Tools** implement business logic only; they do not import `agent.observability.*`. Metrics for MCP tool calls and Slack Web API usage are recorded when `run_tool_json` publishes `tool.call.*` events (with optional `slack_web_api_method` derived from tool id).
- **Middleware** (`agent.observability.middleware`) is the only supported publisher for lifecycle events from HTTP triggers, LLM callbacks, RAG HTTP middleware, scrapers, subagents, and skill loads.
- **Legacy bridge** (`agent.observability.legacy_agent_metrics` / `legacy_scraper_metrics`) subscribes synchronously and calls existing `observe_*` functions so `agent_runtime_*` series are unchanged until Phase 2.

### Per-process buses

- **Agent pod:** `ensure_agent_observability()` registers legacy subscribers on the agent singleton bus (FastAPI `create_app`, RAG `create_app`).
- **Scraper CronJob:** `ensure_scraper_observability()` before `run_scraper_main` body; scraper RAG embed attempts and run duration use the scraper bus.

### Future: `dalc_*` metric schema (locked for parallel agents — Phase 2 implements)

Prometheus metric names **must not** embed tool/trigger/integration identifiers; those are **labels only**. Draft schema (normative mapping work lands with `dalc-plugin-prometheus-metrics`):

```python
from typing import Literal, TypedDict

class MetricDef(TypedDict):
    name: str
    type: Literal["counter", "histogram", "gauge"]
    labels: tuple[str, ...]
    help: str

# Illustrative subset — full tuple lists every `agent_runtime_*` → `dalc_*` rename.
DALC_METRICS_SCHEMA: tuple[MetricDef, ...] = (
    {
        "name": "dalc_tool_calls_total",
        "type": "counter",
        "labels": ("tool", "result"),
        "help": "Tool invocations (label-driven tool id).",
    },
    {
        "name": "dalc_trigger_requests_total",
        "type": "counter",
        "labels": ("trigger", "result"),
        "help": "Inbound trigger handling outcomes.",
    },
    # … LLM token, TTFT, scraper, RAG series per runtime-token-metrics / scraper specs
)
```

Legacy mapping examples for reviewers:

| Legacy | New (Phase 2) |
|--------|----------------|
| `agent_runtime_mcp_tool_calls_total` | `dalc_tool_calls_total` |
| `agent_runtime_http_trigger_requests_total` | `dalc_trigger_requests_total` (trigger=`http`) |
| `agent_runtime_slack_trigger_inbound_total` | `dalc_trigger_requests_total` (trigger=`slack`) |
| `agent_runtime_jira_trigger_inbound_total` | `dalc_trigger_requests_total` (trigger=`jira`) |

### Helm: `observability.plugins`

Single subtree shared by agent Deployment and scraper CronJobs; each process constructs its own bus + plugin instances from the same values tree (`plugins_config.py` stub reads defaults until env wiring lands).
