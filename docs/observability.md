<!-- Traceability: [DALC-REQ-O11Y-LOGS-004] -->

# Observability (DALC runtime)

<!-- Traceability: [DALC-REQ-O11Y-LOGS-004] -->

## Runtime architecture: lifecycle events and plugins (Phase 1)

**Phase 1** ships under OpenSpec change **`openspec/changes/observability-lifecycle-events/`** (chart/runtime alignment and follow-on OpenSpec promotion may track in parallel using branch prefix **`feature--observability-plugins-parallel*`** until a change directory is promoted). It introduces a **synchronous lifecycle event bus** (`SyncEventBus`, `EventName`) and **`agent.observability.middleware`** helpers so trigger handling, tools, LLM callbacks, RAG HTTP, scrapers, and Slack/Jira inbound paths emit **structured events**. Phase **2** registers optional plugins (Prometheus **`dalc_*`**, traces, dashboards) on that bus — see **`openspec/changes/observability-plugin-prometheus/`** and related plugin changes.

**Helm** declares **`agent.observability.plugins`** with **`enabled`** defaults for **`prometheus`**, **`langfuse`**, **`wandb`**, **`grafana`**, and **`logShipping`** (**`helm/chart/values.yaml`**). Several keys are already wired (Prometheus **`/metrics`**, W&B traces, Langfuse lifecycle export, structured JSON logs / log-shipping toggle, Grafana dashboard **`ConfigMap`**); exact env and template behavior is spelled out below and in **`docs/release-notes/`** when breaking.

Per-plugin summaries:

| Plugin key (`observability.plugins.<key>`) | Summary |
| --- | --- |
| **`prometheus`** | **`GET /metrics`** (**`dalc_*`**) when enabled — see [Metrics (Prometheus)](#metrics-prometheus). |
| **`langfuse`** | Lifecycle export via **`HOSTED_AGENT_LANGFUSE_*`** when **`observability.plugins.langfuse.enabled`** — details in middleware/plugin sections and chart values. |
| **`wandb`** | **`observability.plugins.wandb`** aligns with **`wandb.*`** / **`HOSTED_AGENT_WANDB_*`** — see **Checkpoints, W&B traces, and Slack correlation** below. |
| **`grafana`** | Optional **`ConfigMap`** (**`templates/_manifest_grafana_dashboards.tpl`**) packaging **`helm/chart/files/grafana/*.json`** when enabled (mirrors **`grafana/*.json`**); remote_write/stack automation is future work. |
| **`logShipping`** | **`HOSTED_AGENT_LOG_FORMAT=json`** when **`observability.plugins.logShipping.enabled`** or **`observability.structuredLogs.json`** — see **[DALC-REQ-PLUGIN-LOG-SHIPPING-001]** / structured logs sections. |
| **`consumerPlugins`** | Optional PEP 621 hooks under **`declarative_agent.observability_plugins`** (disabled by default). Enables **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_CONSUMER_ENABLED`** plus optional allowlist (**`HOSTED_AGENT_OBSERVABILITY_PLUGINS_ENTRY_POINTS`**), **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_STRICT`**, and opaque **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_CONSUMER_CONFIG_JSON`** — see **[DALC-REQ-CHART-RTV-005]** / **`dalc-custom-observability-plugins`**.

### Consumer observability plugins (extensions)

<!-- Traceability: [DALC-REQ-CUSTOM-O11Y-006] -->

Downstream images can ship additional Python distributions that register **`[project.entry-points."declarative_agent.observability_plugins"]`** objects (same packaging story as **`declarative_agent.tools`**). Hooks mirror the built-in **`enqueue`** / **`attach`** phases documented in **`agent.observability.bootstrap`**: **`enqueue(process_kind, cfg, enqueue_subscription)`** runs before **`SyncEventBus`** construction; **`attach(process_kind, cfg, bus)`** runs afterward. **`process_kind`** is **`agent`** or **`scraper`** (managed RAG uses **`ensure_agent_observability`**, so it follows **`agent`** semantics today).

Treat optional JSON config (**`consumerPlugins.configJson`** or **`configJsonSecret`**) like other bounded operator fields — avoid stuffing high-cardinality or sensitive payloads; follow **[ADR 0011 — Prometheus metrics schema and cardinality](adrs/0011-prometheus-metrics-schema-and-cardinality.md)** for labels emitted from hooks and **[ADR 0015 — Integration-agnostic observability plugins](adrs/0015-integration-agnostic-observability-plugins.md)** for metrics that belong in **`agent.observability.plugins.prometheus`**. Trace redaction references: Langfuse middleware docs (**`openspec/specs/dalc-plugin-langfuse-traces/`**).

**Non-goals:** Helm values SHALL NOT configure arbitrary **`importlib`** import paths for observability hooks — operators install wheels that declare PEP 621 entry points (audit-friendly, aligns with **[DALC-REQ-CUSTOM-O11Y-001]**).

Design record: **[ADR 0014 — Observability plugin architecture](adrs/0014-observability-plugin-architecture.md)** (terminology alongside **[ADR 0005](adrs/0005-observability-vs-execution-persistence.md)**, schema rules in **[ADR 0011](adrs/0011-prometheus-metrics-schema-and-cardinality.md)**).

## Checkpoints, W&B traces, and Slack correlation (OpenSpec)

This section covers **execution persistence**, correlation, and W&B tracing — see [ADR 0005](adrs/0005-observability-vs-execution-persistence.md) for how that differs from **Prometheus observability metrics** and optional **plugins**.

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
| `HOSTED_AGENT_SLACK_TOOLS_BOT_TOKEN` | Bot token (`xoxb-`) for **LLM-time** Slack Web API tools only; disjoint from CronJob **`SLACK_BOT_TOKEN`** / **`SLACK_USER_TOKEN`**. Usually from **`slackTools.botTokenSecretName`** (Helm). |
| `HOSTED_AGENT_SLACK_TOOLS_HISTORY_LIMIT` | Default cap (1–200) for `conversations.history` / `conversations.replies` tool calls. |
| `HOSTED_AGENT_SLACK_TOOLS_TIMEOUT_SECONDS` | HTTP timeout for Slack **`WebClient`** on the tools path (clamped in runtime). |

**`GET /api/v1/runtime/summary`** → **`observability`**: `checkpoint_store`, **`feature_flags`** (`checkpoints_enabled`, `slack_feedback_enabled`), **`wandb.tracing_ready`**, and **`wandb.mandatory_run_tag_keys`**.

### Helm value paths (library subchart)

- **`checkpoints.*`**: `postgresUrl` → `HOSTED_AGENT_POSTGRES_URL`; `enabled` / `backend` → LangGraph checkpoint env vars.
- **`wandb.*`**: maps to `HOSTED_AGENT_WANDB_ENABLED`, `WANDB_PROJECT`, and `WANDB_ENTITY` when enabled.
- **`scrapers.slack.feedback.*`**: `enabled` and `emojiLabelMap` configure reaction ingestion (`HOSTED_AGENT_SLACK_FEEDBACK_ENABLED`, `HOSTED_AGENT_SLACK_EMOJI_LABEL_MAP_JSON`). **`labelRegistry`** is the **human feedback label taxonomy** (ConfigMap `label-registry.json` → **`HOSTED_AGENT_LABEL_REGISTRY_JSON`**); it is **not** Kubernetes or Prometheus label metadata.
- **`slackTools.*`**: optional Secret ref + tunables for **in-process** Slack tools (`HOSTED_AGENT_SLACK_TOOLS_*` on the agent Deployment only; not used by scraper CronJobs).
- **`observability.*`**: cluster scrape hints—`prometheus.io/*` annotations, optional **`ServiceMonitor`**, **`structuredLogs.json`** or **`plugins.logShipping.enabled`** → `HOSTED_AGENT_LOG_FORMAT=json` (see **[DALC-REQ-PLUGIN-LOG-SHIPPING-001]** / `dalc-plugin-log-shipping`), Postgres pool caps for observability tables when configured, etc.
- **`observability.plugins.*`**: toggle tree for optional integrations (`prometheus`, `langfuse`, `wandb`, `grafana`, `logShipping`; defaults vary by key). See [Runtime architecture](#runtime-architecture-lifecycle-events-and-plugins-phase-1) and per-plugin sections below.

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

## Metrics (Prometheus)

When **`observability.plugins.prometheus.enabled`** is **true** (Helm) / **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED`** is truthy (env), the agent HTTP server exposes **`GET /metrics`** on the same port as the API (default **8088**), in Prometheus text format (`dalc_*` series).

### Environment

#### `HOSTED_AGENT_LOG_FORMAT`

Controls how the Python runtime prints **application** log lines (structlog) to **stdout**:

- `**console`** (default when unset): human-readable lines for local development.
- `**json`**: one **JSON object per line** (often called “JSON logging”). Each line includes at least `level`, `message`, `service`, and `request_id` when the HTTP middleware ran. That shape is easy for **Fluent Bit**, **Promtail**, **Vector**, or an OpenTelemetry collector to parse and ship to Loki or similar.

This is separate from Uvicorn’s own access logs; it applies to the structured events we emit (e.g. `http_request_start` / `http_request_end`).


| Variable                  | Values                      | Purpose    |
| ------------------------- | --------------------------- | ---------- |
| `HOSTED_AGENT_LOG_FORMAT` | `console` (default), `json` | See above. |

<!-- Traceability: [DALC-REQ-TOKEN-MET-005] -->

#### LLM token metrics and estimated cost (optional)

| Variable | Purpose |
| -------- | ------- |
| `HOSTED_AGENT_METRICS_TRIGGER_PAYLOAD_MAX_BYTES` | Upper bound (bytes) for histogram clamping of trigger request/response size observations; values above map to the `+Inf` bucket (default **262144**). |
| `HOSTED_AGENT_LLM_EST_COST_USD_PER_INPUT_TOKEN` | Non-negative float; when **both** this and `HOSTED_AGENT_LLM_EST_COST_USD_PER_OUTPUT_TOKEN` are set, `dalc_llm_estimated_cost_usd_total` increments by `input_tokens * in + output_tokens * out` (estimate only). |
| `HOSTED_AGENT_LLM_EST_COST_USD_PER_OUTPUT_TOKEN` | See above. |

Helm: add entries under `extraEnv` on the agent workload (see `helm/chart/values.yaml`) to set pricing inputs without committing secrets.

Helm: set `observability.structuredLogs.json: true` **or** `observability.plugins.logShipping.enabled: true` under the `agent` subchart (dependency alias) to inject `HOSTED_AGENT_LOG_FORMAT=json`. The **`logShipping`** toggle is for operators who model log export as a named plugin alongside other `observability.plugins.*` flags.

### Metric names (agent process)


| Metric                                        | Labels                       | Description                        |
| --------------------------------------------- | ---------------------------- | ---------------------------------- |
| `dalc_trigger_requests_total`   | `trigger`, `transport`, `result` | HTTP trigger rows use `trigger="http"` and `transport="http"`; Slack/Jira bridges use `trigger="slack"|"jira"` plus outcome in `result`. |
| `dalc_trigger_duration_seconds` | `trigger`, `transport`, `result` | Histogram of inbound trigger handling time |
| `dalc_trigger_request_bytes` | (none) | Histogram of `POST /api/v1/trigger` JSON body size (bytes; large values clamped). |
| `dalc_trigger_response_bytes` | (none) | Histogram of successful plain-text response body size (UTF-8 bytes). |
| `dalc_llm_input_tokens_total` | `agent_id`, `model_id`, `result` | Cumulative provider-reported input tokens (supervisor LLM path). |
| `dalc_llm_output_tokens_total` | `agent_id`, `model_id`, `result` | Cumulative provider-reported output tokens. |
| `dalc_llm_usage_missing_total` | `agent_id`, `model_id`, `result` | Completions with incomplete token usage metadata. |
| `dalc_llm_time_to_first_token_seconds` | `agent_id`, `model_id`, `result`, `streaming` | TTFT (streaming vs non-streaming). |
| `dalc_llm_estimated_cost_usd_total` | `agent_id`, `model_id`, `result` | Estimated USD (see env table; not billing). |
| `dalc_tool_calls_total`          | `tool`, `result`             | Cumulative tool invocations; **`tool`** is the registry id (`toolset.tool_name`). |
| `dalc_tool_calls_duration_seconds` | `tool`, `result`          | Tool call latency.                 |
| `dalc_subagent_invocations_total`    | `subagent`, `result`         | Subagent delegations               |
| `dalc_subagent_duration_seconds`     | `subagent`, `result`         | Subagent latency                   |
| `dalc_skill_loads_total`             | `skill`, `result`            | Skill load operations              |
| `dalc_skill_load_duration_seconds`   | `skill`, `result`            | Skill load latency                 |
`tool`, `subagent`, and `skill` label values come from **configuration** only (bounded), not user-supplied free text.

For **`agent_id`** and **`model_id`** on LLM metrics, the runtime uses `HOSTED_AGENT_ID` / `HOSTED_AGENT_AGENT_ID` and `HOSTED_AGENT_CHAT_MODEL` / `HOSTED_AGENT_MODEL_ID` when set; long values are shortened via stable hashes (see `agent.observability.plugins.prometheus.tagify_metric_label`).

### Kubernetes scrape discovery (Helm)

Under `agent.observability` (Kubernetes scrape and log format only; checkpoints, W&B, and Slack feedback use other top-level keys—see `helm/chart/values.yaml`):

- `**observability.plugins.prometheus.enabled**`: wires **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED`** so `/metrics` is served and **`dalc_*`** series are populated from the lifecycle bus.
- `**observability.prometheusAnnotations.enabled`**: adds `prometheus.io/scrape`, `prometheus.io/port`, `prometheus.io/path` to chart-managed workloads **when `observability.plugins.prometheus.enabled` is also true** (otherwise there is no `/metrics` surface to scrape).
- `**observability.serviceMonitor.enabled`**: renders a `**monitoring.coreos.com/v1` `ServiceMonitor`** selecting the agent `Service` on port `**http**`, path `**/metrics**`. Requires the **Prometheus Operator** CRDs in the cluster.

When the chart deploys the **managed RAG** workload (at least one enabled job under `**scrapers.jira**` or `**scrapers.slack**`; see [DALC-REQ-RAG-SCRAPERS-002](../openspec/specs/dalc-rag-from-scrapers/spec.md)):

- `**observability.prometheusAnnotations.enabled**`: the **same** annotation triad as the agent is applied to the **RAG** Pod and **RAG** Service (port from `**scrapers.ragService.service.port`**, default **8090**). There is no separate RAG-only scrape flag.
- `**observability.serviceMonitor.enabled`**: also renders a second `**ServiceMonitor`** (`metadata.name` suffix `**-rag**`) selecting the RAG Service, path `**/metrics**`, same interval / timeout / `**extraLabels**` as the agent monitor so Prometheus Operator selectors (e.g. `release: prometheus`) pick up **both** targets.

Worked example chart: `**examples/with-observability/`** (enables an enabled scraper job so **RAG** is present, **agent + RAG** annotations, and **two** `ServiceMonitor` resources when the Operator is present).

## Logs (Loki / ELK / etc.)

<!-- Traceability: [DALC-REQ-PLUGIN-LOG-SHIPPING-003] extends [DALC-REQ-O11Y-LOGS-004] -->

With `**HOSTED_AGENT_LOG_FORMAT=json`**, stdout lines are JSON objects suitable for **Fluent Bit**, **Promtail**, **Vector**, or the OpenTelemetry Collector (file/stdout receiver).

Recommended pipeline labels:

- `**service`** from the `service` field (constant `declarative-agent-library-chart`).
- `**level`** from the `level` field.
- `**request_id**` from the `request_id` field when present.

Clients may send `**X-Request-Id**`; the server echoes it on responses and includes it in structured logs for the request. Outbound HTTP from the agent to RAG (`**rag**` specialist tool execution inside `**POST /api/v1/trigger**` and `**POST /api/v1/rag/query**`) sends the same `**X-Request-Id**` on the upstream request.

### Example: Fluent Bit → Loki (Kubernetes container logs)

Kubernetes typically presents container stdout as files under `/var/log/containers/`. Parse each log line as JSON so `level`, `message`, `service`, and `request_id` become extracted fields before you attach Loki labels (keep cardinality bounded—prefer static metadata plus `service` / `level`):

```ini
[PARSER]
    Name        dalc_agent_json
    Format      json

[FILTER]
    Name                kubernetes
    Match               kube.*
    Merge_Log           On
    Keep_Log            Off
```

### Example: Promtail / Grafana Agent (`pipeline_stages`)

```yaml
pipeline_stages:
  - json:
      expressions:
        level: level
        service: service
        request_id: request_id
        message: message
  - labels:
      level:
      service:
```

Use **`labelallow`** / **`labeldrop`** so high-cardinality fields such as `request_id` remain LogQL filters unless your retention policy intentionally permits that cardinality as a label.

### Example: Vector (parse JSON line)

When the raw line is JSON text (for example from `file` or `kubernetes_logs` source):

```toml
[transforms.parse_dalc_json]
type = "remap"
inputs = ["raw_kube_logs"]
source = '''
  parsed, err = parse_json(.message)
  if err == null {
    .level = parsed.level
    .service = parsed.service
    .request_id = parsed.request_id
    .msg = parsed.message
  }
'''
```

## Dashboards

<!-- Traceability: [DALC-REQ-O11Y-LOGS-006] -->

Import `**grafana/dalc-overview.json**` (see `**grafana/README.md**`) for agent trigger rate / p95 latency and **RAG** embed + query rate panels (requires both scrape targets in Prometheus). For **LLM token throughput, TTFT, payload sizes, and estimated cost**, import `**grafana/cfha-token-metrics.json**` (same datasource uid convention as `dalc-overview.json`).

### Metric names (RAG workload)

The **RAG** HTTP server (separate Deployment when an enabled scraper job exists; port **8090** by default via `**scrapers.ragService.service.port`**) exposes `**GET /metrics`** (when the same **`observability.plugins.prometheus.enabled`** / env flag is on) with:


| Metric                                     | Labels               | Description              |
| ------------------------------------------ | -------------------- | ------------------------ |
| `dalc_rag_embed_requests_total`   | `result` = `success` | `client_error`           |
| `dalc_rag_embed_duration_seconds` | `result`             | Latency for those routes |
| `dalc_rag_query_requests_total`   | `result`             | `POST /v1/query`         |
| `dalc_rag_query_duration_seconds` | `result`             | Query latency            |


Helm: set `**observability.prometheusAnnotations.enabled: true**` under `agent` to add `prometheus.io/*` hints on **both** agent and RAG Service/Pod when RAG is deployed (RAG port from `**scrapers.ragService.service.port`**).

### Subagent roles (agent process)

Configured subagents are **tools** on the root agent ([LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)). They run when the supervisor invokes them during `**POST /api/v1/trigger`** (after a `**message`** turn), or when exercising them via unit tests with a scripted model.

- `**metrics**`: tool body returns the agent process **Prometheus snapshot** (same registry as `GET /metrics`). `**role: metrics`** is omitted from the default tool list unless `**exposeAsTool: true`** is set on that entry.
- `**rag**`: tool arguments carry `**query**` and optional RAG fields; execution proxies to managed RAG `**/v1/query**`. Requires `HOSTED_AGENT_RAG_BASE_URL` and a separate scrape target for `**dalc_rag_***` on the RAG pod.

`**dalc_subagent_***`, `**dalc_skill_***`, and `**dalc_tool_***` increment when those tools or the legacy direct `**tool**` / `**load_skill**` paths run through the trigger pipeline.

### Metric names (scraper CronJob pods)

Every enabled scraper container listens on **`SCRAPER_METRICS_ADDR`** (Helm sets **`0.0.0.0:9091`**) and exposes **`GET /metrics`** using a **scraper-only** Prometheus registry, so this endpoint does **not** include agent or RAG `dalc_*` series from other workloads. After the job’s main work finishes, the process waits **`SCRAPER_METRICS_GRACE_SECONDS`** (default **35** in the chart) so Prometheus can scrape the Job pod before exit.

- **Jira** job (`agent.scrapers.jira_job`): reads **`/config/job.json`**, posts issue payloads to RAG **`/v1/embed`**, increments **`dalc_scraper_rag_submissions_total`** per attempt.
- **Slack** job (`agent.scrapers.slack_job`): **`slack_search`** (Real-time Search + thread/history context) or **`slack_channel`** (`conversations.history`); same RAG + scraper metrics series as Jira.

| Metric | Labels | Description |
|--------|--------|-------------|
| `dalc_scraper_runs_total` | `integration`, `result` = `success` \| `error` | One completion per CronJob run |
| `dalc_scraper_run_duration_seconds` | `integration` | Wall time for the job |
| `dalc_scraper_rag_submissions_total` | `integration`, `result` = `success` \| `client_error` \| `server_error` | RAG **`/v1/embed`** attempts (reference job) |

**`SCRAPER_INTEGRATION`** sets the Prometheus label **`integration`**: it names the **integration type** for metrics (a bounded, operator-controlled value such as **`reference`**, **`slack`**, or **`jira`**), not an instance id. If unset, the **reference** job defaults to **`reference`**; the **stub** job defaults to **`SCRAPER_NAME`** (the job’s configured `name` in values) or **`stub`**. Use **`SCRAPER_INTEGRATION`** when the Helm job name should differ from the metric type (e.g. job `ingest-prod` but type **`slack`**).

**`SCRAPER_METRICS_ADDR`** accepts **`host:port`** or IPv6 **`[addr]:port`** (for example **`[::]:9091`**).

When **`observability.prometheusAnnotations.enabled`** is true, the chart adds **`prometheus.io/*`** annotations on **all** scraper Job pods (port **9091**, path **`/metrics`**).

### Durable scraper cursor store (Jira/Slack)

Scraper incremental state defaults to the existing file paths (`JIRA_WATERMARK_DIR`, `SLACK_STATE_DIR`). To use a durable backend, set `scrapers.cursorStore.backend: postgres`.

- Scraper pods get `SCRAPER_CURSOR_BACKEND=postgres` only when cursor backend is enabled.
- DSN precedence is scraper-specific Secret override first (`scrapers.cursorStore.postgresUrlSecretName`/`postgresUrlSecretKey`), then shared `checkpoints.postgresUrl` as `HOSTED_AGENT_POSTGRES_URL`.
- Secrets stay in pod env via Secret refs; DSNs are not embedded in scraper `job.json` ConfigMaps.
- Runtime uses lazy, idempotent DDL (`CREATE TABLE IF NOT EXISTS scraper_cursor_state`) at first use, then upsert writes keyed by `(integration, scope, key_hash)`. The agent image includes **`psycopg`** so Postgres cursor mode works without a custom image.
- If `backend: postgres` while at least one scraper job is configured, the chart **`helm template` / `helm upgrade` fails** unless you set `scrapers.cursorStore.postgresUrlSecretName` or `checkpoints.postgresUrl` (shared DSN).
- Recommended ops posture: keep `concurrencyPolicy: Forbid` (default), scope keys per environment, and ensure Postgres connection limits account for short-lived CronJobs.

Migration from file mode to Postgres can be a cold cutover (first run re-establishes cursor state) or one-time copy of existing file cursors into `scraper_cursor_state` before flipping `backend`.

## Integration test (kind + Prometheus)

End-to-end check that `**examples/with-observability`** deploys to **kind** (agent **+** RAG), **Prometheus** (community Helm chart) scrapes **both** Services, and PromQL sees:

- `**dalc_trigger_requests_total`** after several `POST /api/v1/trigger` calls, and  
- `**dalc_rag_embed_requests_total`** / `**dalc_rag_query_requests_total**` after `POST /v1/embed` and `POST /v1/query` on RAG.
- **Script:** `[helm/src/tests/scripts/integration_kind_o11y_prometheus.sh](../helm/src/tests/scripts/integration_kind_o11y_prometheus.sh)` — installs Prometheus with **two** static scrape jobs (`dalc-agent-metrics`, `dalc-rag-metrics`); disables **ServiceMonitor** on the release (`--set agent.observability.serviceMonitor.enabled=false`) so **Prometheus Operator CRDs** are not required.
- **Prometheus values template:** `[helm/src/tests/scripts/prometheus-kind-o11y-values.yaml](../helm/src/tests/scripts/prometheus-kind-o11y-values.yaml)` — placeholders `**@SCRAPE_TARGET_AGENT@`** (agent `Service` cluster DNS on port **8088**) and `**@SCRAPE_TARGET_RAG@`** (managed RAG `Service` on port **8090** by default).
- **Pytest wrapper (opt-in):** `RUN_KIND_O11Y_INTEGRATION=1 pytest tests/integration/test_kind_o11y_prometheus.py -v --no-cov` from `helm/src/` (avoids coverage floor when only this test runs).

**Prerequisites:** Docker, kind, kubectl, helm, curl, Python 3. Optional: `CLEANUP_KIND=1` to delete the cluster when the script exits; `SKIP_KIND_CREATE=1` to reuse an existing cluster name (`KIND_CLUSTER_NAME`, default `dalc-o11y-it`). Helm installs use `HELM_WAIT_TIMEOUT` (default **15m**) and `ROLLOUT_TIMEOUT` (default **600s**) because Prometheus images can be slow to pull on a fresh kind node.