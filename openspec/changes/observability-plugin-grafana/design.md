## Design

### Prometheus → dashboard alignment

Runtime metrics use prefix **`dalc_`** (`helm/src/agent/metrics.py`, `rag/metrics.py`, `scrapers/metrics.py`). Dashboard PromQL substitutes `agent_runtime_*` → **`dalc_*`** one-for-one on metric family names.

Authoritative metric tables remain in **`docs/observability.md`**; **ADR 0011** defines prefix rules (`dalc_*`, `dalc_rag_*`, `dalc_scraper_*`).

### Helm packaging

When **`agent.observability.plugins.grafana.enabled`** is **true**, the library chart renders **`ConfigMap`** `{fullname}-grafana-dashboards` with keys:

- **`dalc-overview.json`**
- **`cfha-token-metrics.json`** (historical filename; queries use **`dalc_*`**)

Bundled bytes are copied from repo **`grafana/`** into **`helm/chart/files/grafana/`** so `helm package` embeds dashboards without escaping the chart directory.

### OpenSpec

Promoted **`dalc-agent-o11y-logs-dashboards`** requirement **[DALC-REQ-O11Y-LOGS-006]** references **`dalc-runtime-token-metrics`** (replacing stale **`cfha-runtime-token-metrics`** wording).
