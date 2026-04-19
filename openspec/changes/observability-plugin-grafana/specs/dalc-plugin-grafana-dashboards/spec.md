## ADDED Requirements

### Requirement: [DALC-REQ-GRAFANA-DASH-001] Optional Helm ConfigMap packages dashboard JSON

The Helm library chart SHALL expose **`observability.plugins.grafana.enabled`** (boolean, default **false**). When **true**, `helm template` SHALL render a **`ConfigMap`** containing **`dalc-overview.json`** and **`cfha-token-metrics.json`** dashboard bodies suitable for Grafana import or operator-side provisioning.

#### Scenario: Disabled by default

- **WHEN** **`observability.plugins.grafana.enabled`** is unset or **false**
- **THEN** the chart SHALL NOT emit the Grafana dashboards **`ConfigMap`**

#### Scenario: Enabled renders dashboards

- **WHEN** **`observability.plugins.grafana.enabled`** is **true**
- **THEN** rendered manifests SHALL include a **`ConfigMap`** whose **`data`** keys include **`dalc-overview.json`** and **`cfha-token-metrics.json`** whose PromQL references **`dalc_*`** metric families documented in **`docs/observability.md`**
