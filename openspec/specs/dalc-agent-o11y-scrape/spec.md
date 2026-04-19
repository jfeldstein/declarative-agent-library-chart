## ADDED Requirements

### Requirement: [DALC-REQ-O11Y-SCRAPE-001] Prometheus metrics exposition endpoint

The agent HTTP server SHALL expose a **Prometheus text exposition** endpoint at the HTTP path **`/metrics`** on the same port used for the public API (default **8088**), returning **`Content-Type: text/plain; version=0.0.4`** (or a documented compatible variant) and a **200** response when the process is healthy enough to serve metrics, **only when** the **Prometheus observability plugin** is enabled (for example **`observability.plugins.prometheus.enabled: true`** in Helm, which sets **`HOSTED_AGENT_OBSERVABILITY_PLUGINS_PROMETHEUS_ENABLED`**).

#### Scenario: Scraper retrieves metrics

- **WHEN** a client sends `GET /metrics` to the agent listen address
- **THEN** the response SHALL be valid Prometheus text exposition parseable by Prometheus 2.x or compatible scrapers

### Requirement: [DALC-REQ-O11Y-SCRAPE-002] Application metrics for HTTP trigger

The runtime SHALL register Prometheus metrics for **`POST /api/v1/trigger`** using these **exact metric base names** (suffixes and label names follow Prometheus client conventions such as `_total`, `_bucket`, `_count`, `_sum` for histograms):

- Counter **`dalc_trigger_requests_total`** labeled **`trigger`**, **`transport`**, and **`result`** where the HTTP synchronous trigger path uses **`trigger="http"`** and **`transport="http"`**, and **`result`** is drawn from the fixed set **`success`**, **`client_error`**, **`server_error`** (mapping **2xx** → `success`, **4xx** → `client_error`, **5xx** and unhandled exceptions → `server_error`).
- Histogram **`dalc_trigger_duration_seconds`** with the same **`trigger`**, **`transport`**, and **`result`** labels on observation (or equivalent labeling that preserves the same cardinality rules).

Implementations SHALL NOT attach labels derived from prompt text, user ids, or other unbounded domains.

#### Scenario: Successful trigger increments success path

- **WHEN** a client successfully completes `POST /api/v1/trigger` with a **2xx** response
- **THEN** the exposed `/metrics` payload SHALL include an increased **`dalc_trigger_requests_total`** series for the HTTP trigger label set with **`result="success"`** and SHALL record latency on **`dalc_trigger_duration_seconds`**

#### Scenario: Client error on trigger

- **WHEN** a client receives a **4xx** response from `POST /api/v1/trigger`
- **THEN** the exposed `/metrics` payload SHALL include an increased **`dalc_trigger_requests_total`** series for the HTTP trigger label set with **`result="client_error"`**

#### Scenario: Server error on trigger

- **WHEN** a client receives a **5xx** response or the handler fails with an unhandled error
- **THEN** the exposed `/metrics` payload SHALL include an increased **`dalc_trigger_requests_total`** series for the HTTP trigger label set with **`result="server_error"`**

### Requirement: [DALC-REQ-O11Y-SCRAPE-003] In-process runtime components reuse platform metric names

When this deployment integrates **tools**, **subagents**, and/or **skills** as specified in **`runtime-tools-mcp`** (reference contract for tool discovery, invocation, and metrics), **`runtime-subagents`**, and **`runtime-skills`** (see change **`agent-runtime-components`**), the agent process SHALL expose the **corresponding `dalc_*` metrics** (`dalc_tool_*`, `dalc_subagent_*`, `dalc_skill_*`) defined in those capability specs on the **same `/metrics` endpoint** using a **shared registry**, so centralized scrapers collect one target per agent pod for HTTP trigger and in-process components. Conforming tool exposure **MAY** use **LangGraph-native or in-process** bindings without a standalone MCP server process, as described in **`runtime-tools-mcp`**.

#### Scenario: Tool-enabled deployment exports tool metrics

- **WHEN** values enable at least one configured tool and the agent invokes that tool during operation
- **THEN** `/metrics` SHALL include the **`dalc_tool_*`** series prescribed in **`runtime-tools-mcp`** with **`tool`** labels restricted to **configured** tool identifiers for that deployment

### Requirement: [DALC-REQ-O11Y-SCRAPE-004] Helm values control scrape discovery

The Helm library chart SHALL expose **values** that allow operators to enable **Prometheus discovery metadata** on **each chart-managed workload that exposes a `/metrics` endpoint** via **`observability.prometheusAnnotations`** (for example **`prometheus.io/scrape`**, **`prometheus.io/port`**, **`prometheus.io/path`**), **only when** **`observability.plugins.prometheus.enabled`** is also **true** (there is no `/metrics` scrape surface otherwise). **Initially**, the chart documents at least the **agent** deployment and, **when deployed**, the **managed RAG HTTP service** and **scraper CronJob** pods as metrics endpoints; additional workloads SHALL follow the same pattern when added. The annotation feature SHALL default to **disabled** so existing releases remain unchanged until opted in. The chart SHALL NOT define a separate per-workload values flag (such as `rag.prometheusAnnotations.enabled`) solely to enable annotations on one optional workload.

#### Scenario: Operator enables annotation-based scrape

- **WHEN** an operator sets **`observability.prometheusAnnotations.enabled`** and **`observability.plugins.prometheus.enabled`** to enable Prometheus annotations for chart-managed metrics endpoints
- **THEN** rendered manifests SHALL include the annotations on the **agent** Pod template and/or **agent** Service as documented, with **port** and **path** consistent with the agent **`/metrics`** endpoint

#### Scenario: Optional metrics services inherit the same annotation policy when deployed

- **WHEN** **`observability.prometheusAnnotations.enabled`** is true, **`observability.plugins.prometheus.enabled`** is true, and the chart deploys an optional metrics-exporting workload documented for scrape (for example the **managed RAG HTTP service** when the scraper gate is satisfied)
- **THEN** rendered manifests SHALL include the same class of Prometheus scrape annotations on that workload’s Pod template and/or **Service** with **port** and **path** consistent with its **`/metrics`** endpoint on the documented HTTP port

#### Scenario: Optional metrics workload not deployed

- **WHEN** **`observability.prometheusAnnotations.enabled`** is true, **`observability.plugins.prometheus.enabled`** is true, and a given optional metrics workload is **not** deployed (for example RAG not deployed because no scraper jobs enable it)
- **THEN** rendered manifests SHALL **not** include scrape annotations for that absent workload’s Services or Pods

### Requirement: [DALC-REQ-O11Y-SCRAPE-005] Optional ServiceMonitor for Prometheus Operator

When a documented values flag requests a **`ServiceMonitor`**, the chart SHALL render one or more **`monitoring.coreos.com/v1`** `ServiceMonitor` resources with **labels** and **namespace** selectors driven by values: **for each** chart-managed **`Service`** that fronts an **enabled** metrics workload in that release, **when** that workload is deployed **and** **`observability.plugins.prometheus.enabled`** is **true**. **At minimum**, the chart SHALL render a monitor for the **agent** `Service` when the agent is deployed. **Additionally**, for **each** optional metrics **`Service`** the chart deploys (for example the **managed RAG HTTP service** when the scraper gate is satisfied), the chart SHALL render a **`ServiceMonitor`** selecting that **`Service`**. The feature SHALL be **off by default**. Documentation SHALL state that enabling this requires the **Prometheus Operator CRDs** to be installed in the cluster.

#### Scenario: Operator enables ServiceMonitor

- **WHEN** an operator enables the ServiceMonitor values and installs into a cluster with the Prometheus Operator CRDs
- **THEN** `helm template` (or install) SHALL produce a valid `ServiceMonitor` that selects the agent `Service` Endpoints on the HTTP port and uses the `/metrics` path

#### Scenario: Operator enables ServiceMonitor with optional metrics service deployed

- **WHEN** an operator enables the ServiceMonitor values and the chart deploys an optional metrics HTTP **`Service`** (for example the managed RAG HTTP service when scraper jobs satisfy the deployment gate)
- **THEN** `helm template` (or install) SHALL produce an additional valid `ServiceMonitor` that selects that **`Service`** on its documented HTTP port and uses the `/metrics` path

#### Scenario: Operator enables ServiceMonitor but optional metrics service is not deployed

- **WHEN** an operator enables the ServiceMonitor values and a given optional metrics **`Service`** is **not** deployed (for example no scraper-gated RAG)
- **THEN** `helm template` (or install) SHALL **not** produce a `ServiceMonitor` for that absent workload

### Requirement: [DALC-REQ-O11Y-SCRAPE-006] Helm values for structured JSON logs

The Helm library chart SHALL expose a boolean **`observability.structuredLogs.json`** that, when **true**, configures the agent container so structured **JSON** logs are emitted per **`dalc-agent-o11y-logs-dashboards`**. When **false** or unset, the chart SHALL NOT force JSON log format via that values key.

#### Scenario: Operator enables JSON logs via values

- **WHEN** an operator sets **`observability.structuredLogs.json`** to **true**
- **THEN** rendered manifests SHALL set **`HOSTED_AGENT_LOG_FORMAT`** to **`json`** on the agent container (or an equivalent documented mechanism achieving the same effect)
