# declarative-agent-library-chart

Standalone repository for **YAML-configured** hosted agents: a **Helm library chart** (`helm/chart/`) consumed by application charts, a **hello-world** example (`examples/hello-world/`), and a **Python** runtime (`hosted_agents`) that exposes **`POST /api/v1/trigger`** as the **only HTTP entry for launching agent work** (LangGraph-orchestrated). The root agent reads **`HOSTED_AGENT_SYSTEM_PROMPT`** from the environment (ConfigMap in-cluster) as **supervisor** instructions when **`subagents`** is configured; optional JSON can carry **`message`** (user input), **`load_skill`**, or a direct **`tool`** step (see below). This matches the LangChain **subagents** pattern ([docs](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)): specialists are **tools** on that root agent, not an HTTP-selected subagent.

## Layout

| Path | Purpose |
|------|---------|
| `runtime/src/hosted_agents/` | Python application (FastAPI, LangGraph trigger pipeline, RAG service module, scrapers, tools) |
| `docs/rag-http-api.md` | RAG HTTP contract (`/v1/embed`, `/v1/query`, `/v1/relate`) |
| `runtime/tests/` | Pytest suite (85%+ coverage enforced in CI) |
| `runtime/pyproject.toml` | `uv` project + Hatch packaging + pytest/coverage config |
| `helm/chart/` | **Declarative Agent Library Chart** (`declarative-agent-library`; Helm subchart / optional direct install) |
| `helm/src/` | Pointer to runtime source (implementation lives in `runtime/src/hosted_agents/`) |
| `helm/tests/chart/` | Notes for Helm `helm test` hooks |
| `examples/hello-world/` | Minimal application chart depending on `file://../../helm/chart` |
| `examples/with-observability/` | Example chart with `o11y` (Prometheus annotations, ServiceMonitor, JSON logs) |
| `examples/with-scrapers/` | Example chart with RAG + reference scraper `CronJob` (asserted in `./ci.sh`) |
| `Dockerfile` | Production-style image for the Python runtime |
| `skaffold.yaml` / `devspace.yaml` | Local deploy + **port-forward `localhost:8088` → service :8088** |
| `docs/observability.md` | Metrics (`/metrics`), structured logs, Helm scrape hints, Grafana import |
| `docs/development-log.md` | Notable chart/runtime changes (breaking API, env, values); ADRs live under `docs/adrs/` |
| `grafana/` | Starter Grafana dashboard JSON + import notes |

## Decisions

Locked design choices: [docs/adrs/](docs/adrs/README.md) (`NNNN-short-title.md`; boilerplate: [0000-topic.md](docs/adrs/0000-topic.md)).

## Requirements

- Python 3.11+ (see `.python-version`), [uv](https://docs.astral.sh/uv/)
- For cluster paths: **kind** (or compatible Kubernetes), **Helm 3**, **kubectl**
- Optional: [Skaffold](https://skaffold.dev/), [DevSpace](https://www.devspace.sh/)

## Local CI (Python + chart render)

Traceability: [CFHA-REQ-HELM-UNITTEST-003] [CFHA-REQ-CHART-CT-002] [CFHA-REQ-O11Y-LOGS-004] — see [docs/spec-test-traceability.md](docs/spec-test-traceability.md) for the full matrix and CI tiers.

From a clone of [github.com/jfeldstein/declarative-agent-library-chart](https://github.com/jfeldstein/declarative-agent-library-chart):

```bash
cd declarative-agent-library-chart
./ci.sh
```

GitHub Actions runs the same checks (Python: `ruff`, `pytest` with **85%+ coverage**, RAG smoke; Helm: `helm unittest` on examples + `ct lint`). See [`.github/workflows/ci.yml`](.github/workflows/ci.yml).

## Observability

- **Metrics**: `GET /metrics` (Prometheus text) on the agent port; metric names and labels are documented in [docs/observability.md](docs/observability.md).
- **Logs**: optional JSON to stdout via `HOSTED_AGENT_LOG_FORMAT=json` or Helm `o11y.structuredLogs.json`.
- **Kubernetes**: opt-in `prometheus.io/*` annotations and optional **ServiceMonitor** under `declarative-agent-library.o11y` (see **`examples/with-observability/`**).
- **Dashboards**: import [grafana/cfha-agent-overview.json](grafana/cfha-agent-overview.json) per [grafana/README.md](grafana/README.md).

## Run API without Kubernetes

```bash
uv sync --all-groups --project runtime
export HOSTED_AGENT_SYSTEM_PROMPT='Respond, "Hello :wave:"'
uv run --project runtime uvicorn hosted_agents.app:create_app --factory --host 0.0.0.0 --port 8088
curl -s -X POST http://127.0.0.1:8088/api/v1/trigger
```

## Hello-world on kind (Helm)

1. Create or select a cluster, e.g. `kind create cluster --name cfha`.
2. Build and load the image (chart defaults: `config-first-hosted-agents:local`, `pullPolicy: Never`):

   ```bash
   cd declarative-agent-library-chart
   docker build -t config-first-hosted-agents:local .
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
| `scrapers.jobs` | **CronJobs** that push normalized content (and graph edges when known) into RAG; built-in **`reference`** job posts a fixture document + `contained_in` edge. If **at least one** job has **`enabled: true`**, the chart also deploys the **managed RAG HTTP** Deployment + Service (`/v1/embed`, `/v1/query`, `/v1/relate`) — see [docs/rag-http-api.md](docs/rag-http-api.md). Tune RAG replicas/port/resources under **`scrapers.ragService`**. |
| `mcp.enabledTools` | Allowlisted **in-process tools** merged into the **supervisor** tool list (and still invokable directly via **`POST /api/v1/trigger`** with `{"tool":"…","tool_arguments":{…}}`). Layout: [runtime/src/hosted_agents/tools_impl/README.md](runtime/src/hosted_agents/tools_impl/README.md). **Merge order:** subagent tools (config order) then MCP tools (sorted by id). |
| `subagents` | JSON list of specialists compiled into **LangGraph subgraphs** and registered as **LangChain tools** on the root agent ([LangChain subagents](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents)). **Recommended:** **`description`** for each entry (tool schema text). **`exposeAsTool`**: omit or **`true`** to register the tool; **`role: metrics`** defaults to **`exposeAsTool: false`** so Prometheus snapshots stay off the default tool list unless you opt in. Optional **`role`**: **`default`** (uses `systemPrompt` + optional task text from the tool call); **`metrics`** (returns agent Prometheus text inside the tool); **`rag`** (tool arguments carry `query` / RAG fields; proxies to RAG `/v1/query` with **`X-Request-Id`**). |
| `skills` | JSON catalog `{ "name", "prompt", "extraTools"? }` — load with **`POST /api/v1/trigger`** and `{"load_skill":"<name>"}` (progressive disclosure; aligns with [LangChain Skills](https://docs.langchain.com/oss/python/langchain/multi-agent/skills)). |
| `chatModel` | Optional Helm value → **`HOSTED_AGENT_CHAT_MODEL`** when **`subagents`** is non-empty (e.g. `openai:gpt-4o-mini`). Requires the matching LangChain provider package and credentials in your image. **Hello-world** keeps **`subagents: []`** so the trigger stays deterministic without a remote LLM. |

The agent Pod receives `HOSTED_AGENT_RAG_BASE_URL` pointing at the in-cluster RAG Service when **any scraper job is enabled** (empty otherwise). ConfigMap keys `subagents.json`, `skills.json`, and `enabled-mcp-tools.json` mirror the arrays above.

**Breaking (HTTP):** JSON field **`subagent`** on **`POST /api/v1/trigger`** is **rejected with 400**. Send **`message`** to the supervisor instead; RAG parameters move to the **`rag`** specialist’s tool arguments when the model invokes that tool.

**Environment (supervisor):** `HOSTED_AGENT_CHAT_MODEL` selects the chat model when `HOSTED_AGENT_SUBAGENTS_JSON` is non-empty. `HOSTED_AGENT_FAKE_CHAT_SEQUENCE` is reserved for tests (JSON array of scripted assistant turns).

### RAG + agent locally

```bash
cd runtime
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

In-process smoke (no servers): from `runtime`, run `uv run python scripts/smoke_rag.py`.

### Example: metrics subagent + RAG subagent (values)

Under the subchart key `declarative-agent-library`, set JSON-compatible YAML (stored in ConfigMap as `subagents.json`). Use **`role: metrics`** for a subagent that returns the **agent** Prometheus snapshot (same as `GET /metrics`), and **`role: rag`** for a subagent that forwards **`query`** to the **RAG** service (`agent_runtime_rag_*` metrics live on the RAG pod’s `/metrics`).

```yaml
declarative-agent-library:
  scrapers:
    jobs:
      - name: reference
        enabled: true
        schedule: "0 * * * *"
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

1. **Scraper → RAG:** CronJob `reference` calls `python -m hosted_agents.scrapers.reference_job` with `RAG_SERVICE_URL` set to the RAG Service (`http://<release>-rag:8090` when an enabled scraper job has deployed RAG).
2. **Agent → RAG (utility HTTP):** `POST /api/v1/rag/query` proxies to RAG `/v1/query` (not the agent *launch* path; use **trigger** for orchestrated runs).
3. **Tool:** With `mcp.enabledTools` including `sample.echo`, either ask the supervisor in natural language or call `POST /api/v1/trigger` with `{"tool":"sample.echo","tool_arguments":{"message":"hi"}}` (direct path bypasses the LLM).

### Scrapers: verifying CronJobs

- **Disabled by default:** `helm template` on `examples/hello-world` yields **no** `CronJob` when `scrapers.jobs` is empty.
- **Enabled example:** `examples/with-scrapers/` enables the `reference` scraper (which deploys RAG); `./ci.sh` templates that chart and expects at least one `CronJob`.

## Extension points

- A future **Slack webhook listener** can expose e.g. `POST /webhooks/slack` and **forward** into **`POST /api/v1/trigger`** (preserving **`X-Request-Id`** when calling the agent). No Slack App or public URL is required for hello-world.
- Draft integration shape (`tools.slack`, `tools.jira`, `tools.drive`) remains in `helm/chart/values.schema.json` for roadmap positioning; it is separate from **`mcp.enabledTools`** (in-process tool allowlist).
