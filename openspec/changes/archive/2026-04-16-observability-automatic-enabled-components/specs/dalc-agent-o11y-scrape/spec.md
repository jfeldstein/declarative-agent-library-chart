## MODIFIED Requirements

### Requirement: [DALC-REQ-O11Y-SCRAPE-004] Helm values control scrape discovery

The Helm library chart SHALL expose **values** that allow operators to enable **Prometheus discovery metadata** on **each chart-managed workload that exposes a `/metrics` endpoint** via a **single** operator-controlled switch under **`o11y.prometheusAnnotations`** (for example **`prometheus.io/scrape`**, **`prometheus.io/port`**, **`prometheus.io/path`**), without editing templates manually. **Initially**, the chart documents at least the **agent** deployment and, **when deployed**, the **managed RAG HTTP service** and **scraper CronJob** pods as metrics endpoints; additional workloads SHALL follow the same pattern when added. The feature SHALL default to **disabled** so existing releases remain unchanged until opted in. The chart SHALL NOT define a separate per-workload values flag (such as `rag.prometheusAnnotations.enabled`) solely to enable annotations on one optional workload.

#### Scenario: Operator enables annotation-based scrape

- **WHEN** an operator sets **`o11y.prometheusAnnotations.enabled`** to enable Prometheus annotations
- **THEN** rendered manifests SHALL include the annotations on the **agent** Pod template and/or **agent** Service as documented, with **port** and **path** consistent with the agent **`/metrics`** endpoint

#### Scenario: Optional metrics services inherit the same annotation policy when deployed

- **WHEN** **`o11y.prometheusAnnotations.enabled`** is true and the chart deploys an optional metrics-exporting workload documented for scrape (for example the **managed RAG HTTP service** when the scraper gate is satisfied)
- **THEN** rendered manifests SHALL include the same class of Prometheus scrape annotations on that workload’s Pod template and/or **Service** with **port** and **path** consistent with its **`/metrics`** endpoint on the documented HTTP port

#### Scenario: Optional metrics workload not deployed

- **WHEN** **`o11y.prometheusAnnotations.enabled`** is true and a given optional metrics workload is **not** deployed (for example RAG not deployed because no scraper jobs enable it)
- **THEN** rendered manifests SHALL **not** include scrape annotations for that absent workload’s Services or Pods

### Requirement: [DALC-REQ-O11Y-SCRAPE-005] Optional ServiceMonitor for Prometheus Operator

When a documented values flag requests a **`ServiceMonitor`**, the chart SHALL render one or more **`monitoring.coreos.com/v1`** `ServiceMonitor` resources with **labels** and **namespace** selectors driven by values: **for each** chart-managed **`Service`** that fronts an **enabled** metrics workload in that release, **when** that workload is deployed. **At minimum**, the chart SHALL render a monitor for the **agent** `Service` when the agent is deployed. **Additionally**, for **each** optional metrics **`Service`** the chart deploys (for example the **managed RAG HTTP service** when the scraper gate is satisfied), the chart SHALL render a **`ServiceMonitor`** selecting that **`Service`**. The feature SHALL be **off by default**. Documentation SHALL state that enabling this requires the **Prometheus Operator CRDs** to be installed in the cluster.

#### Scenario: Operator enables ServiceMonitor

- **WHEN** an operator enables the ServiceMonitor values and installs into a cluster with the Prometheus Operator CRDs
- **THEN** `helm template` (or install) SHALL produce a valid `ServiceMonitor` that selects the agent `Service` Endpoints on the HTTP port and uses the `/metrics` path

#### Scenario: Operator enables ServiceMonitor with optional metrics service deployed

- **WHEN** an operator enables the ServiceMonitor values and the chart deploys an optional metrics HTTP **`Service`** (for example the managed RAG HTTP service when scraper jobs satisfy the deployment gate)
- **THEN** `helm template` (or install) SHALL produce an additional valid `ServiceMonitor` that selects that **`Service`** on its documented HTTP port and uses the `/metrics` path

#### Scenario: Operator enables ServiceMonitor but optional metrics service is not deployed

- **WHEN** an operator enables the ServiceMonitor values and a given optional metrics **`Service`** is **not** deployed (for example no scraper-gated RAG)
- **THEN** `helm template` (or install) SHALL **not** produce a `ServiceMonitor` for that absent workload
