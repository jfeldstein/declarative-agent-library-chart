# Observability (CFHA runtime)

## Metrics (Prometheus)

The agent HTTP server exposes **`GET /metrics`** on the same port as the API (default **8088**), in Prometheus text format.

### Environment

#### `HOSTED_AGENT_LOG_FORMAT`

Controls how the Python runtime prints **application** log lines (structlog) to **stdout**:

- **`console`** (default when unset): human-readable lines for local development.
- **`json`**: one **JSON object per line** (often called “JSON logging”). Each line includes at least `level`, `message`, `service`, and `request_id` when the HTTP middleware ran. That shape is easy for **Fluent Bit**, **Promtail**, **Vector**, or an OpenTelemetry collector to parse and ship to Loki or similar.

This is separate from Uvicorn’s own access logs; it applies to the structured events we emit (e.g. `http_request_start` / `http_request_end`).

| Variable | Values | Purpose |
|----------|--------|---------|
| `HOSTED_AGENT_LOG_FORMAT` | `console` (default), `json` | See above. |

Helm: set `o11y.structuredLogs.json: true` under the `declarative-agent-library` subchart to inject `HOSTED_AGENT_LOG_FORMAT=json`.

### Metric names (agent process)

| Metric | Labels | Description |
|--------|--------|-------------|
| `agent_runtime_http_trigger_requests_total` | `result` = `success` \| `client_error` \| `server_error` | `POST /api/v1/trigger` |
| `agent_runtime_http_trigger_duration_seconds` | `result` | Histogram of trigger handling time |
| `agent_runtime_mcp_tool_calls_total` | `tool`, `result` = `success` \| `error` | In-process tool invocations |
| `agent_runtime_mcp_tool_duration_seconds` | `tool`, `result` | Tool call latency |
| `agent_runtime_subagent_invocations_total` | `subagent`, `result` | Subagent delegations |
| `agent_runtime_subagent_duration_seconds` | `subagent`, `result` | Subagent latency |
| `agent_runtime_skill_loads_total` | `skill`, `result` | Skill load operations |
| `agent_runtime_skill_load_duration_seconds` | `skill`, `result` | Skill load latency |

`tool`, `subagent`, and `skill` label values come from **configuration** only (bounded), not user-supplied free text.

### Kubernetes scrape discovery (Helm)

Under `declarative-agent-library.o11y`:

- **`prometheusAnnotations.enabled`**: adds `prometheus.io/scrape`, `prometheus.io/port`, `prometheus.io/path` to the agent **Pod** and **Service** (for scrapers that honor these annotations).
- **`serviceMonitor.enabled`**: renders a **`monitoring.coreos.com/v1` `ServiceMonitor`** selecting the agent `Service` on port **`http`**, path **`/metrics`**. Requires the **Prometheus Operator** CRDs in the cluster.

When the chart deploys the **managed RAG** workload (at least one **`scrapers.jobs`** entry with **`enabled: true`**):

- **`o11y.prometheusAnnotations.enabled`**: the **same** annotation triad as the agent is applied to the **RAG** Pod and **RAG** Service (port from **`scrapers.ragService.service.port`**, default **8090**). There is no separate RAG-only scrape flag.
- **`o11y.serviceMonitor.enabled`**: also renders a second **`ServiceMonitor`** (`metadata.name` suffix **`-rag`**) selecting the RAG Service, path **`/metrics`**, same interval / timeout / **`extraLabels`** as the agent monitor so Prometheus Operator selectors (e.g. `release: prometheus`) pick up **both** targets.

Worked example chart: **`examples/with-observability/`** (enables an enabled scraper job so **RAG** is present, **agent + RAG** annotations, and **two** `ServiceMonitor` resources when the Operator is present).

## Logs (Loki / ELK / etc.)

With **`HOSTED_AGENT_LOG_FORMAT=json`**, stdout lines are JSON objects suitable for **Fluent Bit**, **Promtail**, **Vector**, or the OpenTelemetry Collector (file/stdout receiver).

Recommended pipeline labels:

- **`service`** from the `service` field (constant `config-first-hosted-agents`).
- **`level`** from the `level` field.
- **`request_id`** from the `request_id` field when present.

Clients may send **`X-Request-Id`**; the server echoes it on responses and includes it in structured logs for the request. Outbound HTTP from the agent to RAG (**`rag`** specialist tool execution inside **`POST /api/v1/trigger`** and **`POST /api/v1/rag/query`**) sends the same **`X-Request-Id`** on the upstream request.

## Dashboards

Import **`grafana/cfha-agent-overview.json`** (see **`grafana/README.md`**) for agent trigger rate / p95 latency and **RAG** embed + query rate panels (requires both scrape targets in Prometheus).

### Metric names (RAG workload)

The **RAG** HTTP server (separate Deployment when an enabled scraper job exists; port **8090** by default via **`scrapers.ragService.service.port`**) exposes **`GET /metrics`** with:

| Metric | Labels | Description |
|--------|--------|-------------|
| `agent_runtime_rag_embed_requests_total` | `result` = `success` \| `client_error` \| `server_error` | `POST /v1/embed` and `POST /v1/relate` |
| `agent_runtime_rag_embed_duration_seconds` | `result` | Latency for those routes |
| `agent_runtime_rag_query_requests_total` | `result` | `POST /v1/query` |
| `agent_runtime_rag_query_duration_seconds` | `result` | Query latency |

Helm: set **`o11y.prometheusAnnotations.enabled: true`** under `declarative-agent-library` to add `prometheus.io/*` hints on **both** agent and RAG Service/Pod when RAG is deployed (RAG port from **`scrapers.ragService.service.port`**).

### Subagent roles (agent process)

Configured subagents are **tools** on the root agent ([LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)). They run when the supervisor invokes them during **`POST /api/v1/trigger`** (after a **`message`** turn), or when exercising them via unit tests with a scripted model.

- **`metrics`**: tool body returns the agent process **Prometheus snapshot** (same registry as `GET /metrics`). **`role: metrics`** is omitted from the default tool list unless **`exposeAsTool: true`** is set on that entry.
- **`rag`**: tool arguments carry **`query`** and optional RAG fields; execution proxies to managed RAG **`/v1/query`**. Requires `HOSTED_AGENT_RAG_BASE_URL` and a separate scrape target for **`agent_runtime_rag_*`** on the RAG pod.

**`agent_runtime_subagent_*`**, **`agent_runtime_skill_*`**, and **`agent_runtime_mcp_tool_*`** increment when those tools or the legacy direct **`tool`** / **`load_skill`** paths run through the trigger pipeline.

### Metric names (reference scraper CronJob)

The **reference** scraper container listens on **`SCRAPER_METRICS_ADDR`** (Helm sets **`0.0.0.0:9091`**) and exposes **`GET /metrics`**. After a successful run it waits **`SCRAPER_METRICS_GRACE_SECONDS`** (default **35** in the chart) so Prometheus can scrape the Job pod before exit. Stub scraper jobs do not expose this endpoint.

| Metric | Labels | Description |
|--------|--------|-------------|
| `agent_runtime_scraper_runs_total` | `integration`, `result` = `success` \| `error` | One scrape per CronJob execution |
| `agent_runtime_scraper_run_duration_seconds` | `integration` | End-to-end wall time for the job |
| `agent_runtime_scraper_rag_submissions_total` | `integration`, `result` = `success` \| `client_error` \| `server_error` | Attempts to call RAG **`POST /v1/embed`** (same result mapping as RAG metrics) |

`integration` is a **bounded** type name (e.g. **`reference`**); use **`SCRAPER_INTEGRATION`** to override the default **`reference`**.

When **`o11y.prometheusAnnotations.enabled`** is true, the chart adds **`prometheus.io/*`** annotations on **reference** scraper Job pods (port **9091**, path **`/metrics`**) alongside agent and RAG targets.

## Integration test (kind + Prometheus)

End-to-end check that **`examples/with-observability`** deploys to **kind** (agent **+** RAG), **Prometheus** (community Helm chart) scrapes **both** Services, and PromQL sees:

- **`agent_runtime_http_trigger_requests_total`** after several `POST /api/v1/trigger` calls, and  
- **`agent_runtime_rag_embed_requests_total`** / **`agent_runtime_rag_query_requests_total`** after `POST /v1/embed` and `POST /v1/query` on RAG.

- **Script:** [`runtime/tests/scripts/integration_kind_o11y_prometheus.sh`](../runtime/tests/scripts/integration_kind_o11y_prometheus.sh) — installs Prometheus with **two** static scrape jobs (`cfha-agent-metrics`, `cfha-rag-metrics`); disables **ServiceMonitor** on the release (`--set declarative-agent-library.o11y.serviceMonitor.enabled=false`) so **Prometheus Operator CRDs** are not required.
- **Prometheus values template:** [`runtime/tests/scripts/prometheus-kind-o11y-values.yaml`](../runtime/tests/scripts/prometheus-kind-o11y-values.yaml) — placeholders **`@SCRAPE_TARGET_AGENT@`** (`…declarative-agent-library…:8088`) and **`@SCRAPE_TARGET_RAG@`** (`…declarative-agent-library-rag…:8090`).
- **Pytest wrapper (opt-in):** `RUN_KIND_O11Y_INTEGRATION=1 pytest tests/integration/test_kind_o11y_prometheus.py -v --no-cov` from `runtime/` (avoids coverage floor when only this test runs).

**Prerequisites:** Docker, kind, kubectl, helm, curl, Python 3. Optional: `CLEANUP_KIND=1` to delete the cluster when the script exits; `SKIP_KIND_CREATE=1` to reuse an existing cluster name (`KIND_CLUSTER_NAME`, default `cfha-o11y-it`). Helm installs use `HELM_WAIT_TIMEOUT` (default **15m**) and `ROLLOUT_TIMEOUT` (default **600s**) because Prometheus images can be slow to pull on a fresh kind node.
