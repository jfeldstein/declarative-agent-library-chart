# Declarative Agent Library Chart — Architecture

This document describes how **user application charts** (in other repositories or in `examples/*` in this repo) compose the **Declarative Agent Library** Helm chart and Python **runtime** (`helm/src/hosted_agents/`) into a deployable system. It aligns with the promoted OpenSpec capabilities under `openspec/specs/`.

## System context

```mermaid
flowchart TB
  subgraph user["User chart (application)"]
    UV[values.yaml]
    DEP[helm dependency: declarative-agent-library]
  end
  subgraph lib["Library chart (helm/chart)"]
    CM[ConfigMap: prompts + JSON catalogs]
    AG[Deployment: agent container]
    SVC[Service: agent HTTP]
    CJ[CronJobs: scrapers]
    RAG_DEP[RAG Deployment + Service]
    SM[Optional ServiceMonitors]
  end
  subgraph rt["Runtime image (same image for agent / RAG / scrapers)"]
    API[FastAPI: /api/v1/trigger, /metrics, ...]
    LG[LangGraph trigger pipeline]
    RAG_APP[RAG HTTP app: /v1/*, /metrics]
    SCR[scraper modules: jira_job | slack_job]
  end
  UV --> DEP
  DEP --> CM
  DEP --> AG
  DEP --> SVC
  DEP --> CJ
  DEP --> RAG_DEP
  DEP --> SM
  AG --> API
  AG --> LG
  RAG_DEP --> RAG_APP
  CJ --> SCR
  SCR -->|"POST embed / ingest"| RAG_APP
  API -->|"optional proxy"| RAG_APP
```

**Idea:** Operators declare agents, tools, scrapers, and observability in YAML. The chart renders Kubernetes resources and injects configuration into the runtime via environment variables and a ConfigMap. The **same container image** runs the agent HTTP server, the optional managed RAG service (different command/args), and scraper job pods (different `command`).

---

## User charts (other repos)

A **user chart** is a normal Helm **application** chart that lists `declarative-agent-library` as a **dependency** and passes nested values under the dependency name (for example `declarative-agent-library:` in `examples/hello-world/values.yaml`).

Responsibilities of the user chart:

- **Release identity:** `Release.Name`, namespace, and any org-specific labels or annotations not modeled in the library.
- **Image supply:** Point `image.repository` / `image.tag` at a built image that contains `hosted_agents` (built with [`helm/Dockerfile`](helm/Dockerfile) from the repository root; see README).
- **Policy:** NetworkPolicies, PodSecurity, external Secrets operators, ingress controllers, etc., if required beyond what the library renders.
- **Composition:** Enable scrapers, observability flags, and resource limits appropriate to the workload.

The library chart is published from `helm/chart` (`Chart.yaml` describes it as reusable templates for a YAML-configured hosted agent runtime). Example parent charts live under `examples/` and are the reference integration pattern.

---

## The library chart — what it defines

### Infra (Kubernetes resources)

| Area | Resources | Notes |
|------|-------------|--------|
| Agent workload | `Deployment`, `Service` | Agent listens on container port **8088**; Service port is configurable (`values.service.port`). |
| Configuration | `ConfigMap` | System prompt, `subagents.json`, `skills.json`, MCP allowlist JSON, observability JSON blobs (label registry, Slack emoji map, shadow tenant allowlist). |
| Scrapers | `CronJob` + `ConfigMap` (per enabled job) | Under `scrapers.jira` / `scrapers.slack`: one pair per job with `enabled: true` (see [DALC-REQ-RAG-SCRAPERS-002](openspec/specs/dalc-rag-from-scrapers/spec.md)). |
| Managed RAG | `Deployment`, `Service` | Rendered **if and only if** at least one scraper job is enabled ([DALC-REQ-RAG-SCRAPERS-002](openspec/specs/dalc-rag-from-scrapers/spec.md)). No top-level `rag` key; tuning lives under `scrapers.ragService` ([DALC-REQ-RAG-SCRAPERS-001](openspec/specs/dalc-rag-from-scrapers/spec.md)). |
| Naming | Helpers in `_helpers.tpl` | `fullname`, selector labels, `ragInternalBaseUrl` (cluster DNS URL to the RAG Service when deployed). |

Optional **NodePort** is supported via `service.type` and `service.nodePort`.

### Observability (O11y)

Promoted requirements: [dalc-agent-o11y-scrape](openspec/specs/dalc-agent-o11y-scrape/spec.md), [dalc-agent-o11y-logs-dashboards](openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md).

- **Metrics:** The runtime exposes **`GET /metrics`** (Prometheus text format) on the agent HTTP port. Histogram/counter names for `POST /api/v1/trigger` are specified in [DALC-REQ-O11Y-SCRAPE-002](openspec/specs/dalc-agent-o11y-scrape/spec.md). When RAG is deployed, the RAG process also exposes `/metrics` on the RAG HTTP port.
- **Scrape discovery:** `o11y.prometheusAnnotations.enabled` toggles `prometheus.io/scrape`, `port`, and `path` on **agent** and **RAG** (and scraper pods use a documented metrics side port). A single switch applies to all chart-managed scrape targets ([DALC-REQ-O11Y-SCRAPE-004](openspec/specs/dalc-agent-o11y-scrape/spec.md)).
- **Prometheus Operator:** `o11y.serviceMonitor.enabled` renders `ServiceMonitor` resources for the agent Service and, when RAG is deployed, the RAG Service ([DALC-REQ-O11Y-SCRAPE-005](openspec/specs/dalc-agent-o11y-scrape/spec.md)).
- **Structured logs:** `o11y.structuredLogs.json` sets `HOSTED_AGENT_LOG_FORMAT=json` so the agent emits JSON lines to stdout ([DALC-REQ-O11Y-LOGS-001](openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md)). Request handling ties into correlation IDs for triggers ([DALC-REQ-O11Y-LOGS-002](openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md)).
- **Dashboards:** The repo includes Grafana JSON (see spec [DALC-REQ-O11Y-LOGS-003](openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md)) under `grafana/` for operator import.

### W&B tracing and extended observability

Under `values.observability`, the chart wires optional runtime behavior (checkpointing, tracing, feedback, exports):

- **Postgres URL:** `observability.postgresUrl` → `HOSTED_AGENT_POSTGRES_URL` (shared DSN pattern for checkpointing and related features).
- **Checkpoints:** `observability.checkpoints` → `HOSTED_AGENT_CHECKPOINTS_ENABLED`, `HOSTED_AGENT_CHECKPOINT_BACKEND`.
- **Weights & Biases:** `observability.wandb` → `HOSTED_AGENT_WANDB_ENABLED`, `WANDB_PROJECT`, `WANDB_ENTITY` when enabled. The LangGraph trigger path integrates W&B session handling in code (`hosted_agents.observability.wandb_trace`, used from `trigger_graph.py`).
- **Slack feedback, ATIF export, shadow rollouts:** toggles and JSON maps from values → env / ConfigMap keys as rendered in `templates/deployment.yaml` and `templates/configmap.yaml`.

These are **runtime** concerns; the chart’s role is to pass consistent env and mounted JSON so the same image can be used across environments.

### Scrapers

- **Configuration:** `scrapers.jira` and `scrapers.slack` each expose `enabled`, shared auth/site settings, `defaults`, and a `jobs` list (`schedule`, `source`, and source-specific fields). Non-secret fields render into a per-job `ConfigMap` (`job.json`).
- **Dispatch:** `templates/scraper-cronjobs.yaml` runs `jira_job` or `slack_job` only; unknown `source` values fail at runtime (process exit non-zero).
- **Environment:** Each job receives `RAG_SERVICE_URL` (cluster-internal base URL to the managed RAG Service), `SCRAPER_NAME`, `SCRAPER_SCOPE`, and metrics bind settings (`SCRAPER_METRICS_ADDR`, grace period).
- **Metrics:** Scraper pods expose Prometheus metrics on port **9091** (separate from the agent’s `/metrics` on the main HTTP port), with optional scrape annotations when `o11y.prometheusAnnotations.enabled` is true.

Scrapers exist to **feed** the managed RAG service (embed/ingest); they are not the agent’s synchronous request path.

### RAG

- **Deployment rule:** RAG Deployment + Service appear only when the scraper gate is satisfied ([DALC-REQ-RAG-SCRAPERS-002](openspec/specs/dalc-rag-from-scrapers/spec.md)).
- **Tuning:** `scrapers.ragService` controls replicas, Service type/port, and resources ([DALC-REQ-RAG-SCRAPERS-003](openspec/specs/dalc-rag-from-scrapers/spec.md)).
- **Agent integration:** When RAG is deployed, the chart sets `HOSTED_AGENT_RAG_BASE_URL` to the internal `http://<release>-rag:<port>` URL ([DALC-REQ-RAG-SCRAPERS-004](openspec/specs/dalc-rag-from-scrapers/spec.md)). The agent runtime exposes `POST /api/v1/rag/query`, which proxies to the RAG service’s HTTP API (e.g. `/v1/query`).

The RAG container runs **uvicorn** with factory `hosted_agents.rag.app:create_app` on the configured port; health checks hit `/health`.

### Triggers

- **Single external launch path:** `POST /api/v1/trigger` ([DALC-REQ-O11Y-SCRAPE-002](openspec/specs/dalc-agent-o11y-scrape/spec.md) and runtime `app.py`).
- **Orchestration:** The handler builds a `TriggerContext` and calls `run_trigger_graph` — a **LangGraph**-based pipeline in `trigger_graph.py` (see `GET /api/v1/runtime/summary` field `orchestration: langgraph`).
- **Payload:** JSON body is validated into `TriggerBody` (`agent_models`); legacy `subagent` field is rejected in favor of the supervisor + tools pattern.
- **Threading / checkpoints:** Additional GET routes under `/api/v1/runtime/...` and `/api/v1/trigger/...` expose thread state and checkpoint history when the checkpoint store is enabled.

### Agents

- **Supervisor system prompt:** `values.systemPrompt` → ConfigMap `system-prompt` → `HOSTED_AGENT_SYSTEM_PROMPT`.
- **Chat model:** Optional `chatModel` → `HOSTED_AGENT_CHAT_MODEL` when non-empty (LangChain model id style).
- **Subagents (declarative):** `values.subagents` → JSON in ConfigMap → `HOSTED_AGENT_SUBAGENTS_JSON`. When this list is non-empty, the trigger path runs `run_supervisor_agent` (LangChain “subagents as tools” pattern) instead of a single static reply.
- **Replicas / resources:** Standard `replicaCount`, `resources`, and `extraEnv` on the agent Deployment.

### Tools

Two complementary mechanisms are modeled in values and env:

1. **MCP-style tool allowlist:** `mcp.enabledTools` → `HOSTED_AGENT_ENABLED_MCP_TOOLS_JSON` (array of tool id strings). The runtime uses this for configured, in-process tool execution and metrics (see cross-reference in [DALC-REQ-O11Y-SCRAPE-003](openspec/specs/dalc-agent-o11y-scrape/spec.md) to `runtime-tools-mcp` in OpenSpec changes).
2. **Skills catalog:** `skills` → `HOSTED_AGENT_SKILLS_JSON`. Skills can gate or load tool JSON via the trigger graph (`load_skill`, `run_skill_load_json`, etc.).

Tool invocation paths also include direct **`tool`** / **`tool_arguments`** on the trigger body for JSON tool runs (`run_tool_json`).

---

## Helm ↔ runtime contract (summary)

| Helm values / source | Runtime env / behavior |
|----------------------|-------------------------|
| `systemPrompt` | `HOSTED_AGENT_SYSTEM_PROMPT` |
| `chatModel` | `HOSTED_AGENT_CHAT_MODEL` |
| `subagents`, `skills`, `mcp.enabledTools` | `HOSTED_AGENT_*_JSON` |
| RAG deployed (helper) | `HOSTED_AGENT_RAG_BASE_URL` |
| `o11y.structuredLogs.json` | `HOSTED_AGENT_LOG_FORMAT=json` |
| `observability.*` | W&B, checkpoints, Slack, ATIF, shadow, label registry env + ConfigMap |
| `extraEnv` | Additional passthrough env on agent container |

Scraper jobs use `RAG_SERVICE_URL` (same internal base URL pattern as the chart helper) rather than the agent’s `HOSTED_AGENT_RAG_BASE_URL`.

---

## Testing and chart quality (CI orientation)

Promoted specs describe how this repo validates charts:

- **Helm unittest:** [dalc-helm-unittest](openspec/specs/dalc-helm-unittest/spec.md) — example charts under `examples/` assert CronJob/RAG/ServiceMonitor behavior.
- **Chart-testing (`ct`):** [dalc-chart-testing-ct](openspec/specs/dalc-chart-testing-ct/spec.md) — lint and discovery for all charts.

---

## Spec index (promoted)

| Capability | Path |
|------------|------|
| Requirement verification / IDs | `openspec/specs/dalc-requirement-verification/spec.md` |
| Prometheus scrape + metrics contract | `openspec/specs/dalc-agent-o11y-scrape/spec.md` |
| Logs + Grafana dashboard expectations | `openspec/specs/dalc-agent-o11y-logs-dashboards/spec.md` |
| RAG from scrapers (no top-level `rag`, scraper gate) | `openspec/specs/dalc-rag-from-scrapers/spec.md` |
| Helm unittest | `openspec/specs/dalc-helm-unittest/spec.md` |
| Chart-testing (`ct`) | `openspec/specs/dalc-chart-testing-ct/spec.md` |

For in-flight designs, see `openspec/changes/*`; **promoted** normative text lives under `openspec/specs/*/spec.md`.
