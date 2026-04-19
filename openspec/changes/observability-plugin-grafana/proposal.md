# Proposal: observability-plugin-grafana

Package **DALC Grafana dashboard JSON** for operators and optionally render a **`ConfigMap`** when **`observability.plugins.grafana.enabled`** is true.

## Goals

- Regenerate **`grafana/dalc-overview.json`** and **`grafana/cfha-token-metrics.json`** to query **`dalc_*`** Prometheus names (aligned with runtime emission and **ADR 0011**).
- Document import paths, datasource uid conventions, scrape alignment, and the optional Helm ConfigMap in **`grafana/README.md`**.
- Capture normative deltas under this change (`specs/`) until archive promotion.

## Non-goals

- Automatic Grafana provisioning or sidecar wiring (clusters differ); ConfigMap carries raw JSON only.
