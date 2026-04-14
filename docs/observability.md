<!-- Traceability: [CFHA-REQ-O11Y-LOGS-004] -->

# Observability (CFHA runtime)

<!-- Traceability: [CFHA-REQ-O11Y-LOGS-004] -->

## Checkpoints, W&B traces, and Slack correlation (OpenSpec)

This section aligns with **`openspec/changes/agent-checkpointing-wandb-feedback`** (`runtime-langgraph-checkpoints`, `wandb-agent-traces`, `tool-feedback-slack`). Deep dive: **[checkpointing-and-traces.md](checkpointing-and-traces.md)** and **[runbooks/checkpoints-wandb.md](runbooks/checkpoints-wandb.md)**.

- **Checkpointer** — The **ordered step history** for a run lives in the **LangGraph-aligned checkpointer** (per-thread checkpoints). It is the **source of truth** for resume and for binding feedback to steps.
- **Weights & Biases** — When enabled, the runtime **initializes a W&B run** per trigger invocation and records **config/tags** from bounded env-derived fields; full span-level LLM tracing can extend the same module. **Do not** put unbounded text (full prompts, Slack bodies, per-message ids) on **W&B tags**; keep tags **low cardinality** and put rich content in **spans** / trace payloads (with redaction).
- **Slack** — Slack messages **cannot** carry hidden correlation metadata. The host keeps a **durable server-side map** (implementation in progress): **`(slack_channel_id, message_ts)` → `tool_call_id`, `checkpoint_id`, `run_id`, `thread_id`, W&B run/span identifiers** so reactions can resolve **message → tool call → checkpoint → W&B** for storage + trace updates.

### Environment

| Variable | Purpose |
| -------- | ------- |
| `HOSTED_AGENT_CHECKPOINT_STORE` | `memory` when unset (**default-on** in-process store), `none` to disable persistence, or reserved `postgres` / `redis` (not implemented). |
| `HOSTED_AGENT_WANDB_ENABLED` | `1` / `true` / `yes` / `on` = **intent** to trace to W&B. |
| `WANDB_API_KEY` | Standard W&B credential (mount via Secret). |
| `WANDB_PROJECT` or `HOSTED_AGENT_WANDB_PROJECT` | W&B project name. |
| `WANDB_ENTITY` | Optional team/entity. |
| `HOSTED_AGENT_SLACK_FEEDBACK_ENABLED` | Reserved flag for Slack reaction ingestion (off until wired). |

**`GET /api/v1/runtime/summary`** → **`observability`**: `checkpoint_store`, **`feature_flags`** (`checkpoints_enabled`, `slack_feedback_enabled`), **`wandb.tracing_ready`**, and **`wandb.mandatory_run_tag_keys`**.

**Thread APIs** (when `HOSTED_AGENT_CHECKPOINT_STORE` ≠ `none`):

- **`GET /api/v1/trigger/threads/{thread_id}/state`**
- **`GET /api/v1/trigger/threads/{thread_id}/checkpoints`**

**`POST /api/v1/trigger`** accepts **`thread_id`** and **`ephemeral`** (skip checkpointer for that call).

### Mandatory W&B run tags (implementation target)

| Tag | Notes |
| --- | ----- |
| `agent_id` | Omit if unknown; never use free text blobs as tag *values*. |
| `environment` | e.g. `prod` / `staging`. |
| `skill_id` | From config, bounded. |
| `skill_version` | From config, bounded. |
| `model_id` | From config, bounded. |
| `prompt_hash` | Hash or sentinel, not raw prompt text. |
| `thread_id` | Stable conversation/run id. |

**Shadow**-related W&B tags (`rollout_arm`, `shadow_variant_id`) may appear when runtime shadow configuration is enabled; there is **no** separate OpenSpec change documenting shadow behavior in this repo.

## Metrics (Prometheus)

The agent HTTP server exposes `**GET /metrics**` on the same port as the API (default **8088**), in Prometheus text format.

### Environment

#### `HOSTED_AGENT_LOG_FORMAT`

Controls how the Python runtime prints **application** log lines (structlog) to **stdout**:

- `**console`** (default when unset): human-readable lines for local development.
- `**json`**: one **JSON object per line** (often called “JSON logging”). Each line includes at least `level`, `message`, `service`, and `request_id` when the HTTP middleware ran. That shape is easy for **Fluent Bit**, **Promtail**, **Vector**, or an OpenTelemetry collector to parse and ship to Loki or similar.

This is separate from Uvicorn’s own access logs; it applies to the structured events we emit (e.g. `http_request_start` / `http_request_end`).


| Variable                  | Values                      | Purpose    |
| ------------------------- | --------------------------- | ---------- |
| `HOSTED_AGENT_LOG_FORMAT` | `console` (default), `json` | See above. |


Helm: set `o11y.structuredLogs.json: true` under the `declarative-agent-library` subchart to inject `HOSTED_AGENT_LOG_FORMAT=json`.

### Metric names (agent process)


| Metric                                        | Labels                       | Description                        |
| --------------------------------------------- | ---------------------------- | ---------------------------------- |
| `agent_runtime_http_trigger_requests_total`   | `result` = `success`         | `client_error`                     |
| `agent_runtime_http_trigger_duration_seconds` | `result`                     | Histogram of trigger handling time |
| `agent_runtime_mcp_tool_calls_total`          | `tool`, `result` = `success` | `error`                            |
| `agent_runtime_mcp_tool_duration_seconds`     | `tool`, `result`             | Tool call latency                  |
| `agent_runtime_subagent_invocations_total`    | `subagent`, `result`         | Subagent delegations               |
| `agent_runtime_subagent_duration_seconds`     | `subagent`, `result`         | Subagent latency                   |
| `agent_runtime_skill_loads_total`             | `skill`, `result`            | Skill load operations              |
| `agent_runtime_skill_load_duration_seconds`   | `skill`, `result`            | Skill load latency                 |


`tool`, `subagent`, and `skill` label values come from **configuration** only (bounded), not user-supplied free text.

### Kubernetes scrape discovery (Helm)

Under `declarative-agent-library.o11y`:

- `**prometheusAnnotations.enabled`**: adds `prometheus.io/scrape`, `prometheus.io/port`, `prometheus.io/path` to the agent **Pod** and **Service** (for scrapers that honor these annotations).
- `**serviceMonitor.enabled`**: renders a `**monitoring.coreos.com/v1` `ServiceMonitor`** selecting the agent `Service` on port `**http**`, path `**/metrics**`. Requires the **Prometheus Operator** CRDs in the cluster.

When the chart deploys the **managed RAG** workload (at least one `**scrapers.jobs`** entry with `**enabled: true`**):

- `**o11y.prometheusAnnotations.enabled**`: the **same** annotation triad as the agent is applied to the **RAG** Pod and **RAG** Service (port from `**scrapers.ragService.service.port`**, default **8090**). There is no separate RAG-only scrape flag.
- `**o11y.serviceMonitor.enabled`**: also renders a second `**ServiceMonitor`** (`metadata.name` suffix `**-rag**`) selecting the RAG Service, path `**/metrics**`, same interval / timeout / `**extraLabels**` as the agent monitor so Prometheus Operator selectors (e.g. `release: prometheus`) pick up **both** targets.

Worked example chart: `**examples/with-observability/`** (enables an enabled scraper job so **RAG** is present, **agent + RAG** annotations, and **two** `ServiceMonitor` resources when the Operator is present).

## Logs (Loki / ELK / etc.)

With `**HOSTED_AGENT_LOG_FORMAT=json`**, stdout lines are JSON objects suitable for **Fluent Bit**, **Promtail**, **Vector**, or the OpenTelemetry Collector (file/stdout receiver).

Recommended pipeline labels:

- `**service`** from the `service` field (constant `config-first-hosted-agents`).
- `**level`** from the `level` field.
- `**request_id**` from the `request_id` field when present.

Clients may send `**X-Request-Id**`; the server echoes it on responses and includes it in structured logs for the request. Outbound HTTP from the agent to RAG (`**rag**` specialist tool execution inside `**POST /api/v1/trigger**` and `**POST /api/v1/rag/query**`) sends the same `**X-Request-Id**` on the upstream request.

## Dashboards

Import `**grafana/cfha-agent-overview.json**` (see `**grafana/README.md**`) for agent trigger rate / p95 latency and **RAG** embed + query rate panels (requires both scrape targets in Prometheus).

### Metric names (RAG workload)

The **RAG** HTTP server (separate Deployment when an enabled scraper job exists; port **8090** by default via `**scrapers.ragService.service.port`**) exposes `**GET /metrics`** with:


| Metric                                     | Labels               | Description              |
| ------------------------------------------ | -------------------- | ------------------------ |
| `agent_runtime_rag_embed_requests_total`   | `result` = `success` | `client_error`           |
| `agent_runtime_rag_embed_duration_seconds` | `result`             | Latency for those routes |
| `agent_runtime_rag_query_requests_total`   | `result`             | `POST /v1/query`         |
| `agent_runtime_rag_query_duration_seconds` | `result`             | Query latency            |


Helm: set `**o11y.prometheusAnnotations.enabled: true**` under `declarative-agent-library` to add `prometheus.io/*` hints on **both** agent and RAG Service/Pod when RAG is deployed (RAG port from `**scrapers.ragService.service.port`**).

### Subagent roles (agent process)

Configured subagents are **tools** on the root agent ([LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)). They run when the supervisor invokes them during `**POST /api/v1/trigger`** (after a `**message`** turn), or when exercising them via unit tests with a scripted model.

- `**metrics**`: tool body returns the agent process **Prometheus snapshot** (same registry as `GET /metrics`). `**role: metrics`** is omitted from the default tool list unless `**exposeAsTool: true`** is set on that entry.
- `**rag**`: tool arguments carry `**query**` and optional RAG fields; execution proxies to managed RAG `**/v1/query**`. Requires `HOSTED_AGENT_RAG_BASE_URL` and a separate scrape target for `**agent_runtime_rag_***` on the RAG pod.

`**agent_runtime_subagent_***`, `**agent_runtime_skill_***`, and `**agent_runtime_mcp_tool_***` increment when those tools or the legacy direct `**tool**` / `**load_skill**` paths run through the trigger pipeline.

### Metric names (scraper CronJob pods)

Every enabled scraper container listens on **`SCRAPER_METRICS_ADDR`** (Helm sets **`0.0.0.0:9091`**) and exposes **`GET /metrics`** using a **scraper-only** Prometheus registry, so this endpoint does **not** include agent or RAG `agent_runtime_*` series from other workloads. After the job’s main work finishes, the process waits **`SCRAPER_METRICS_GRACE_SECONDS`** (default **35** in the chart) so Prometheus can scrape the Job pod before exit.

- **Reference** job (`hosted_agents.scrapers.reference_job`): posts to RAG **`/v1/embed`** and increments **`agent_runtime_scraper_rag_submissions_total`** per attempt.
- **Stub** job (`hosted_agents.scrapers.stub_job`): placeholder integration; prints to stdout and records **`agent_runtime_scraper_runs_total`** / duration only (no RAG submissions).

| Metric | Labels | Description |
|--------|--------|-------------|
| `agent_runtime_scraper_runs_total` | `integration`, `result` = `success` \| `error` | One completion per CronJob run |
| `agent_runtime_scraper_run_duration_seconds` | `integration` | Wall time for the job |
| `agent_runtime_scraper_rag_submissions_total` | `integration`, `result` = `success` \| `client_error` \| `server_error` | RAG **`/v1/embed`** attempts (reference job) |

**`SCRAPER_INTEGRATION`** sets the Prometheus label **`integration`**: it names the **integration type** for metrics (a bounded, operator-controlled value such as **`reference`**, **`slack`**, or **`jira`**), not an instance id. If unset, the **reference** job defaults to **`reference`**; the **stub** job defaults to **`SCRAPER_NAME`** (the job’s configured `name` in values) or **`stub`**. Use **`SCRAPER_INTEGRATION`** when the Helm job name should differ from the metric type (e.g. job `ingest-prod` but type **`slack`**).

**`SCRAPER_METRICS_ADDR`** accepts **`host:port`** or IPv6 **`[addr]:port`** (for example **`[::]:9091`**).

When **`o11y.prometheusAnnotations.enabled`** is true, the chart adds **`prometheus.io/*`** annotations on **all** scraper Job pods (port **9091**, path **`/metrics`**).

## Integration test (kind + Prometheus)

End-to-end check that `**examples/with-observability`** deploys to **kind** (agent **+** RAG), **Prometheus** (community Helm chart) scrapes **both** Services, and PromQL sees:

- `**agent_runtime_http_trigger_requests_total`** after several `POST /api/v1/trigger` calls, and  
- `**agent_runtime_rag_embed_requests_total`** / `**agent_runtime_rag_query_requests_total**` after `POST /v1/embed` and `POST /v1/query` on RAG.
- **Script:** `[runtime/tests/scripts/integration_kind_o11y_prometheus.sh](../runtime/tests/scripts/integration_kind_o11y_prometheus.sh)` — installs Prometheus with **two** static scrape jobs (`cfha-agent-metrics`, `cfha-rag-metrics`); disables **ServiceMonitor** on the release (`--set declarative-agent-library.o11y.serviceMonitor.enabled=false`) so **Prometheus Operator CRDs** are not required.
- **Prometheus values template:** `[runtime/tests/scripts/prometheus-kind-o11y-values.yaml](../runtime/tests/scripts/prometheus-kind-o11y-values.yaml)` — placeholders `**@SCRAPE_TARGET_AGENT@`** (`…declarative-agent-library…:8088`) and `**@SCRAPE_TARGET_RAG@`** (`…declarative-agent-library-rag…:8090`).
- **Pytest wrapper (opt-in):** `RUN_KIND_O11Y_INTEGRATION=1 pytest tests/integration/test_kind_o11y_prometheus.py -v --no-cov` from `runtime/` (avoids coverage floor when only this test runs).

**Prerequisites:** Docker, kind, kubectl, helm, curl, Python 3. Optional: `CLEANUP_KIND=1` to delete the cluster when the script exits; `SKIP_KIND_CREATE=1` to reuse an existing cluster name (`KIND_CLUSTER_NAME`, default `cfha-o11y-it`). Helm installs use `HELM_WAIT_TIMEOUT` (default **20m** for the example chart **`helm --wait`**) and `ROLLOUT_TIMEOUT` (default **600s**). For **`prometheus-community/prometheus`**, the integration script skips **`helm --wait`** (gRPC deadlines on GitHub Actions), **`kubectl patch`es** the server Deployment **`progressDeadlineSeconds`** to **`PROM_PROGRESS_DEADLINE_SEC`** (default **3600**; the chart default **600** is too tight for kind on CI), then runs **`kubectl rollout status`** with **`PROM_ROLLOUT_TIMEOUT`** (default **45m**). Values set **`imagePullPolicy: Never`** on the Prometheus server and config-reloader because images are pre-loaded into kind. The server image is **pinned to `quay.io/prometheus/prometheus:v2.55.1`** in **`prometheus-kind-o11y-values.yaml`** (chart **29.2.0** defaults to Prometheus **3.x**; **2.x** matches the integration script’s expectations). **`global.scrape_timeout`** must be **≤ `global.scrape_interval`** (values use **3s** / **2s**); the chart’s default global timeout is larger and makes Prometheus **refuse the config**. The integration script **pre-pulls** the matching preload list for **`PROM_CHART_VERSION` 29.2.0** and **loads images into the kind node** via **`docker cp` + `ctr -n k8s.io images import`** (same as the app image) so the cluster avoids slow quay pulls (see **`runtime/tests/scripts/integration_kind_o11y_prometheus.sh`**). If you bump **`PROM_CHART_VERSION`**, update the preload image list in that script and re-check the server tag override.