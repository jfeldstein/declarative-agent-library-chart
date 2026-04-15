# declarative-agent-library-chart

<!-- Traceability: [DALC-REQ-HELM-UNITTEST-003] [DALC-REQ-CHART-CT-002] [DALC-REQ-O11Y-LOGS-004] -->

# Declarative Agent Library Chart

This repo is a **Helm library chart** (`helm/chart/`). Add it as a dependency in `Chart.yaml`, and add your config in `values.yaml`.

## Examples

### hello-world

To make an agentic Slack bot, you need:

1. Chart.yaml:

    ```yaml
    dependencies:
      - name: declarative-agent-library
        version: 0.1.0
        repository: https://github.com/jfeldstein/declarative-agent-library-chart
    ```

2. and a values.yaml:

    ```yaml
    declarative-agent-library:
      systemPrompt: |
        Respond, "Hello :wave:"
      presence:
        slackBotId:
          secretName: slack-bot-token
          secretKey: token
    ```

3. Register your bot on Slack

You can now deploy the chart, and @-tag your bot on slack. That's it!

(See [hello-world example](examples/hello-world) for more details.)

## Architecture

```
+-----------------------------------------------------------------------------+
|                                        |                                    |
|      NON-AGENTIC SCAFFOLDING           |              THE AGENT             |
|   (HTTP triggers, sources of context)  |  (harness, tools, RLHF / feedback) |
|                                        |                                    |
+-----------------------------------------------------------------------------+
|                                                                             |
|                                       IaC                                   |
|                                                                             |
+-----------------------------------------------------------------------------+
```

### Subcomponents

```
+-------------------------------------------------------------------+
| NON-AGENTIC SCAFFOLDING         | AGENTIC                         |
|  + Sources of context           |  + Agent (system prompt,        |
|    (scrapers / ETL -> RAG,      |    config, subagents, skills,   |
|    entities/relationships)      |    chat model, checkpoints,     |
|                                 |    W&B, etc.)                   |
|  + Workflow triggers (webhooks, |  + Tools:                       |
|    bridges, cron->HTTP) ->      |    | RAG (zero-config)          |
|    everything routes to         |    | Built-in (Jira, Slack, …)  |
|    POST /trigger endpoint       |    | Extendable (in your chart) |
|                                 |  + RLHF / feedback (persistence |
|                                 |    & telemetry, experience lib) |
+----------------------------------+--------------------------------+
| IaC                                                               |
| + K8s Resources                                                   |
| + Observability (everything exports metrics, dashboards OOTB)     |
+-------------------------------------------------------------------+
```

### Layout

| Path                        | Purpose                                                      |
|-----------------------------|--------------------------------------------------------------|
| `helm/chart/`               | Declarative Agent Library Helm chart                         |
| `helm/src/hosted_agents/`   | Python app: FastAPI entry, trigger logic, RAG, scrapers      |
| `examples/hello-world/`     | Minimal example chart, uses the agent subchart               |


## Observability

You get **baseline observability without writing instrumentation**: the FastAPI runtime already exposes Prometheus metrics, structured logging hooks, and request correlation. 

You decides **what scrapes and ships** that data (annotations, Operator `ServiceMonitor`, JSON vs console logs). Deeper reference (RAG and scraper metrics, label rules, kind + Prometheus recipe) lives in [docs/observability.md](docs/observability.md).

- **Metrics (always on the agent)**: `GET /metrics` on the same port as the HTTP API (default **8088**), Prometheus text format. Counters and histograms cover triggers, MCP tools, subagents, and skill loads; label values are **config-bounded** (not free-form user text), which keeps cardinality safe. When the chart deploys **managed RAG** (enabled scraper jobs), the RAG pod exposes its own `/metrics` (`agent_runtime_rag_*`). Scraper `CronJob` pods expose a separate **`/metrics`** on **9091** with scraper-only series (`agent_runtime_scraper_*`).
- **Logs**: default **console** lines for local dev; set **`HOSTED_AGENT_LOG_FORMAT=json`** or Helm **`declarative-agent-library.observability.structuredLogs.json`** for one JSON object per line on stdout (Loki / ELK / Vector friendly). **`X-Request-Id`** is echoed on responses and included in structured logs; the agent forwards it to RAG on proxy calls.
- **Kubernetes scrape hints (opt-in)**: under **`declarative-agent-library.observability`**, turn on **`prometheusAnnotations`** for `prometheus.io/scrape|port|path` on agent (and RAG and scraper pods when those workloads exist), and/or **`serviceMonitor`** for Prometheus Operator. Example wiring: **`examples/with-observability/`**.
- **Dashboards**: starter panels for agent triggers and RAG traffic in [grafana/dalc-agent-overview.json](grafana/dalc-agent-overview.json) — import steps in [grafana/README.md](grafana/README.md).

## Run API without Kubernetes

```bash
uv sync --all-groups --project helm/src
export HOSTED_AGENT_SYSTEM_PROMPT='Respond, "Hello :wave:"'
uv run --project helm/src uvicorn hosted_agents.app:create_app --factory --host 0.0.0.0 --port 8088
curl -s -X POST http://127.0.0.1:8088/api/v1/trigger
```

## Hello-world on kind (Helm)

1. Create or select a cluster, e.g. `kind create cluster --name cfha`.
2. Build and load the image (chart defaults: `config-first-hosted-agents:local`, `pullPolicy: Never`):

   ```bash
   cd declarative-agent-library-chart
   docker build -f helm/Dockerfile -t config-first-hosted-agents:local .
   kind load docker-image config-first-hosted-agents:local --name cfha
   ```

3. Vendor the subchart (use `helm dependency update` when `Chart.lock` changes; otherwise `helm dependency build --skip-refresh`):

   ```bash
   (cd examples/hello-world && helm dependency build --skip-refresh)
   helm upgrade --install hello-world examples/hello-world -n default --wait
   ```

4. Reach the service on **127.0.0.1:8088** (Service is `ClusterIP`):

   ```bash
   kubectl port-forward svc/hello-world-declarative-agent-library 8088:8088 -n default
   ```

   In another terminal:

   ```bash
   curl -s -X POST http://127.0.0.1:8088/api/v1/trigger
   ```

   Expected body includes `Hello` and `:wave:` (plain text).

5. Optional: `helm test hello-world -n default` runs the chart test Job that POSTs the trigger and checks for `Hello`.

## Skaffold

From the repository root (after `helm dependency build` in `examples/hello-world`):

```bash
skaffold dev
```

Skaffold sets subchart image repo/tag from the built artifact and port-forwards **local 8088** to the `hello-world-declarative-agent-library` service.

## DevSpace

```bash
devspace dev
```

Uses `examples/hello-world` and port **8088:8088** to the workload selected by `app.kubernetes.io/name=declarative-agent-library`.

## Runtime components (OpenSpec: `agent-runtime-components`)

Values keys under the **`declarative-agent-library`** subchart configure these runtime surfaces:

| Values key | Role |
|------------|------|
| `scrapers.jira` / `scrapers.slack` | **CronJobs** (one per enabled job) push normalized content into RAG; each job mounts a **ConfigMap** (`job.json`) and receives tokens via **Secret** `valueFrom` env vars. If **at least one** job is enabled (parent `enabled: true` and job `enabled` not `false`), the chart deploys the **managed RAG HTTP** Deployment + Service — see [docs/rag-http-api.md](docs/rag-http-api.md). Tune RAG under **`scrapers.ragService`**. |
| `mcp.enabledTools` | Allowlisted **in-process tools** merged into the **supervisor** tool list (and still invokable directly via **`POST /api/v1/trigger`** with `{"tool":"…","tool_arguments":{…}}`). Layout: [helm/src/hosted_agents/tools_impl/README.md](helm/src/hosted_agents/tools_impl/README.md). **Merge order:** subagent tools (config order) then MCP tools (sorted by id). |
| `subagents` | JSON list of specialists compiled into **LangGraph subgraphs** and registered as **LangChain tools** on the root agent ([LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)). **Recommended:** **`description`** for each entry (tool schema text). **`exposeAsTool`**: omit or **`true`** to register the tool; **`role: metrics`** defaults to **`exposeAsTool: false`** so Prometheus snapshots stay off the default tool list unless you opt in. Optional **`role`**: **`default`** (uses `systemPrompt` + optional task text from the tool call); **`metrics`** (returns agent Prometheus text inside the tool); **`rag`** (tool arguments carry `query` / RAG fields; proxies to RAG `/v1/query` with **`X-Request-Id`**). |
| `skills` | JSON catalog `{ "name", "prompt", "extraTools"? }` — load with **`POST /api/v1/trigger`** and `{"load_skill":"<name>"}` (progressive disclosure; aligns with [LangChain Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)). |
| `chatModel` | Optional Helm value → **`HOSTED_AGENT_CHAT_MODEL`** when **`subagents`** is non-empty (e.g. `openai:gpt-4o-mini`). Requires the matching LangChain provider package and credentials in your image. **Hello-world** keeps **`subagents: []`** so the trigger stays deterministic without a remote LLM. |

The agent Pod receives `HOSTED_AGENT_RAG_BASE_URL` pointing at the in-cluster RAG Service when **any scraper job is enabled** (empty otherwise). ConfigMap keys `subagents.json`, `skills.json`, and `enabled-mcp-tools.json` mirror the arrays above.

**Breaking (HTTP):** JSON field **`subagent`** on **`POST /api/v1/trigger`** is **rejected with 400**. Send **`message`** to the supervisor instead; RAG parameters move to the **`rag`** specialist’s tool arguments when the model invokes that tool.

**Environment (supervisor):** `HOSTED_AGENT_CHAT_MODEL` selects the chat model when `HOSTED_AGENT_SUBAGENTS_JSON` is non-empty. `HOSTED_AGENT_FAKE_CHAT_SEQUENCE` is reserved for tests (JSON array of scripted assistant turns).

### RAG + agent locally

```bash
cd helm/src
uv sync
# Terminal A — RAG on 8090
uv run uvicorn hosted_agents.rag.app:create_app --factory --host 127.0.0.1 --port 8090
# Terminal B — agent on 8088
export HOSTED_AGENT_RAG_BASE_URL=http://127.0.0.1:8090
export HOSTED_AGENT_SYSTEM_PROMPT='Respond, "Hello :wave:"'
uv run uvicorn hosted_agents.app:create_app --factory --host 127.0.0.1 --port 8088
# Query RAG through the agent proxy
curl -s -X POST http://127.0.0.1:8088/api/v1/rag/query -H 'content-type: application/json' \
  -d '{"query":"banana","scope":"default","expand_relationships":true}'
```

In-process smoke (no servers): from `helm/src`, run `uv run python tests/integration/smoke_rag.py`.

### Example: metrics subagent + RAG subagent (values)

Under the subchart key `declarative-agent-library`, set JSON-compatible YAML (stored in ConfigMap as `subagents.json`). Use **`role: metrics`** for a subagent that returns the **agent** Prometheus snapshot (same as `GET /metrics`), and **`role: rag`** for a subagent that forwards **`query`** to the **RAG** service (`agent_runtime_rag_*` metrics live on the RAG pod’s `/metrics`).

```yaml
declarative-agent-library:
  scrapers:
    jira:
      enabled: true
      siteUrl: https://example.atlassian.net
      auth:
        emailSecretName: jira-credentials
        emailSecretKey: email
        tokenSecretName: jira-credentials
        tokenSecretKey: token
      jobs:
        - schedule: "0 * * * *"
          source: jira
          query: 'project = DEMO ORDER BY updated ASC'
  subagents:
    - name: metrics
      role: metrics
      exposeAsTool: true
      description: Return the agent process Prometheus snapshot
    - name: rag
      role: rag
      systemPrompt: ""
      description: Query the managed RAG HTTP API
```

With a configured chat model, the supervisor chooses tools; **`message`** is the user turn. For **`metrics`**, set **`exposeAsTool: true`** (hidden by default for `role: metrics`). For **`rag`**, the model passes **`query`** / scope fields as tool arguments. **`POST /api/v1/rag/query`** remains a non-launch utility that proxies to RAG with **`X-Request-Id`**.

### Example: two classic prompt-only subagents

```yaml
declarative-agent-library:
  subagents:
    - name: research
      description: Research specialist
      systemPrompt: |
        Respond, "Research subagent"
    - name: jira
      description: Jira specialist
      systemPrompt: |
        Respond, "Jira subagent"
```

### End-to-end trace (POC)

1. **Scraper → RAG:** Each enabled job under `scrapers.jira` / `scrapers.slack` runs `python -m hosted_agents.scrapers.jira_job` or `slack_job` with `RAG_SERVICE_URL` set to the RAG Service (`http://<release>-rag:8090` when the RAG gate per [DALC-REQ-RAG-SCRAPERS-002](openspec/specs/dalc-rag-from-scrapers/spec.md) is satisfied).
2. **Agent → RAG (utility HTTP):** `POST /api/v1/rag/query` proxies to RAG `/v1/query` (not the agent *launch* path; use **trigger** for orchestrated runs).
3. **Tool:** With `mcp.enabledTools` including `sample.echo`, either ask the supervisor in natural language or call `POST /api/v1/trigger` with `{"tool":"sample.echo","tool_arguments":{"message":"hi"}}` (direct path bypasses the LLM).

### Scrapers: verifying CronJobs

- **Disabled by default:** `helm template` on `examples/hello-world` yields **no** scraper `CronJob` when `scrapers.jira.enabled` and `scrapers.slack.enabled` are false (or have no enabled jobs).
- **Enabled example:** `examples/with-scrapers/` enables Jira and Slack scraper jobs (which deploy RAG); CI (`helm unittest` on that chart) asserts scraper + RAG manifest rendering, including at least one `CronJob`.

## Extension points

- A future **Slack webhook listener** can expose e.g. `POST /webhooks/slack` and **forward** into **`POST /api/v1/trigger`** (preserving **`X-Request-Id`** when calling the agent). No Slack App or public URL is required for hello-world.
- Draft integration shape (`tools.slack`, `tools.jira`, `tools.drive`) remains in `helm/chart/values.schema.json` for roadmap positioning; it is separate from **`mcp.enabledTools`** (in-process tool allowlist).
