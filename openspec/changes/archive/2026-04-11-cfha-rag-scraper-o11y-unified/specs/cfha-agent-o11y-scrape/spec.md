## MODIFIED Requirements

### Requirement: Helm values control scrape discovery

The Helm library chart SHALL expose **values** that allow operators to enable **Prometheus discovery metadata** on **each chart-managed workload that exposes a `/metrics` endpoint** (initially the **agent** and, when deployed, the **managed RAG HTTP service**), using a **single** operator-controlled switch under **`o11y.prometheusAnnotations`** (for example **`prometheus.io/scrape`**, **`prometheus.io/port`**, **`prometheus.io/path`**), without editing templates manually. The feature SHALL default to **disabled** so existing releases remain unchanged until opted in. The chart SHALL NOT define a separate per-workload values flag (such as `rag.prometheusAnnotations.enabled`) solely to enable annotations on RAG.

#### Scenario: Operator enables annotation-based scrape

- **WHEN** an operator sets **`o11y.prometheusAnnotations.enabled`** to enable Prometheus annotations
- **THEN** rendered manifests SHALL include the annotations on the **agent** Pod template and/or **agent** Service as documented, with **port** and **path** consistent with the agent **`/metrics`** endpoint

#### Scenario: RAG inherits the same annotation policy when deployed

- **WHEN** **`o11y.prometheusAnnotations.enabled`** is true and the chart deploys the managed RAG HTTP service
- **THEN** rendered manifests SHALL include the same class of Prometheus scrape annotations on the **RAG** Pod template and **RAG** Service with **port** and **path** consistent with the RAG **`/metrics`** endpoint on the documented RAG HTTP port

### Requirement: Optional ServiceMonitor for Prometheus Operator

When a documented values flag requests a **`ServiceMonitor`**, the chart SHALL render one or more **`monitoring.coreos.com/v1`** `ServiceMonitor` resources with **labels** and **namespace** selectors driven by values: **at minimum** a monitor for the **agent** `Service`, and **additionally** a monitor for the **RAG** `Service` **when** the RAG workload is deployed. The feature SHALL be **off by default**. Documentation SHALL state that enabling this requires the **Prometheus Operator CRDs** to be installed in the cluster.

#### Scenario: Operator enables ServiceMonitor

- **WHEN** an operator enables the ServiceMonitor values and installs into a cluster with the Prometheus Operator CRDs
- **THEN** `helm template` (or install) SHALL produce a valid `ServiceMonitor` that selects the agent `Service` Endpoints on the HTTP port and uses the `/metrics` path

#### Scenario: Operator enables ServiceMonitor with RAG deployed

- **WHEN** an operator enables the ServiceMonitor values and the chart deploys the managed RAG HTTP service (scraper gate satisfied)
- **THEN** `helm template` (or install) SHALL produce an additional valid `ServiceMonitor` that selects the RAG `Service` on the RAG HTTP port and uses the `/metrics` path
